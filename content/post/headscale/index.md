---
title: "🚀 Self-Hosting Tailscale with Headscale & Headplane via NPM"
subtitle: "Setting up a secure Tailscale control plane using Docker, Nginx Proxy Manager, and local DNS overrides for seamless access"
summary: "A practical guide to deploying the open-source Tailscale control server Headscale and its web UI Headplane using Docker, exposing them securely via Nginx Proxy Manager with path-based routing and IP restrictions, and solving local access issues with Technitium DNS."
date: 2025-04-27
draft: false
featured: false
authors:
  - Bas Nijholt
tags:
  - Headscale
  - Tailscale
  - Headplane
  - Self-Hosting
  - Docker
  - Nginx Proxy Manager
  - Networking
  - DNS
  - Technitium
  - WireGuard
categories:
  - Networking
  - Self-Hosting
  - Tutorial
---

{{< toc >}}

## 1. Introduction: Taking Control of My Mesh Network

Like many self-hosters, I've become a big fan of [Tailscale](https://tailscale.com/) for creating secure, zero-config overlay networks.
It makes connecting my various devices – servers in my homelab, laptops, phone – incredibly simple, no matter where they are.
However, while Tailscale's hosted control plane is convenient, the idea of having complete ownership and control over this critical piece of my infrastructure is appealing, especially from a privacy and customization perspective.

