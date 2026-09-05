import os
import json
import urllib.request
from datetime import datetime, timedelta
import re

API_KEY = os.environ.get('YOUTUBE_API_KEY')
HANDLE = "@dihantxd"
DB_FILE = 'youtube_stats.json'
README_FILE = 'README.md'

# 1. Получаем данные с YouTube
def get_youtube_stats():
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&forHandle={HANDLE}&key={API_KEY}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        stats = data['items'][0]['statistics']
        return int(stats['subscriberCount']), int(stats['viewCount'])

# 2. Грузим JSON базу
db = {}
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)

today_obj = datetime.now()
today_str = today_obj.strftime('%Y-%m-%d')
subs, views = get_youtube_stats()

# Записываем сегодняшний день
db[today_str] = {"subs": subs, "views": views}

# Функция разницы для статистики в тексте
def get_diff(target_days):
    target_date_str = (today_obj - timedelta(days=target_days)).strftime('%Y-%m-%d')
    if target_date_str in db:
        return subs - db[target_date_str]['subs'], views - db[target_date_str]['views'], target_days
    else:
        dates = sorted(db.keys())
        oldest_str = dates[0]
        oldest_date_obj = datetime.strptime(oldest_str, '%Y-%m-%d')
        actual_days = (today_obj - oldest_date_obj).days
        if actual_days == 0: actual_days = 1 
        return subs - db[oldest_str]['subs'], views - db[oldest_str]['views'], actual_days

def format_diff(val):
    return f"+{val:,}".replace(',', ' ') if val > 0 else str(val)

d7_subs, d7_views, _ = get_diff(7)
d30_subs, d30_views, _ = get_diff(30)
d180_subs, d180_views, _ = get_diff(180)

# ==============================================================================
# 🔮 ADVANCED MATH: Линейная регрессия + Взвешенная скользящая средняя
# ==============================================================================
def get_next_milestone(current_val, is_subs=True):
    if is_subs:
        if current_val < 2000: return 2000
        elif current_val < 10000: return (current_val // 1000 + 1) * 1000
        else: return (current_val // 10000 + 1) * 10000
    else:
        if current_val < 1000000: return (current_val // 100000 + 1) * 100000
        elif current_val < 10000000: return (current_val // 500000 + 1) * 500000
        else: return (current_val // 1000000 + 1) * 1000000

def advanced_predict(current_val, metric_key, is_subs=True):
    target = get_next_milestone(current_val, is_subs)
    
    sorted_dates = sorted(db.keys())
    recent_dates = sorted_dates[-30:] # Анализируем до 30 последних дней
    
    if len(recent_dates) < 3:
        return target, "Сбор данных... ⏳ (нужно больше дней)"
        
    start_date = datetime.strptime(recent_dates[0], '%Y-%m-%d')
    data_points = []
    
    for d_str in recent_dates:
        d_obj = datetime.strptime(d_str, '%Y-%m-%d')
        day_idx = (d_obj - start_date).days
        val = db[d_str][metric_key]
        data_points.append((day_idx, val))
        
    # Математика: Метод наименьших квадратов (Линейная регрессия)
    n = len(data_points)
    sum_x = sum(x for x, y in data_points)
    sum_y = sum(y for x, y in data_points)
    sum_xy = sum(x * y for x, y in data_points)
    sum_x2 = sum(x * x for x, y in data_points)
    
    denominator = (n * sum_x2 - sum_x ** 2)
    slope_lr = (n * sum_xy - sum_x * sum_y) / denominator if denominator != 0 else 0
    
    # Свежий импульс (последние 7 дней)
    recent_diff = db[recent_dates[-1]][metric_key] - db[recent_dates[-min(7, n)]][metric_key]
    days_passed = (datetime.strptime(recent_dates[-1], '%Y-%m-%d') - datetime.strptime(recent_dates[-min(7, n)], '%Y-%m-%d')).days
    slope_recent = recent_diff / days_passed if days_passed > 0 else 0

    # Формируем итоговую скорость роста в день (60% тренд + 40% свежий импульс)
    if slope_lr > 0 and slope_recent > 0:
        final_speed = (slope_lr * 0.6) + (slope_recent * 0.4)
    else:
        final_speed = slope_lr if slope_lr > 0 else slope_recent
        
    if final_speed <= 0.1:
        return target, "Рост пока остановился 💤"
        
    # Рассчитываем дату
    days_left = (target - current_val) / final_speed
    est_date = today_obj + timedelta(days=int(days_left))
    
    months = ["Янв", "Фев", "Марта", "Апр", "Мая", "Июня", "Июля", "Авг", "Сент", "Окт", "Нояб", "Дек"]
    month_name = months[est_date.month - 1]
    
    return target, f"~{est_date.day} {month_name} {est_date.year} (через {int(days_left)} дн.)"

target_subs, pred_subs = advanced_predict(subs, 'subs', True)
target_views, pred_views = advanced_predict(views, 'views', False)

# 3. Формируем текст
stats_text = f"""
> 🔴 **YouTube: [@dihantxd](https://youtube.com/@dihantxd)**
> 📈 **Подписчики:** {subs:,} *(За неделю: {format_diff(d7_subs)} | За месяц: {format_diff(d30_subs)} | За полгода: {format_diff(d180_subs)})*
> 🎯 *Прогноз {target_subs:,}:* **{pred_subs}**
> 
> 👁️ **Просмотры:** {views:,} *(За неделю: {format_diff(d7_views)} | За месяц: {format_diff(d30_views)} | За полгода: {format_diff(d180_views)})*
> 🎯 *Прогноз {target_views:,}:* **{pred_views}**
""".replace(',', ' ')

# 4. Записываем в README
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
