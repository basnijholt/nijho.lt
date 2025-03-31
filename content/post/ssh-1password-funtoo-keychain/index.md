---
title: Combining Keychain and 1Password CLI for SSH Agent Management
subtitle: A method to use 1Password CLI for secure SSH key passphrase storage while leveraging Keychain for persistent agent access and minimal prompts.
summary: Using 1Password CLI with Keychain for secure, persistent SSH agent access with fewer password prompts after initial setup.
projects: []
date: "2025-03-31T00:00:00Z"
draft: false
featured: false

image:
  caption: "Integrating Keychain and the 1Password CLI"
  focal_point: ""
  placement: 2
  preview_only: false

authors:
  - admin

tags:
  # Core concepts
  - ssh
  - ssh-agent
  - keychain
  - 1password
  - 1password-cli
  # Broader context
  - terminal
  - productivity
  - security
  - automation
  - zsh
  - dotfiles

categories:
  - terminal
  - security
  - level:intermediate
---

## Combining Keychain and 1Password CLI for SSH Agent Management

For about a decade, I've relied on two key tools in my development workflow: [Funtoo Keychain](https://www.funtoo.org/Funtoo:Keychain) for managing my `ssh-agent` and 1Password for securely storing secrets.
While I used them extensively, I never actually integrated them directly for SSH key passphrase handling.

