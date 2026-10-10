"""Draw the homepage's contact map from OpenStreetMap tiles, centered on the coordinates in content/home/contact.md.

    uv run --with pillow python contact_map.py [--zoom 10]

Writes assets/media/map.webp (800x560). The page puts the marker at the image's center and credits OpenStreetMap
contributors, so run this again after changing content.coordinates.
"""

import argparse
import io
import math
from pathlib import Path

import httpx
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CONTACT = ROOT / "content/home/contact.md"
OUT = ROOT / "assets/media/map.webp"
WIDTH, HEIGHT, TILE = 800, 560, 256
TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
# The OpenStreetMap tile policy asks for a User-Agent that identifies the application.
HEADERS = {"User-Agent": "nijho.lt contact map (https://github.com/basnijholt/nijho.lt)"}


def world_pixel(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """The Web Mercator pixel of a coordinate in the whole-world image at zoom."""
    scale = TILE * 2**zoom
    x = (lon + 180) / 360 * scale
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * scale
    return x, y


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zoom", type=int, default=10, help="OpenStreetMap zoom level (default 10)")
    args = parser.parse_args()
    coordinates = yaml.safe_load(CONTACT.read_text(encoding="utf-8").split("---")[1])["content"]["coordinates"]
    cx, cy = world_pixel(float(coordinates["latitude"]), float(coordinates["longitude"]), args.zoom)
    left, top = cx - WIDTH / 2, cy - HEIGHT / 2
    image = Image.new("RGB", (WIDTH, HEIGHT))
    with httpx.Client(headers=HEADERS, timeout=30) as client:
        for tx in range(math.floor(left / TILE), math.floor((left + WIDTH) / TILE) + 1):
            for ty in range(math.floor(top / TILE), math.floor((top + HEIGHT) / TILE) + 1):
                response = client.get(TILES.format(z=args.zoom, x=tx, y=ty))
                response.raise_for_status()
                tile = Image.open(io.BytesIO(response.content)).convert("RGB")
                image.paste(tile, (round(tx * TILE - left), round(ty * TILE - top)))
    image.save(OUT, "webp", quality=80)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
