#!/usr/bin/env python3
from __future__ import annotations

import colorsys
import re
import sys
from pathlib import Path

HEX6 = re.compile(r"#([0-9a-fA-F]{6})(?![0-9a-fA-F])")
HEX3 = re.compile(r"#([0-9a-fA-F]{3})(?![0-9a-fA-F])")
RGB = re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(\s*,\s*[\d.]+\s*)?\)", re.I)
HSL = re.compile(r"hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%(\s*,\s*[\d.]+\s*)?\)", re.I)


def gray(r: int, g: int, b: int) -> int:
    return max(0, min(255, round(0.2126 * r + 0.7152 * g + 0.0722 * b)))


def hex6_to_gray(match: re.Match) -> str:
    value = match.group(1)
    r, g, b = int(value[:2], 16), int(value[2:4], 16), int(value[4:], 16)
    y = gray(r, g, b)
    return f"#{y:02x}{y:02x}{y:02x}"


def hex3_to_gray(match: re.Match) -> str:
    value = match.group(1)
    r, g, b = (int(ch * 2, 16) for ch in value)
    y = gray(r, g, b)
    return f"#{y:02x}{y:02x}{y:02x}"


def rgb_to_gray(match: re.Match) -> str:
    r, g, b = (max(0, min(255, int(match.group(i)))) for i in (1, 2, 3))
    y = gray(r, g, b)
    alpha = match.group(4)
    return f"rgba({y},{y},{y}{alpha})" if alpha else f"rgb({y},{y},{y})"


def hsl_to_gray(match: re.Match) -> str:
    h = (float(match.group(1)) % 360) / 360
    s = max(0, min(100, float(match.group(2)))) / 100
    l = max(0, min(100, float(match.group(3)))) / 100
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    y = gray(round(r * 255), round(g * 255), round(b * 255))
    alpha = match.group(4)
    return f"rgba({y},{y},{y}{alpha})" if alpha else f"rgb({y},{y},{y})"


def process(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = HEX6.sub(hex6_to_gray, text)
    text = HEX3.sub(hex3_to_gray, text)
    text = RGB.sub(rgb_to_gray, text)
    text = HSL.sub(hsl_to_gray, text)
    path.write_text(text, encoding="utf-8")
    print(f"monochrome: {path}")


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]] or [
        Path("profile-3d-contrib/profile-season-animate.svg"),
        Path("profile-3d-contrib/profile-night-view.svg"),
    ]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("Missing generated SVG(s): " + ", ".join(missing))
    for path in paths:
        process(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
