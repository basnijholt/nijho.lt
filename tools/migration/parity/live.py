"""Request every path of the live sitemap from the live site and a preview deploy."""

import asyncio
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from . import ParityError
from .site import norm_url, parse_sitemap

TIMEOUT = 20.0
CONCURRENCY = 16

# A status code and the normalized Location header, if any
Reply = tuple[int, str | None]


def normalize_location(location: str, request_url: str) -> str:
    """Turn a Location on the requested host or on www.nijho.lt into a path; leave other hosts absolute.

    So a preview redirecting to its own host compares equal to the live site redirecting to www.nijho.lt.
    """
    absolute = urljoin(request_url, location)
    parts = urlsplit(absolute)
    if parts.netloc == urlsplit(request_url).netloc:
        return urlunsplit(("", "", parts.path or "/", parts.query, parts.fragment))
    return norm_url(absolute)


def live_mismatch(live: Reply, preview: Reply) -> bool:
    """Whether the preview fails a path: it must return 200, or the live site's 3xx status with the same Location.

    Anything else fails, including a 404 on both sides.
    """
    status, location = preview
    return status != 200 and not (300 <= status < 400 and location is not None and preview == live)


async def _get(client: httpx.AsyncClient, semaphore: asyncio.Semaphore, url: str) -> Reply:
    async with semaphore:
        try:
            response = await client.get(url)
        except (httpx.ConnectError, httpx.TimeoutException):
            await asyncio.sleep(0.5)
            response = await client.get(url)
    location = response.headers.get("Location")
    return response.status_code, normalize_location(location, url) if location else None


async def _sweep(sitemap_url: str, preview_base: str) -> list[tuple[str, Reply, Reply]]:
    live_base = sitemap_url.removesuffix("/sitemap.xml")
    async with httpx.AsyncClient(follow_redirects=False, timeout=TIMEOUT) as client:
        sitemap = await client.get(sitemap_url)
        sitemap.raise_for_status()
        paths = parse_sitemap(sitemap.text, sitemap_url)
        if not paths:
            raise ParityError(f"{sitemap_url}: no <loc> entries")
        semaphore = asyncio.Semaphore(CONCURRENCY)
        responses = await asyncio.gather(
            *(_get(client, semaphore, base + path) for path in paths for base in (live_base, preview_base))
        )
    return list(zip(paths, responses[::2], responses[1::2]))


def live_responses(sitemap_url: str, preview_base: str) -> list[tuple[str, Reply, Reply]]:
    """Return (path, live response, preview response) for every path in the live sitemap.

    A request that cannot connect or times out is retried once.
    """
    return asyncio.run(_sweep(sitemap_url, preview_base.rstrip("/")))
