#!/usr/bin/env python3
from pathlib import Path
import re
HEX6=re.compile(r"#([0-9a-fA-F]{6})(?![0-9a-fA-F])")
HEX3=re.compile(r"#([0-9a-fA-F]{3})(?![0-9a-fA-F])")
RGB=re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(?:\s*,\s*([0-9.]+))?\s*\)",re.I)
def gray(r,g,b):
    lum=round(.2126*r+.7152*g+.0722*b)
    if lum<22:return 0
    return max(18,min(244,round((lum-22)*1.08+18)))
def h6(m):
    h=m.group(1); r,g,b=[int(h[i:i+2],16) for i in (0,2,4)];v=gray(r,g,b);return f'#{v:02x}{v:02x}{v:02x}'
def h3(m):
    h=m.group(1); r,g,b=[int(c*2,16) for c in h];v=gray(r,g,b);return f'#{v:02x}{v:02x}{v:02x}'
def rgb(m):
    r,g,b=[min(255,int(m.group(i))) for i in (1,2,3)];v=gray(r,g,b);a=m.group(4)
    return f'rgba({v},{v},{v},{a})' if a is not None else f'rgb({v},{v},{v})'
root=Path('profile-3d-contrib')
for p in root.glob('*.svg'):
    s=p.read_text(encoding='utf-8')
    s=HEX6.sub(h6,s);s=HEX3.sub(h3,s);s=RGB.sub(rgb,s)
    p.write_text(s,encoding='utf-8');print('monochromized',p)
