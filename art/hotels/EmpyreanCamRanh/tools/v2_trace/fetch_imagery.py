"""Download the aerial tiles used to trace the v2 site plan and build the mosaics.

Imagery is NOT stored in the repository (provider terms).  Run:
  python fetch_imagery.py WORKDIR
WORKDIR receives tiles/, mosaic19_bing.jpg (oblique detail), mosaic18_esri.jpg and
esri_on_bing_grid.jpg (near-nadir footprints, resampled onto the z19 Bing grid).
Requires Pillow.
"""
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

UA = {"User-Agent": "Mozilla/5.0"}
BING_Z19 = (421196, 421209, 244495, 244507)     # x0, x1, y0, y1 (inclusive)
ESRI_Z18 = (210598, 210604, 122248, 122253)


def quadkey(x, y, z):
    q = ""
    for i in range(z, 0, -1):
        d, m = 0, 1 << (i - 1)
        if x & m:
            d += 1
        if y & m:
            d += 2
        q += str(d)
    return q


def fetch(args):
    url, fn = args
    if not os.path.exists(fn):
        with open(fn, "wb") as fh:
            fh.write(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read())


def mosaic(tiles, src, z, box, out):
    x0, x1, y0, y1 = box
    im = Image.new("RGB", ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            im.paste(Image.open(os.path.join(tiles, f"t_{src}_{z}_{x}_{y}.jpg")).convert("RGB"), ((x - x0) * 256, (y - y0) * 256))
    im.save(out, quality=92)
    return im


def main(work):
    tiles = os.path.join(work, "tiles")
    os.makedirs(tiles, exist_ok=True)
    jobs = []
    x0, x1, y0, y1 = BING_Z19
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            jobs.append((f"https://ecn.t{(x + y) % 4}.tiles.virtualearth.net/tiles/a{quadkey(x, y, 19)}.jpeg?g=1",
                         os.path.join(tiles, f"t_bing_19_{x}_{y}.jpg")))
    x0, x1, y0, y1 = ESRI_Z18
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            jobs.append((f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/18/{y}/{x}",
                         os.path.join(tiles, f"t_esri_18_{x}_{y}.jpg")))
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(fetch, jobs))
    b = mosaic(tiles, "bing", 19, BING_Z19, os.path.join(work, "mosaic19_bing.jpg"))
    e = mosaic(tiles, "esri", 18, ESRI_Z18, os.path.join(work, "mosaic18_esri.jpg"))
    # z18 tile (210598,122248) == z19 (421196,244496): one z19 row below the Bing origin -> +256 px
    e2 = e.resize((e.width * 2, e.height * 2), Image.BICUBIC)
    grid = Image.new("RGB", b.size)
    grid.paste(e2.crop((0, 0, b.width, b.height - 256)), (0, 256))
    grid.save(os.path.join(work, "esri_on_bing_grid.jpg"), quality=92)


if __name__ == "__main__":
    main(sys.argv[1])
