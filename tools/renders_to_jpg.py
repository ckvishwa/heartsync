"""Convert the Fusion PNG renders in cad/renders/_png/ to JPG (<= 300 KB each) in cad/renders/.

Run outside Fusion after make_renders(): python tools/renders_to_jpg.py
"""
import os
import sys

from PIL import Image

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cad", "renders")
SRC = os.path.join(HERE, "_png")
LIMIT = 300 * 1024


def main():
    done = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith(".png"):
            continue
        img = Image.open(os.path.join(SRC, fn)).convert("RGB")
        out = os.path.join(HERE, fn[:-4] + ".jpg")
        for q in (88, 82, 76, 70, 64, 58, 50):
            img.save(out, "JPEG", quality=q, optimize=True, progressive=True)
            if os.path.getsize(out) <= LIMIT:
                break
        else:
            img = img.resize((img.width * 3 // 4, img.height * 3 // 4), Image.LANCZOS)
            img.save(out, "JPEG", quality=70, optimize=True, progressive=True)
        done.append("%s %d KB (q %d)" % (os.path.basename(out), os.path.getsize(out) // 1024, q))
    print("\n".join(done))
    return 0


if __name__ == "__main__":
    sys.exit(main())
