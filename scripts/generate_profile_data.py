#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict
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
            "User-Agent": "amir-profile-generator",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub GraphQL HTTP {exc.code}: {details}") from exc
    if payload.get("errors"):
        raise SystemExit("GitHub GraphQL error: " + json.dumps(payload["errors"]))
    return payload["data"]


def fetch_user_data(token: str, username: str, start: datetime, end: datetime) -> dict:
    query = r'''
    query($login: String!, $from: DateTime!, $to: DateTime!, $cursor: String) {
      user(login: $login) {
        login
        followers { totalCount }
        repositories(
          first: 100,
          after: $cursor,
          ownerAffiliations: OWNER,
          isFork: false,
          privacy: PUBLIC,
          orderBy: {field: UPDATED_AT, direction: DESC}
        ) {
          totalCount
          pageInfo { hasNextPage endCursor }
          nodes { stargazerCount }
        }
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { date contributionCount weekday }
            }
          }
        }
      }
    }
    '''
    cursor = None
    stars = 0
    user = None
    repo_count = 0
    while True:
        data = graphql(token, query, {
            "login": username,
            "from": start.isoformat().replace("+00:00", "Z"),
            "to": end.isoformat().replace("+00:00", "Z"),
            "cursor": cursor,
        })
        user = data.get("user")
        if not user:
            raise SystemExit(f"GitHub user not found: {username}")
        repos = user["repositories"]
        repo_count = repos["totalCount"]
        stars += sum(node["stargazerCount"] for node in repos["nodes"])
        if not repos["pageInfo"]["hasNextPage"]:
            break
        cursor = repos["pageInfo"]["endCursor"]
    user["_total_stars"] = stars
    user["_repo_count"] = repo_count
    return user


def flatten_days(calendar: dict) -> dict[str, int]:
    result: dict[str, int] = {}
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            result[day["date"]] = int(day["contributionCount"])
    return result


def calculate_streaks(day_counts: dict[str, int]) -> tuple[int, int, int, int]:
    if not day_counts:
        return 0, 0, 0, 0
    dates = sorted(datetime.fromisoformat(d).date() for d in day_counts)
    active_days = sum(v > 0 for v in day_counts.values())
    peak_day = max(day_counts.values(), default=0)

    longest = 0
    running = 0
    for d in dates:
        if day_counts[d.isoformat()] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    current = 0
    cursor = dates[-1]
    while cursor.isoformat() in day_counts and day_counts[cursor.isoformat()] > 0:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest, active_days, peak_day


