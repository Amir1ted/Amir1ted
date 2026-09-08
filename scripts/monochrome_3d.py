#!/usr/bin/env python3
from pathlib import Path
import re

HEX = re.compile(r"#([0-9a-fA-F]{6})(?![0-9a-fA-F])")
RGB = re.compile(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", re.I)

def to_gray(r, g, b):
    lum=round(0.2126*r+0.7152*g+0.0722*b)
    # Increase contrast and preserve a true-black ground.
    if lum < 28: v=0
    else: v=max(18,min(244,round((lum-28)*1.10+18)))
    return v

def gray_hex(match):
    h=match.group(1)
    r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
    v=to_gray(r,g,b)
    return f"#{v:02x}{v:02x}{v:02x}"

def gray_rgb(match):
    r,g,b=(min(255,int(match.group(i))) for i in (1,2,3))
    v=to_gray(r,g,b)
    return f"rgb({v}, {v}, {v})"

root=Path('profile-3d-contrib')
for path in root.glob('*.svg'):
    text=path.read_text(encoding='utf-8')
    text=HEX.sub(gray_hex,text)
    text=RGB.sub(gray_rgb,text)
    path.write_text(text,encoding='utf-8')
    print('monochromized',path)
