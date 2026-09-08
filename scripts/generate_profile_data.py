#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.request, datetime as dt, html, math
from pathlib import Path

TOKEN=os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
USER=os.environ.get('USERNAME') or os.environ.get('GITHUB_REPOSITORY_OWNER')
if not TOKEN or not USER:
    raise SystemExit('GITHUB_TOKEN and USERNAME are required')

QUERY=r'''
query($login:String!){
  user(login:$login){
    followers{totalCount}
    repositories(first:100, ownerAffiliations:OWNER, isFork:false){
      totalCount
      nodes{stargazerCount}
    }
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{contributionDays{date contributionCount contributionLevel weekday}}
      }
    }
  }
}
'''
req=urllib.request.Request(
    'https://api.github.com/graphql',
    data=json.dumps({'query':QUERY,'variables':{'login':USER}}).encode(),
    headers={'Authorization':f'bearer {TOKEN}','Content-Type':'application/json','User-Agent':'amir-profile-workflow'}
)
with urllib.request.urlopen(req,timeout=30) as r:
    payload=json.load(r)
if payload.get('errors'):
    raise SystemExit('GraphQL error: '+json.dumps(payload['errors']))
u=payload['data']['user']
if not u: raise SystemExit('GitHub user not found')
cal=u['contributionsCollection']['contributionCalendar']
weeks=cal['weeks']
days=[]
for wi,w in enumerate(weeks):
    for d in w['contributionDays']:
        d=dict(d); d['week']=wi; days.append(d)

total=cal['totalContributions']
followers=u['followers']['totalCount']
repos=u['repositories']['totalCount']
stars=sum(n['stargazerCount'] for n in u['repositories']['nodes'])
active=sum(1 for d in days if d['contributionCount']>0)
peak=max((d['contributionCount'] for d in days),default=0)

# streaks: current can end yesterday when today is still empty.
bydate={dt.date.fromisoformat(d['date']):d['contributionCount'] for d in days}
today=dt.date.today()
end=today if bydate.get(today,0)>0 else today-dt.timedelta(days=1)
current=0
cur=end
while bydate.get(cur,0)>0:
    current+=1; cur-=dt.timedelta(days=1)
longest=0; run=0
for d in sorted(days,key=lambda x:x['date']):
    if d['contributionCount']>0: run+=1; longest=max(longest,run)
    else: run=0

OUT=Path('assets'); OUT.mkdir(exist_ok=True)

def stat_card(x,label,value,sub=''):
    return f'''<g transform="translate({x},112)"><rect width="250" height="118" rx="12" fill="#080808" stroke="#2b2b2b"/><text x="18" y="29" class="mono" fill="#747474" font-size="10" letter-spacing="1.8">{html.escape(label)}</text><text x="18" y="76" class="sans" fill="#f4f4f4" font-size="35" font-weight="750">{html.escape(str(value))}</text><text x="18" y="99" class="mono" fill="#6d6d6d" font-size="9.5">{html.escape(sub)}</text></g>'''

stats=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360" role="img" aria-label="Live GitHub stats for {html.escape(USER)}"><defs><style><![CDATA[.sans{{font-family:Inter,'Segoe UI',Arial,sans-serif}}.mono{{font-family:'SFMono-Regular',Consolas,monospace}}.p{{animation:p 3s ease-in-out infinite}}@keyframes p{{0%,100%{{opacity:.25}}50%{{opacity:1}}}}]]></style></defs><rect width="1200" height="360" fill="#000"/><rect x="14" y="14" width="1172" height="332" rx="18" fill="#040404" stroke="#242424"/><text x="50" y="57" class="mono" fill="#777" font-size="12" letter-spacing="3">GITHUB / LIVE SIGNAL</text><text x="1150" y="57" text-anchor="end" class="mono" fill="#5f5f5f" font-size="10">SYNCED {dt.datetime.utcnow().strftime('%Y-%m-%d')} UTC</text><circle cx="1125" cy="53" r="3.5" fill="#eee" class="p"/><path d="M50 82H1150" stroke="#242424"/>{stat_card(50,'TOTAL CONTRIBUTIONS',total,'rolling GitHub calendar')}{stat_card(330,'CURRENT STREAK',str(current)+'D','consecutive active days')}{stat_card(610,'LONGEST STREAK',str(longest)+'D','within the current calendar')}{stat_card(890,'TOTAL STARS',stars,'public owned repositories')}<g class="mono" font-size="11" fill="#8a8a8a"><text x="58" y="292">REPOSITORIES <tspan fill="#ececec">{repos}</tspan></text><text x="330" y="292">FOLLOWERS <tspan fill="#ececec">{followers}</tspan></text><text x="610" y="292">ACTIVE DAYS <tspan fill="#ececec">{active}</tspan></text><text x="890" y="292">PEAK DAY <tspan fill="#ececec">{peak}</tspan></text></g><path d="M50 315H1150" stroke="#1d1d1d"/><text x="600" y="335" text-anchor="middle" class="mono" fill="#505050" font-size="9.5">generated inside this repository · no external stats card service</text></svg>'''
(OUT/'github-stats.svg').write_text(stats)

