# Crop trailing white space below page content; keep a small margin; save as JPEG for size.
import sys
from pathlib import Path
from PIL import Image, ImageChops
src, dst = map(Path, sys.argv[1:3])
for f in sorted(src.glob("*.png")):
    im = Image.open(f).convert("RGB")
    w, h = im.size
    body = im.crop((560, 0, w, h))  # skip the left sidebar when finding content bottom
    bg = Image.new("RGB", body.size, (255, 255, 255))
    bbox = ImageChops.difference(body, bg).point(lambda p: 255 if p > 12 else 0).getbbox()
    bottom = max(700, min(h, (bbox[3] if bbox else h) + 50))
    im.crop((0, 0, w, bottom)).save(dst / (f.stem + ".jpg"), quality=86, optimize=True)
    print(f.stem, h, "->", bottom)