def write_stats(username: str, calendar: dict, followers: int, repos: int, stars: int, output: Path) -> None:
    counts = flatten_days(calendar)
    current, longest, active, peak = calculate_streaks(counts)
    metrics = [
        ("CONTRIBUTIONS", str(calendar["totalContributions"]), "LAST 365 DAYS"),
        ("CURRENT STREAK", f"{current}D", "ENDING TODAY"),
        ("LONGEST STREAK", f"{longest}D", "LAST 365 DAYS"),
        ("TOTAL STARS", str(stars), "PUBLIC OWNED REPOS"),
        ("REPOSITORIES", str(repos), "PUBLIC · NON-FORK"),
        ("FOLLOWERS", str(followers), "GITHUB"),
        ("ACTIVE DAYS", str(active), "LAST 365 DAYS"),
        ("PEAK DAY", str(peak), "CONTRIBUTIONS"),
    ]
    cards = []
    for i, (label, value, note) in enumerate(metrics):
        col, row = i % 4, i // 4
        x, y = 48 + col * 231, 132 + row * 116
        cards.append(f'''
        <g transform="translate({x} {y})">
          <rect width="211" height="92" rx="12" fill="#080808" stroke="#242424"/>
          <text x="18" y="24" fill="#585858" font-family="ui-monospace, monospace" font-size="9" letter-spacing="1.7">{escape(label)}</text>
          <text x="18" y="59" fill="#efefef" font-family="Georgia, serif" font-size="27" font-weight="700">{escape(value)}</text>
          <text x="18" y="78" fill="#444444" font-family="ui-monospace, monospace" font-size="8" letter-spacing="1.2">{escape(note)}</text>
        </g>''')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="390" viewBox="0 0 1000 390" role="img" aria-label="{escape(username)} live GitHub stats">
      <rect width="1000" height="390" rx="24" fill="#050505"/>
      <text x="48" y="58" fill="#f0f0f0" font-family="Georgia, serif" font-size="31" letter-spacing="3">GITHUB / STATS</text>
      <text x="48" y="86" fill="#5f5f5f" font-family="ui-monospace, monospace" font-size="10" letter-spacing="3">LIVE PROFILE TELEMETRY · {escape(username.upper())}</text>
      <path d="M48 108H952" stroke="#242424"/>
      {''.join(cards)}
      <text x="952" y="366" text-anchor="end" fill="#3c3c3c" font-family="ui-monospace, monospace" font-size="8">generated by GitHub Actions</text>
    </svg>'''
    output.write_text(svg, encoding="utf-8")


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
    start, end = dates[0], dates[-1]
    aligned_start = start - timedelta(days=(start.weekday() + 1) % 7)
    weeks = math.ceil(((end - aligned_start).days + 1) / 7)
    cell, gap = 11, 4
    x0, y0 = 72, 142
    palette = ["#101010", "#2d2d2d", "#565656", "#969696", "#f0f0f0"]
    rects, month_labels = [], []
    seen_month = None

    for i in range(weeks * 7):
        day = aligned_start + timedelta(days=i)
        if day > end:
            break
        week = i // 7
        dow = (day.weekday() + 1) % 7
        count = counts.get(day.isoformat(), 0)
        x = x0 + week * (cell + gap)
        y = y0 + dow * (cell + gap)
        fill = palette[intensity(count)] if day >= start else "#090909"
        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{fill}">'
            f'<title>{day.isoformat()}: {count} contributions</title></rect>'
        )
        if day.day <= 7 and day.month != seen_month and dow == 0:
            seen_month = day.month
            month_labels.append(
                f'<text x="{x}" y="125" fill="#4f4f4f" font-family="ui-monospace, monospace" font-size="9">{day.strftime("%b").upper()}</text>'
            )

    weekly = defaultdict(int)
    for date_text, count in counts.items():
        day = datetime.fromisoformat(date_text).date()
        weekly[(day - aligned_start).days // 7] += count
    max_week = max(weekly.values(), default=1)
    signal = []
    baseline = 310
    for week in range(weeks):
        x = x0 + week * (cell + gap)
        height = 40 * weekly.get(week, 0) / max_week if max_week else 0
        signal.append(f'<rect x="{x}" y="{baseline-height:.1f}" width="{cell}" height="{height:.1f}" rx="2" fill="#6f6f6f"/>')

    legend = ''.join(
        f'<rect x="{40+i*18}" y="-9" width="11" height="11" rx="2" fill="{color}"/>'
        for i, color in enumerate(palette)
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="365" viewBox="0 0 1000 365" role="img" aria-label="{escape(username)} contribution graph">
      <rect width="1000" height="365" rx="24" fill="#050505"/>
      <text x="48" y="58" fill="#f0f0f0" font-family="Georgia, serif" font-size="31" letter-spacing="3">CONTRIBUTION / GRAPH</text>
      <text x="48" y="86" fill="#5f5f5f" font-family="ui-monospace, monospace" font-size="10" letter-spacing="3">LAST 365 DAYS · MONOCHROME SIGNAL MAP</text>
      <path d="M48 108H952" stroke="#242424"/>
      {''.join(month_labels)}
      <text x="42" y="153" fill="#3f3f3f" font-family="ui-monospace, monospace" font-size="8">SUN</text>
      <text x="42" y="183" fill="#3f3f3f" font-family="ui-monospace, monospace" font-size="8">TUE</text>
      <text x="42" y="213" fill="#3f3f3f" font-family="ui-monospace, monospace" font-size="8">THU</text>
      <text x="42" y="243" fill="#3f3f3f" font-family="ui-monospace, monospace" font-size="8">SAT</text>
      {''.join(rects)}
      <text x="72" y="337" fill="#424242" font-family="ui-monospace, monospace" font-size="9" letter-spacing="2">WEEKLY SIGNAL</text>
      {''.join(signal)}
      <g transform="translate(775 330)">
        <text x="0" y="0" fill="#414141" font-family="ui-monospace, monospace" font-size="8">LESS</text>
        {legend}
        <text x="140" y="0" fill="#414141" font-family="ui-monospace, monospace" font-size="8">MORE</text>
      </g>
    </svg>'''
    output.write_text(svg, encoding="utf-8")


def main() -> int:
    token = require_env("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_USERNAME", "Amir1ted").strip() or "Amir1ted"
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=364)
    user = fetch_user_data(token, username, start, now)
    calendar = user["contributionsCollection"]["contributionCalendar"]
    ASSETS.mkdir(parents=True, exist_ok=True)
    write_stats(
        username,
        calendar,
        user["followers"]["totalCount"],
        user["_repo_count"],
        user["_total_stars"],
        ASSETS / "github-stats.svg",
    )
    write_graph(username, calendar, ASSETS / "contribution-graph.svg")
    print("Generated github-stats.svg and contribution-graph.svg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