# Contribution calendar. Use GitHub's contributionLevel, recolored into grayscale.
LEVEL={'NONE':'#0b0b0b','FIRST_QUARTILE':'#303030','SECOND_QUARTILE':'#666666','THIRD_QUARTILE':'#aaaaaa','FOURTH_QUARTILE':'#f1f1f1'}
cell=14; gap=4; x0=120; y0=118
parts=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="390" viewBox="0 0 1200 390" role="img" aria-label="Monochrome GitHub contribution graph for {html.escape(USER)}"><defs><style><![CDATA[.sans{{font-family:Inter,'Segoe UI',Arial,sans-serif}}.mono{{font-family:'SFMono-Regular',Consolas,monospace}}]]></style></defs><rect width="1200" height="390" fill="#000"/><rect x="14" y="14" width="1172" height="362" rx="18" fill="#040404" stroke="#242424"/><text x="50" y="58" class="mono" fill="#777" font-size="12" letter-spacing="3">CONTRIBUTION / 365-DAY SIGNAL</text><text x="1150" y="58" text-anchor="end" class="mono" fill="#d7d7d7" font-size="12">{total} CONTRIBUTIONS</text><path d="M50 82H1150" stroke="#242424"/>''']
# month labels based on first visible day per month
seen=set()
for wi,w in enumerate(weeks):
    for d in w['contributionDays']:
        date=dt.date.fromisoformat(d['date'])
        key=(date.year,date.month)
        if key not in seen and date.day<=7:
            seen.add(key)
            x=x0+wi*(cell+gap)
            parts.append(f'<text x="{x}" y="103" class="mono" fill="#626262" font-size="9">{date.strftime("%b").upper()}</text>')
# weekday labels
for lab,row in [('MON',1),('WED',3),('FRI',5)]:
    parts.append(f'<text x="82" y="{y0+row*(cell+gap)+11}" text-anchor="end" class="mono" fill="#555" font-size="8.5">{lab}</text>')
for wi,w in enumerate(weeks):
    ds=w['contributionDays']
    for ri,d in enumerate(ds):
        x=x0+wi*(cell+gap); y=y0+ri*(cell+gap); fill=LEVEL.get(d['contributionLevel'],'#444')
        title=f"{d['date']}: {d['contributionCount']} contributions"
        parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{fill}" stroke="#1e1e1e"><title>{html.escape(title)}</title></rect>')
# weekly signal bars underneath
weekly=[sum(d['contributionCount'] for d in w['contributionDays']) for w in weeks]
mx=max(weekly or [1])
base=306
parts.append('<path d="M120 306H1075" stroke="#1e1e1e"/>')
for wi,val in enumerate(weekly):
    x=x0+wi*(cell+gap)+2; h=0 if mx==0 else 35*val/mx
    parts.append(f'<rect x="{x}" y="{base-h:.1f}" width="10" height="{h:.1f}" fill="#bdbdbd" opacity=".72"/>')
parts.append('<g class="mono" font-size="9" fill="#5d5d5d"><text x="120" y="344">LESS</text><rect x="160" y="334" width="12" height="12" rx="2" fill="#0b0b0b" stroke="#1e1e1e"/><rect x="180" y="334" width="12" height="12" rx="2" fill="#303030"/><rect x="200" y="334" width="12" height="12" rx="2" fill="#666"/><rect x="220" y="334" width="12" height="12" rx="2" fill="#aaa"/><rect x="240" y="334" width="12" height="12" rx="2" fill="#f1f1f1"/><text x="262" y="344">MORE</text><text x="1150" y="344" text-anchor="end">generated from GitHub GraphQL · monochrome only</text></g></svg>')
(OUT/'contribution-graph.svg').write_text(''.join(parts))
print('generated',OUT/'github-stats.svg',OUT/'contribution-graph.svg')
