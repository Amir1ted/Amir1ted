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

BG = "#05070a"
FG = "#e4e9ef"
STRONG = "#c5ccd4"
WEAK = "#6f7a86"

CONTRIBUTION_FILL = re.compile(
    r"(\.cont-(top|left|right)-p\d+-(\d+)\s*\{\s*fill\s*:\s*)[^;}}]+",
    re.I,
)

CONTRIBUTION_RAMP = {
    "top": ["#151a20", "#39414b", "#626d79", "#959faa", "#d3d9df"],
    "left": ["#11151a", "#303741", "#555e68", "#7b858f", "#aeb6bf"],
    "right": ["#0d1014", "#282e36", "#48515a", "#69737e", "#929ca6"],
}


def luma(r: int, g: int, b: int) -> int:
    return max(0, min(255, round(0.2126 * r + 0.7152 * g + 0.0722 * b)))


def dark_ramp(y: int) -> int:
    # Preserve relative 3D shading while compressing the generated light theme
    # into a readable silver-on-obsidian palette.
    low, high = 24, 224
    normalized = max(0.0, min(1.0, y / 255))
    return round(low + (normalized ** 1.12) * (high - low))


def map_rgb(r: int, g: int, b: int) -> int:
    return dark_ramp(luma(r, g, b))


def hex6_to_dark(match: re.Match) -> str:
    value = match.group(1)
    y = map_rgb(int(value[:2], 16), int(value[2:4], 16), int(value[4:], 16))
    return f"#{y:02x}{y:02x}{y:02x}"


def hex3_to_dark(match: re.Match) -> str:
    value = match.group(1)
    rgb = [int(ch * 2, 16) for ch in value]
    y = map_rgb(*rgb)
    return f"#{y:02x}{y:02x}{y:02x}"


def rgb_to_dark(match: re.Match) -> str:
    r, g, b = (max(0, min(255, int(match.group(i)))) for i in (1, 2, 3))
    y = map_rgb(r, g, b)
    alpha = match.group(4)
    return f"rgba({y},{y},{y}{alpha})" if alpha else f"rgb({y},{y},{y})"


def hsl_to_dark(match: re.Match) -> str:
    h = (float(match.group(1)) % 360) / 360
    s = max(0, min(100, float(match.group(2)))) / 100
    light = max(0, min(100, float(match.group(3)))) / 100
    r, g, b = colorsys.hls_to_rgb(h, light, s)
    y = map_rgb(round(r * 255), round(g * 255), round(b * 255))
    alpha = match.group(4)
    return f"rgba({y},{y},{y}{alpha})" if alpha else f"rgb({y},{y},{y})"



def recolor_contribution_face(match: re.Match) -> str:
    face = match.group(2).lower()
    level = max(0, min(4, int(match.group(3))))
    return match.group(1) + CONTRIBUTION_RAMP[face][level]

def replace_css_rule(text: str, selector: str, property_name: str, value: str) -> str:
    pattern = re.compile(
        rf"({re.escape(selector)}\s*\{{[^}}]*?{re.escape(property_name)}\s*:\s*)[^;}}]+",
        re.I | re.S,
    )
    return pattern.sub(rf"\g<1>{value}", text)


def process(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    # First collapse any theme colors into a neutral dark silver ramp.
    text = HEX6.sub(hex6_to_dark, text)
    text = HEX3.sub(hex3_to_dark, text)
    text = RGB.sub(rgb_to_dark, text)
    text = HSL.sub(hsl_to_dark, text)

    # Contribution levels are inverted for a dark theme: empty cells stay dark
    # and higher activity becomes brighter silver.
    text = CONTRIBUTION_FILL.sub(recolor_contribution_face, text)

    # Then force semantic theme classes so the output is truly dark instead of
    # merely grayscale. These classes are emitted by github-profile-3d-contrib.
    for selector, prop, value in [
        (".fill-bg", "fill", BG),
        (".stroke-bg", "stroke", BG),
        (".fill-fg", "fill", FG),
        (".stroke-fg", "stroke", FG),
        (".fill-strong", "fill", STRONG),
        (".fill-weak", "fill", WEAK),
        (".stroke-weak", "stroke", WEAK),
    ]:
        text = replace_css_rule(text, selector, prop, value)

    # The generated SVG may include a full-canvas white background as an inline
    # value rather than through .fill-bg. Convert only obvious canvas whites.
    text = text.replace('fill="white"', f'fill="{BG}"')
    text = text.replace('fill="#ffffff"', f'fill="{BG}"')
    text = text.replace('fill="#fff"', f'fill="{BG}"')

    path.write_text(text, encoding="utf-8")
    print(f"dark monochrome: {path}")


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
