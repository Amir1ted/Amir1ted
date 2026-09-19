#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
API = "https://api.github.com/graphql"


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def graphql(token: str, query: str, variables: dict) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        API,
        data=body,
        method="POST",
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "amirhosse1n-profile-generator",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub GraphQL HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"GitHub GraphQL network error: {exc}") from exc

    if payload.get("errors"):
        raise SystemExit("GitHub GraphQL error: " + json.dumps(payload["errors"]))
    return payload["data"]


def fetch_calendar(token: str, username: str, start: datetime, end: datetime) -> dict:
    query = r'''
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        login
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                weekday
              }
            }
          }
        }
      }
    }
    '''
    data = graphql(
        token,
        query,
        {
            "login": username,
            "from": start.isoformat().replace("+00:00", "Z"),
            "to": end.isoformat().replace("+00:00", "Z"),
        },
    )
    user = data.get("user")
    if not user:
        raise SystemExit(f"GitHub user not found: {username}")
    return user["contributionsCollection"]["contributionCalendar"]


def flatten_days(calendar: dict) -> dict[str, int]:
    result: dict[str, int] = {}
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            result[day["date"]] = int(day["contributionCount"])
    return result


def intensity(count: int) -> int:
    if count <= 0:
        return 0
    if count == 1:
        return 1
    if count <= 3:
        return 2
    if count <= 6:
        return 3
    return 4


def write_graph(username: str, calendar: dict, output: Path) -> None:
    counts = flatten_days(calendar)
    if not counts:
        raise SystemExit("No contribution days returned")

    dates = sorted(datetime.fromisoformat(d).date() for d in counts)
    end = dates[-1]
    start = end - timedelta(days=364)
    counts = {d: c for d, c in counts.items() if start <= datetime.fromisoformat(d).date() <= end}
    aligned_start = start - timedelta(days=(start.weekday() + 1) % 7)
    weeks = math.ceil(((end - aligned_start).days + 1) / 7)

    cell, gap = 11, 4
    x0, y0 = 76, 142
    palette = ["#0C1015", "#252B33", "#4A535E", "#89939F", "#E1E6EC"]
    rects: list[str] = []
    month_labels: list[str] = []
    seen_month: tuple[int, int] | None = None

    for i in range(weeks * 7):
        day = aligned_start + timedelta(days=i)
        if day > end:
            break
        if day < start:
            continue
        week = i // 7
        dow = (day.weekday() + 1) % 7
        count = counts.get(day.isoformat(), 0)
        x = x0 + week * (cell + gap)
        y = y0 + dow * (cell + gap)
        fill = palette[intensity(count)] if day >= start else "#080B0F"
        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{fill}">'
            f'<title>{day.isoformat()}: {count} contributions</title></rect>'
        )

        month_key = (day.year, day.month)
        if day.day <= 7 and month_key != seen_month and dow == 0:
            seen_month = month_key
            month_labels.append(
                f'<text x="{x}" y="123" fill="#59636F" '
                f'font-family="ui-monospace, monospace" font-size="8.5" letter-spacing=".8">'
                f'{day.strftime("%b").upper()}</text>'
            )

    legend = "".join(
        f'<rect x="{i * 18}" y="-9" width="11" height="11" rx="2" fill="{color}"/>'
        for i, color in enumerate(palette)
    )

    total = int(calendar.get("totalContributions", 0))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="300" viewBox="0 0 1000 300" role="img" aria-labelledby="title desc">
  <title id="title">{escape(username)} contribution graph</title>
  <desc id="desc">GitHub contribution activity for the last 365 days. {total} contributions in the displayed period.</desc>
  <rect width="1000" height="300" rx="22" fill="#05070A"/>
  <text x="52" y="57" fill="#E8EDF3" font-family="Georgia, 'Times New Roman', serif" font-size="29" letter-spacing="3">CONTRIBUTION / GRAPH</text>
  <text x="52" y="83" fill="#606B77" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="9.5" letter-spacing="2.7">LAST 365 DAYS · LIVE GITHUB ACTIVITY</text>
  <text x="948" y="57" text-anchor="end" fill="#AAB3BD" font-family="ui-monospace, monospace" font-size="12" letter-spacing="1.2">{total} CONTRIBUTIONS</text>
  <path d="M52 103H948" stroke="#20262E"/>
  {''.join(month_labels)}
  <text x="45" y="151" fill="#4F5965" font-family="ui-monospace, monospace" font-size="7.5">SUN</text>
  <text x="45" y="181" fill="#4F5965" font-family="ui-monospace, monospace" font-size="7.5">TUE</text>
  <text x="45" y="211" fill="#4F5965" font-family="ui-monospace, monospace" font-size="7.5">THU</text>
  <text x="45" y="241" fill="#4F5965" font-family="ui-monospace, monospace" font-size="7.5">SAT</text>
  {''.join(rects)}
  <g transform="translate(808 276)">
    <text x="-42" y="0" fill="#4F5965" font-family="ui-monospace, monospace" font-size="7.5">LESS</text>
    {legend}
    <text x="98" y="0" fill="#4F5965" font-family="ui-monospace, monospace" font-size="7.5">MORE</text>
  </g>
</svg>'''
    output.write_text(svg, encoding="utf-8")


def main() -> int:
    token = require_env("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_USERNAME", "amirhosse1n").strip() or "amirhosse1n"
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=364)

    calendar = fetch_calendar(token, username, start, now)
    ASSETS.mkdir(parents=True, exist_ok=True)
    write_graph(username, calendar, ASSETS / "contribution-graph.svg")
    print(f"Generated contribution graph for {username}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
