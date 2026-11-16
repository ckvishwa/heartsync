#!/usr/bin/env python3
"""Convert a PNG to a C++ sprite in the format used by firmware/src/art/Sprites.h.

The output is a 1-bit-per-pixel bitmap (rows packed MSB first) plus one colour.
A pixel is "set" if its alpha is above 127 and it is not black. The sprite's
colour is the most common colour among the set pixels.

  python tools/pixel2header.py heart.png --name Heart
  python tools/pixel2header.py avatar.png --name AvatarA >> snippet.h

Paste the output into the `sprites` namespace in Sprites.h and add a native test.
Requires: pip install pillow
"""
import argparse
import sys
from collections import Counter

from PIL import Image


def convert(path: str, name: str) -> str:
    image = Image.open(path).convert("RGBA")
    width, height = image.size
    if width > 255 or height > 255:
        raise ValueError(f"{path}: {width}x{height} is too large (max 255x255)")

    row_bytes = (width + 7) // 8
    data = []
    art = []
    colors = Counter()
    for y in range(height):
        row = [0] * row_bytes
        line = ""
        for x in range(width):
            r, g, b, a = image.getpixel((x, y))
            is_set = a > 127 and (r, g, b) != (0, 0, 0)
            if is_set:
                row[x // 8] |= 0x80 >> (x % 8)
                colors[(r, g, b)] += 1
            line += "#" if is_set else "."
        data.extend(row)
        art.append(line)

    if not colors:
        raise ValueError(f"{path}: no visible pixels")
    r, g, b = colors.most_common(1)[0][0]

    lines = [f"// {line}" for line in art]
    body = ", ".join(f"0x{byte:02X}" for byte in data)
    lines.append(f"inline constexpr uint8_t k{name}Rows[{len(data)}] = {{{body}}};")
    lines.append(
        f"inline constexpr Sprite k{name}{{{width}, {height}, k{name}Rows, Rgb{{{r}, {g}, {b}}}}};"
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="PNG to C++ sprite bitmap")
    parser.add_argument("png")
    parser.add_argument("--name", required=True, help="sprite name in CamelCase, e.g. Heart")
    args = parser.parse_args()
    if not args.name.isidentifier():
        print(f"--name must be a valid identifier, got {args.name!r}", file=sys.stderr)
        return 1
    try:
        print(convert(args.png, args.name))
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
