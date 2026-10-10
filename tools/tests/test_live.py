"""The live sweep: every live sitemap path must work on the preview, checked against local HTTP servers."""

import http.server
import socket
import threading
import time
from contextlib import contextmanager

import pytest

from conftest import sitemap
from parity.live import live_mismatch, live_responses, normalize_location

PREVIEW = "http://preview.example/old/"


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        pytest.param("/new/", "/new/", id="path"),
        pytest.param("new/", "/old/new/", id="relative"),
        pytest.param("http://preview.example/new/?a=1#b", "/new/?a=1#b", id="own-host"),
        pytest.param("http://preview.example", "/", id="own-host-root"),
        pytest.param("https://www.nijho.lt/new/", "/new/", id="live-host"),
        pytest.param("https://elsewhere.example/new/", "https://elsewhere.example/new/", id="other-host"),
    ],
)
def test_location_on_the_preview_or_live_host_becomes_a_path(location, expected):
    assert normalize_location(location, PREVIEW) == expected


@pytest.mark.parametrize(
    ("live", "preview", "mismatch"),
    [
        pytest.param((200, None), (200, None), False, id="both-200"),
        pytest.param((301, "/a/"), (200, None), False, id="redirect-now-200"),
        pytest.param((301, "/a/"), (301, "/a/"), False, id="same-301"),
        pytest.param((301, "/a/"), (301, "/b/"), True, id="301-elsewhere"),
        pytest.param((308, "/a/"), (308, "/b/"), True, id="308-elsewhere"),
        pytest.param((301, "/a/"), (302, "/a/"), True, id="301-became-302"),
        pytest.param((200, None), (301, "/a/"), True, id="200-became-301"),
        pytest.param((301, None), (301, None), True, id="301-without-location"),
        pytest.param((404, None), (404, None), True, id="both-404"),
        pytest.param((200, None), (204, None), True, id="other-2xx"),
        pytest.param((200, None), (500, None), True, id="server-error"),
    ],
)
def test_preview_must_return_200_or_the_live_redirect(live, preview, mismatch):
    assert live_mismatch(live, preview) is mismatch


class Server(http.server.ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        """A handler that fails shows up as a failed request in the client; keep stderr quiet."""


@contextmanager
def serve(routes, on_request=None):
    """Serve routes (path -> (status, Location or None, body)); other paths 404. Yield the base URL.

    routes may be filled in after start; on_request(path) runs before every answer except the sitemap's.
    """

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if on_request and self.path != "/sitemap.xml":
                on_request(self.path)
            status, location, body = routes.get(self.path, (404, None, ""))
            self.send_response(status)
            if location:
                self.send_header("Location", location)
            self.send_header("Content-Length", str(len(body.encode())))
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, format, *args):
            pass

    server = Server(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def site(paths, **overrides):
    """Routes for a site whose sitemap lists paths; every path answers 200 unless overridden."""
    return {path: (200, None, "") for path in paths} | overrides | {"/sitemap.xml": (200, None, sitemap(paths))}


MOVED = (301, "https://www.nijho.lt/new/", "")


def test_live_passes_identical_sites(cli):
    with serve(site(["/", "/page/", "/old/"], **{"/old/": MOVED})) as base:
        assert cli("live", "--preview", base + "/", "--sitemap", f"{base}/sitemap.xml") == (
            0, "All 3 sitemap paths OK on the preview\n", ""
        )


@pytest.mark.parametrize(
    ("live_routes", "preview_routes", "line"),
    [
        pytest.param(site(["/", "/page/"]), site(["/"]), "/page/: live=200, preview=404", id="preview-404"),
        pytest.param(
            site(["/gone/"], **{"/gone/": (404, None, "")}), {}, "/gone/: live=404, preview=404", id="both-404"
        ),
        pytest.param(
            site(["/old/"], **{"/old/": MOVED}), {"/old/": (301, "/elsewhere/", "")},
            "/old/: live=301 -> /new/, preview=301 -> /elsewhere/", id="other-location",
        ),
        pytest.param(
            site(["/old/"], **{"/old/": MOVED}), {"/old/": (302, "/new/", "")},
            "/old/: live=301 -> /new/, preview=302 -> /new/", id="other-status",
        ),
    ],
)
def test_live_reports_mismatch(cli, live_routes, preview_routes, line):
    with serve(live_routes) as live, serve(preview_routes) as preview:
        assert cli("live", "--preview", preview, "--sitemap", f"{live}/sitemap.xml") == (
            1, f"Mismatches found:\n  {line}\n", ""
        )


def test_live_preview_redirect_to_its_own_host_matches_live_redirect(cli):
    preview_routes = {}
    with serve(site(["/old/"], **{"/old/": MOVED})) as live, serve(preview_routes) as preview:
        preview_routes["/old/"] = (301, f"{preview}/new/", "")
        assert cli("live", "--preview", preview, "--sitemap", f"{live}/sitemap.xml")[0] == 0


def test_live_names_the_url_it_cannot_reach(cli):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{sock.getsockname()[1]}/sitemap.xml"
    assert cli("live", "--preview", "http://127.0.0.1:1", "--sitemap", url)[0].startswith(f"Error: {url}: ")


def test_live_names_a_malformed_sitemap(cli):
    with serve({"/sitemap.xml": (200, None, "<urlset>")}) as base:
        url = f"{base}/sitemap.xml"
        assert cli("live", "--preview", base, "--sitemap", url) == (
            f"Error: {url}: invalid XML: no element found: line 1, column 8", "", ""
        )


def test_live_refuses_a_sitemap_without_locs(cli):
    with serve({"/sitemap.xml": (200, None, sitemap([]))}) as base:
        url = f"{base}/sitemap.xml"
        assert cli("live", "--preview", base, "--sitemap", url) == (f"Error: {url}: no <loc> entries", "", "")


def test_live_retries_a_request_that_timed_out(monkeypatch):
    monkeypatch.setattr("parity.live.TIMEOUT", 0.3)
    stalled = threading.Event()

    def stall_once(path):
        if not stalled.is_set():
            stalled.set()
            time.sleep(2)

    with serve(site(["/page/"]), stall_once) as base:
        assert live_responses(f"{base}/sitemap.xml", base) == [("/page/", (200, None), (200, None))]


def test_live_keeps_16_requests_in_flight():
    """The barrier answers requests in groups of 16 and holds each group briefly, so a 17th would be counted.

    Every path is requested from both sites, so 40 paths make 80 requests: five full groups. A request count that is
    not a multiple of 16 would leave a group that never fills.
    """
    lock = threading.Lock()
    count = {"in_flight": 0, "peak": 0}
    barrier = threading.Barrier(16, action=lambda: time.sleep(0.05), timeout=5)

    def wait_for_16(path):
        with lock:
            count["in_flight"] += 1
            count["peak"] = max(count["peak"], count["in_flight"])
        barrier.wait()
        with lock:
            count["in_flight"] -= 1

    paths = [f"/page{i}/" for i in range(5 * 16 // 2)]
    with serve(site(paths), wait_for_16) as base:
        responses = live_responses(f"{base}/sitemap.xml", base)
    assert responses == [(path, (200, None), (200, None)) for path in paths]
    assert count["peak"] == 16
