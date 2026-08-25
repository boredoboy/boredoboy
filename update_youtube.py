import os
import json
import urllib.request
from datetime import datetime, timedelta
import re

API_KEY = os.environ.get('YOUTUBE_API_KEY')
HANDLE = "@dihantxd"
DB_FILE = 'youtube_stats.json'
README_FILE = 'README.md'

def get_youtube_stats():
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&forHandle={HANDLE}&key={API_KEY}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        stats = data['items'][0]['statistics']
        return int(stats['subscriberCount']), int(stats['viewCount'])

db = {}
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)

today = datetime.now().strftime('%Y-%m-%d')
subs, views = get_youtube_stats()
db[today] = {"subs": subs, "views": views}

def get_diff(days):
    target_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    if target_date in db:
        return subs - db[target_date]['subs'], views - db[target_date]['views']
    else:
        dates = sorted(db.keys())
        oldest = dates[0]
        return subs - db[oldest]['subs'], views - db[oldest]['views']

def format_diff(val):
    return f"+{val:,}".replace(',', ' ') if val > 0 else str(val)

d7_subs, d7_views = get_diff(7)
d14_subs, d14_views = get_diff(14)
d30_subs, d30_views = get_diff(30)
d180_subs, d180_views = get_diff(180)

stats_text = f"""
> 🔴 **YouTube: [@dihantxd](https://youtube.com/@dihantxd)**
> 📈 **Подписчики:** {subs:,} *(За неделю: {format_diff(d7_subs)} | За месяц: {format_diff(d30_subs)} | За полгода: {format_diff(d180_subs)})*
> 👁️ **Просмотры:** {views:,} *(За неделю: {format_diff(d7_views)} | За месяц: {format_diff(d30_views)} | За полгода: {format_diff(d180_views)})*
""".replace(',', ' ')

with open(README_FILE, 'r', encoding='utf-8') as f:
    readme = f.read()

readme = re.sub(
    r'<!-- YOUTUBE_STATS_START -->.*<!-- YOUTUBE_STATS_END -->',
    f'<!-- YOUTUBE_STATS_START -->\n{stats_text.strip()}\n<!-- YOUTUBE_STATS_END -->',
    readme,
    flags=re.DOTALL
)

with open(README_FILE, 'w', encoding='utf-8') as f:
    f.write(readme)

with open(DB_FILE, 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4)