Enter [**Headscale**](https://github.com/juanfont/headscale), an open-source, self-hosted implementation of the Tailscale control server.
It lets you run your own Tailscale network without relying on the official Tailscale SaaS.
To make managing it easier, there's also [**Headplane**](https://github.com/tale/headplane), a sleek web UI.

Setting them up in Docker is straightforward, but integrating them smoothly into my existing homelab setup – specifically behind [**Nginx Proxy Manager (NPM)**](https://nginxproxymanager.com/) and dealing with local network access restrictions – took many hours of fiddling.
After getting it working nicely, I figured I'd share my setup, particularly the NPM configuration and the crucial local DNS trick needed to make IP whitelisting effective.
This post details _my specific setup_; it mostly serves as a guide for myself so I remember what I did, but hopefully, it can help others facing similar challenges.
Your own mileage may vary depending on your specific environment and tools.

{{% callout note %}}
**TL;DR:** This post details how I configured **Headscale** and **Headplane** (both in Docker) behind **Nginx Proxy Manager** using a single domain (`headscale.nijho.lt`), routing `/admin` to Headplane and `/` to Headscale.
It covers the necessary Nginx configuration, including **CORS headers** and **IP restrictions**, and crucially, how to use **local DNS overrides** (with Technitium DNS) to make those IP restrictions work correctly from within the local network.
{{% /callout %}}

## 2. Why Self-Host with Headscale?

While Tailscale's service is excellent, self-hosting with Headscale offers a few advantages that appealed to me:

- **Complete Control & Privacy:** No reliance on a third-party service for node registration and key exchange.
  All coordination happens on your own server.
- **No Node Limits (Potentially):** While Tailscale has generous free tier limits, self-hosting removes any vendor-imposed restrictions (though your server resources become the limit).
- **Learning & Customization:** It's a great way to understand the underlying coordination mechanisms better.

Of course, it comes with the responsibility of maintaining, updating, and securing the Headscale server yourself.

## 3. The Components

Here's a quick rundown of the tools involved in my setup:

- [**Headscale**](https://github.com/juanfont/headscale): The open-source Tailscale control server. Runs in Docker.
- [**Headplane**](https://github.com/tale/headplane): The web UI for managing Headscale. Runs in Docker.
- [**Docker**](https://www.docker.com/): Containerization platform for running Headscale and Headplane.
- [**Nginx Proxy Manager (NPM)**](https://nginxproxymanager.com/): My go-to reverse proxy for managing SSL and routing traffic to backend services. Runs on a separate machine (`192.168.1.4` in my case).
- [**Technitium DNS Server**](https://technitium.com/dns/): My local DNS server, used for the critical DNS override step. (You could also use Pi-hole, AdGuard Home, or similar).
- **Headscale/Headplane Docker Host:** The machine running the Docker containers (`192.168.1.66` in my case).

## 4. Docker and Service Configuration

I use `docker-compose` to manage the Headscale and Headplane containers.
The official docs cover the basics well, but here are the crucial parts of my setup on host `192.168.1.66`:

- **Volumes:** Persistent volumes are essential for configuration and state.
  For Headscale: `/mnt/data/headscale/config:/etc/headscale` and `/mnt/data/headscale/data:/var/lib/headscale`.
  For Headplane: `/mnt/data/headplane/config:/etc/headplane`, `/mnt/data/headplane/data:/var/lib/headplane`, plus access to Headscale's config (`/mnt/data/headscale/config/config.yaml:/etc/headscale/config.yaml`).
- **Ports:** Headscale runs on port `8080` internally (API/main) and `9090` (metrics).
  Headplane runs on port `3000` internally (UI).
  I map these to different host ports so NPM (running on `.4`) can reach them via the Docker host's IP (`.66`):
  ```yaml
  # Relevant docker-compose sections:
  services:
    headscale:
      # ... image, container_name, networks, volumes, env ...
      ports:
        - '8086:8080' # API mapped to host 8086
        - '9092:9090' # Metrics mapped to host 9092
      # ... command ...

    headplane:
      # ... image, container_name, networks, volumes, env ...
      ports:
        - '3002:3000' # UI mapped to host 3002
      # ...
  ```
- **Networking:** Both containers share a Docker network (`mynetwork`) allowing direct communication using service names (e.g., `http://headscale:8080`).

- **Headscale Configuration (`/mnt/data/headscale/config/config.yaml`):**
  Key settings include:
  `server_url: https://headscale.nijho.lt:443` - This is the public URL clients use to reach Headscale (via NPM).
  `listen_addr: 0.0.0.0:8080` - Headscale listens on port `8080` inside the container.
  `dns.base_domain: headscale.nijho.lt` - Sets the base domain for MagicDNS.
  Database is configured for SQLite at `/var/lib/headscale/db.sqlite`.

- **Headplane Configuration (`/mnt/data/headplane/config/config.yaml`):**
  Headplane needs to know how to talk to Headscale *internally* and what the *public* URL is:
  `headscale.url: http://headscale:8080` - Headplane backend uses the Docker service name and internal port.
  `headscale.public_url: https://headscale.nijho.lt` - Headplane frontend uses this (via NPM) for certain operations.
  It also needs access to Headscale's config path (`headscale.config_path: /etc/headscale/config.yaml`).

## 5. Nginx Proxy Manager Configuration (The Core)

This is where the magic happens for exposing Headscale and Headplane securely under the single domain, `headscale.nijho.lt`.
I use the "Advanced" configuration section in NPM for the proxy host running on `192.168.1.4`.

Here's the configuration that works for me:

```nginx
# NPM Advanced configuration for headscale.nijho.lt

# === Headscale API ===
location / {
    # CORS Headers - Allow requests from the UI served under this same domain
    # Needed because the browser JS loaded from /admin/ makes API calls to /
    add_header 'Access-Control-Allow-Origin' 'https://headscale.nijho.lt' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' '*' always; # Be more specific if needed
    add_header 'Access-Control-Allow-Credentials' 'true' always;
    add_header 'Access-Control-Max-Age' '1728000'; # Cache preflight for 20 days

    # Handle CORS preflight requests for the API endpoint
    if ($request_method = 'OPTIONS') {
        # Respond successfully to OPTIONS requests
        add_header 'Access-Control-Allow-Origin' 'https://headscale.nijho.lt' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' '*' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Max-Age' '1728000';
        add_header 'Content-Length' 0;
        add_header 'Content-Type' 'text/plain charset=UTF-8';
        return 204; # Return '204 No Content' which is standard for preflight
    }

    # Proxy settings for Headscale API
    proxy_pass http://192.168.1.66:8086; # Point to Headscale Docker host mapped port
    proxy_redirect http:// https://;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade; # Essential for WebSocket connections used by clients
    proxy_set_header Connection "Upgrade"; # Essential for WebSocket connections used by clients
    proxy_read_timeout 3600; # Reduced timeout (1 hour)
    proxy_send_timeout 3600; # Reduced timeout (1 hour)
    proxy_buffering off; # Good for Headscale's potentially long-lived connections
}

# === Headscale Metrics ===
location ^~ /metrics/ {
    # Proxy to Headscale metrics port
    proxy_pass http://192.168.1.66:9092/metrics; # Point to Headscale Docker host mapped port
    proxy_redirect http:// https://;

    # --- IMPORTANT: IP Restriction ---
    allow 192.168.1.0/24;   # Allow local LAN
    allow 100.64.0.0/24;    # Allow typical Headscale/Tailscale CGNAT range
    allow 10.8.0.0/24;      # Allow my WireGuard VPN clients (Adjust to your VPN subnet)
    deny all;               # Deny all other IPs
    # --- ------------------------ ---
}

# === Headplane Admin UI ===
location ^~ /admin/ {
    # Proxy to Headplane host port
    proxy_pass http://192.168.1.66:3002/admin/; # Note the trailing slash here!
    proxy_redirect http:// https://;

    # Proxy headers (optional but good practice)
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # --- IMPORTANT: IP Restriction ---
    allow 192.168.1.0/24;   # Allow local LAN
    allow 100.64.0.0/24;    # Allow typical Headscale/Tailscale CGNAT range
    allow 10.8.0.0/24;      # Allow my WireGuard VPN clients (Adjust to your VPN subnet)
    deny all;               # Deny all other IPs
    # --- ------------------------ ---
}

# === Block Bots ===
location = /robots.txt {
    add_header Content-Type text/plain;
    return 200 "User-agent: *\nDisallow: /\nUser-agent: GPTBot\nDisallow: /\nUser-agent: nibbler\nDisallow: /\n";
}
```

**Key takeaways from this Nginx configuration:**

- **Single Domain Routing:** Everything lives under `headscale.nijho.lt`.
  NPM directs traffic based on the path (`/`, `/metrics/`, `/admin/`).
- **Headscale API (`/`):** This is publicly accessible (security relies on Headscale's authentication).
  It includes **WebSocket headers** (`Upgrade`, `Connection`) crucial for Tailscale clients and **CORS headers**.
  Even though the UI is served from the same domain, explicitly adding CORS headers is good practice and ensures things work smoothly.
- **Headplane UI (`/admin/`) & Metrics (`/metrics/`):** These are **IP restricted**.
  Only devices connecting from the specified `allow` ranges (local LAN, Headscale internal IPs, my specific WireGuard VPN subnet) can access these endpoints.
  This significantly enhances security.
- **`^~` Modifier:** Used for `/metrics/` and `/admin/` for performance.
  It tells Nginx that if this prefix matches, don't bother checking other regular expression `location` blocks.

## 6. The Local Access Problem (NAT Loopback & IP Whitelisting)

Now, here's a common "gotcha".
You set up the IP restrictions (`allow 192.168.1.0/24; deny all;`) in NPM, but when you try accessing `https://headscale.nijho.lt/admin/` from a device _inside_ your `192.168.1.x` network, you might get blocked with a `403 Forbidden` error!

Why?
**NAT Loopback (or Hairpinning)**.

1.  Your local device asks public DNS for `headscale.nijho.lt`.
2.  Public DNS gives back your _public_ home IP address.
3.  Your device sends the request to your router's public IP.
4.  Your router forwards the request _back inside_ to NPM (`192.168.1.4`).
5.  NPM sees the request coming from your _router's public IP_, not your device's local `192.168.1.x` IP.
6.  The public IP doesn't match `192.168.1.0/24`, so `deny all` kicks in.

## 7. The Solution: Local DNS Override (Split DNS)

As explained in the blog post where I initially found parts of this setup, the solution is to use a **local DNS server** to override the public DNS record for devices inside your network.
This is often called "Split DNS" or "Split-Horizon DNS".

I use [**Technitium DNS Server**](https://technitium.com/dns/), but Pi-hole, AdGuard Home, or even some routers can do this.

**Steps in Technitium DNS:**

1.  **Go to DNS Zones.**
2.  Click **+ Add Zone**.
3.  **Zone Domain Name:** `headscale.nijho.lt` (the exact domain handled by NPM).
4.  **Zone Type:** `Primary`. Click **Add**.
5.  Click on the newly created `headscale.nijho.lt` zone to manage it.
6.  Click **+ Add Record**.
7.  **Name:** Leave **blank** (represents the zone domain itself).
8.  **Type:** `A`.
9.  **TTL:** `3600` (or similar).
10. **IP Address:** Enter the **local IP address of your Nginx Proxy Manager server** (in my case, `192.168.1.4`).
11. Click **Add**.

{{% callout warning %}}
**Crucial Point:** The `A` record must point to the IP address of the **reverse proxy (NPM)**, _not_ the backend Headscale/Headplane server.
The client needs to talk to NPM first.
{{% /callout %}}

Finally, ensure your local network clients (via DHCP settings on your router) use your Technitium DNS server for lookups.

Now, when a local device asks for `headscale.nijho.lt`, Technitium provides `192.168.1.4`.
The device connects directly to NPM, NPM sees the device's _local_ IP, and the `allow 192.168.1.0/24` rule works as expected!

## 8. Conclusion

Setting up a self-hosted Tailscale control plane with Headscale and Headplane is a rewarding way to gain full control over your mesh network.
While the basic Docker deployment is simple, integrating it securely behind a reverse proxy like Nginx Proxy Manager requires careful configuration, especially when using path-based routing and IP restrictions.
This post documented my specific setup, largely as a personal reminder, but the principles might help others navigating similar networking puzzles.

The key elements are:

- Correctly proxying requests based on the path (`/`, `/admin/`, `/metrics/`) to the right backend ports.
- Ensuring the Headscale API endpoint (`/`) has WebSocket support enabled and appropriate CORS headers (even if serving from the same domain).
- Implementing IP restrictions on sensitive endpoints like the admin UI and metrics.
- Using local DNS overrides to ensure those IP restrictions function correctly for clients inside your own network.

With this setup, I have a robust, secure, and self-managed Tailscale network, accessible seamlessly both internally and externally, with the added management convenience of the Headplane UI safely tucked behind IP whitelisting.
It fits my preference for self-hosting and fine-grained control over my infrastructure!

---

**Further Reading & Links:**

- [Headscale GitHub Repository](https://github.com/juanfont/headscale)
- [Headplane GitHub Repository](https://github.com/tale/headplane)
- [Nginx Proxy Manager](https://nginxproxymanager.com/)
- [Technitium DNS Server](https://technitium.com/dns/)
- [Tailscale Website](https://tailscale.com/)
