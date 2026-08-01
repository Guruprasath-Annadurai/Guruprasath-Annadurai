#!/usr/bin/env python3
"""
Prep a photo for ASCII conversion: remove background, boost local
contrast, composite onto white. Run once per photo:

    python scripts/prep_photo.py source-photo.jpg

Writes source-prepped.png next to the input (or to the path given
as a second argument).
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep(src_path: str, out_path: str) -> None:
    src_bytes = Path(src_path).read_bytes()

    # 1. Remove background -> RGBA with subject isolated.
    cutout_bytes = remove(src_bytes)
    cutout = Image.open(__import__("io").BytesIO(cutout_bytes)).convert("RGBA")

    # 2. Boost local contrast with CLAHE on the luminance channel.
    rgb = np.array(cutout.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    contrasted = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    contrasted_img = Image.fromarray(contrasted).convert("RGBA")
    contrasted_img.putalpha(cutout.getchannel("A"))

    # 3. Composite onto pure white so background maps to blank glyphs.
    white_bg = Image.new("RGBA", contrasted_img.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, contrasted_img).convert("L")

    composited.save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: prep_photo.py <source-photo> [out-path]", file=sys.stderr)
        sys.exit(1)

    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"
    prep(src, out)