Recently, with the advent of [1Password's built-in SSH agent](https://developer.1password.com/docs/ssh/get-started/), I gave it a try, attracted by the promise of managing keys directly within my vault.
However, I quickly found myself frequently prompted for my master password or biometrics, which interrupted my flow more often than I preferred compared to Keychain's persistence.

This led me back to the reliable "unlock once per session" behavior of Keychain.
But the experience using the 1Password Command-Line Interface (`op`) during that time sparked an idea: could I combine the persistence of Keychain with the secure passphrase retrieval of the `op` CLI?
The answer is yes, and this post outlines the setup that achieves that balance.

**The Goal:** Use 1Password as the secure vault for the SSH key passphrase but rely on `keychain` to manage the `ssh-agent` process and ensure the key, once unlocked, remains available for the entire login session without further prompts from 1Password.

**Why This Approach?**

This setup directly addresses the trade-off I encountered.
Funtoo `keychain` excels at starting `ssh-agent` reliably on login and keeping keys available throughout a session with just one initial unlock.
While the native 1Password agent is convenient for vault integration, its session management, in my experience, led to more frequent authentication prompts than desired for long-running sessions.

By using `keychain` for agent management and calling the `op` CLI via the standard `SSH_ASKPASS` mechanism _only_ for the initial key load, we get the best of both worlds: 1Password's secure storage for the passphrase and Keychain's persistent agent access with minimal prompting after the first unlock.

**The Components:**

1.  **Funtoo `keychain`:** Manages `ssh-agent` lifecycle and loads specified keys.
2.  **1Password CLI (`op`):** Securely retrieves secrets (the passphrase) from your 1Password vault. Requires `op` to be installed and logged in.
3.  **`askpass-1password.sh`:** A small helper script that `ssh-add` (via `keychain`) calls to get the passphrase. This script invokes `op`.
4.  **`setup_ssh_agent.sh`:** A script sourced by your shell startup file (`.zshrc`, `.bashrc`, etc.) to orchestrate the setup.

**Implementation:**

**Step 1: Create the `askpass` Helper Script**

This script simply calls `op read` to fetch the passphrase using its [Secret Reference URI](https://developer.1password.com/docs/cli/secret-reference-syntax/).

- Find your SSH key item in 1Password.
- Locate the passphrase field, click the options/arrow, and copy the "Copy Secret Reference".
- Create the script at `~/.ssh/askpass-1password.sh`:

![Copy Secret Reference screenshot](https://developer.1password.com/img/cli/copy-secret-reference-dark.png)

```sh
#!/bin/sh
# ~/.ssh/askpass-1password.sh
# Provides the SSH key passphrase from 1Password CLI via SSH_ASKPASS

# Paste your Secret Reference URI here
OP_SECRET_REFERENCE="op://YourVault/YourSSHKeyItem/password"

# Use 'op read' to retrieve and print the passphrase to stdout
# Requires 1Password CLI ('op') to be installed and authenticated.
op read "$OP_SECRET_REFERENCE"
```

- Make it executable: `chmod u+x ~/.ssh/askpass-1password.sh`

**Step 2: Create the Setup Orchestration Script**

This script checks if `op` is available and conditionally configures `keychain` to use the helper script.

_(Adjust path `~/dotfiles/scripts/setup_ssh_agent.sh` as needed)_

```bash
#!/bin/zsh
# ~/dotfiles/scripts/setup_ssh_agent.sh - Sets up ssh-agent via keychain.
# If 'op' CLI and the askpass helper script are available, uses 1Password for passphrase.
# Intended to be sourced by .zshrc or similar.

_askpass_helper="$HOME/.ssh/askpass-1password.sh"
_askpass_vars_set=false

# Check if 'op' CLI is installed and the helper script is usable
if command -v op >/dev/null 2>&1 && [[ -f "$_askpass_helper" ]] && [[ -x "$_askpass_helper" ]]; then
  # Configure environment for 1Password helper script
  export SSH_ASKPASS="$_askpass_helper"
  export SSH_ASKPASS_REQUIRE="prefer" # Use ASKPASS even in terminals
  _askpass_vars_set=true
fi

# Execute keychain to start/find agent, load key, and set env vars
# (Adjust key name 'id_ed25519' as needed)
eval $(keychain --eval --quiet --agents ssh --inherit any-once id_ed25519)

# Clean up ASKPASS variables if they were set
if $_askpass_vars_set; then
  unset SSH_ASKPASS
  unset SSH_ASKPASS_REQUIRE
fi
```

**Step 3: Source the Setup Script in `.zshrc`**

Add this to your `~/.zshrc` (or equivalent):

```zsh
# --- SSH Agent Configuration (via keychain & 1Password) ---
# Source the dedicated setup script if it exists.
_ssh_setup_script="${HOME}/dotfiles/scripts/setup_ssh_agent.sh"
if [[ -f "$_ssh_setup_script" ]]; then
  source "$_ssh_setup_script"
fi
# --- End SSH Agent Configuration ---
```

**How It Works:**

1.  When you start a new shell session, `.zshrc` sources `setup_ssh_agent.sh`.
2.  The script checks if `op` is installed and the `askpass-1password.sh` helper is ready.
3.  If yes, it sets the `SSH_ASKPASS` and `SSH_ASKPASS_REQUIRE` environment variables.
4.  It runs `keychain --eval id_ed25519`.
5.  `keychain` starts or connects to `ssh-agent` and uses `ssh-add` to load `id_ed25519`.
6.  `ssh-add` sees `SSH_ASKPASS` is set and executes `askpass-1password.sh`.
7.  The helper script runs `op read ...`.
8.  The 1Password CLI handles authentication (prompting for your master password or using biometrics/system auth _if necessary_ based on its current session state – typically only if the `op` session has expired).
9.  `op read` outputs the passphrase.
10. `ssh-add` receives the passphrase and unlocks the key, adding it to the agent.
11. `keychain --eval` outputs the necessary `export SSH_AUTH_SOCK=...` commands.
12. `eval` executes these commands, configuring your current shell to use the agent.
13. The `ASKPASS` variables are unset.

**Conclusion:**

After years of using Funtoo Keychain and 1Password separately, and a brief foray into the native 1Password agent, this combined approach hits the sweet spot for me.
It leverages 1Password's secure vault for storing the SSH key passphrase but restores the "unlock once per session" convenience I appreciate from `keychain`.
It requires a single passphrase entry via 1Password when the key is first added (typically on login/boot), after which the key remains available via the standard `ssh-agent` mechanism without further 1Password interaction for that session.
