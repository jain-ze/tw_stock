#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import ssl
import datetime
import time
import csv
from PIL import Image, ImageDraw, ImageFont

# Set output directories
OUTPUT_DIR = "/home/jrh/桌面/JRH20260720"
ARTIFACT_DIR = "/home/jrh/.gemini/antigravity/brain/cd19aaa8-bb4f-4103-ab8f-aec64f1c458f"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# Font configurations
FONT_BOLD_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REG_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# Custom Sector Dictionary mapping code to sector name
SECTOR_MAP = {
    "2330": "半導體 / 晶圓代工",
    "2327": "被動元件",
    "2454": "半導體 / IC設計",
    "2408": "半導體 / 記憶體",
    "2303": "半導體 / 晶圓代工",
    "1303": "塑膠塑化 / 塑膠原料",
    "0050": "指數型 / ETF",
    "3037": "電子 / ABF載板",
    "8046": "電子 / ABF載板",
    "4958": "電子 / PCB軟板",
    "2308": "電子 / 電源與綠能",
    "2344": "半導體 / 記憶體",
    "6182": "上櫃 / 矽晶圓",
    "3481": "光電 / 面板製造",
    "2317": "代工 / 鴻海集團AI",
    "3231": "電腦 / AI伺服器",
    "3711": "半導體 / 封測龍頭",
    "6274": "上櫃 / CCL銅箔基板",
    "2383": "電子 / CCL銅箔基板",
    "00631L": "槓桿型 / ETF"
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

dates = ['20260723', '20260722', '20260721', '20260720', '20260717']

stocks = {}

print("Fetching TWSE and TPEx market data for the last 5 trading days...")

for d in dates:
    print(f"-> Processing date: {d}")
    
    # 1. Fetch TWSE (上市)
    url_twse = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d}&type=ALLBUT0999&response=json"
    try:
        req = urllib.request.Request(url_twse, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            t8 = None
            for t in data.get('tables', []):
                if t.get('title') and '每日收盤行情' in t.get('title'):
                    t8 = t
                    break
            if not t8 and len(data.get('tables', [])) > 8:
                t8 = data['tables'][8]
            
            if t8 and t8.get('data'):
                for row in t8['data']:
                    code = row[0].strip()
                    name = row[1].strip()
                    try:
                        volume = int(row[2].replace(',', ''))
                        value = int(row[4].replace(',', ''))
                        close_str = row[8].replace(',', '')
                        close = float(close_str) if (close_str != '--' and close_str != '---') else 0.0
                    except Exception:
                        continue
                    
                    if code not in stocks:
                        stocks[code] = {
                            'code': code,
                            'name': name,
                            'market': '上市',
                            'total_value': 0,
                            'total_volume': 0,
                            'daily_values': {},
                            'daily_closes': {}
                        }
                    stocks[code]['total_value'] += value
                    stocks[code]['total_volume'] += volume
                    stocks[code]['daily_values'][d] = value
                    stocks[code]['daily_closes'][d] = close
    except Exception as e:
        print(f"   [!] TWSE error on {d}: {e}")
        
    # 2. Fetch TPEx (上櫃)
    y = int(d[:4]) - 1911
    m = d[4:6]
    day = d[6:8]
    tpex_d = f"{y}/{m}/{day}"
    url_tpex = f"https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d={tpex_d}"
    try:
        req = urllib.request.Request(url_tpex, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            t0 = data.get('tables', [{}])[0]
            if t0 and t0.get('data'):
                for row in t0['data']:
                    code = row[0].strip()
                    name = row[1].strip()
                    try:
                        close_str = row[2].replace(',', '')
                        close = float(close_str) if (close_str != '--' and close_str != '---') else 0.0
                        volume = int(row[8].replace(',', ''))
                        value = int(row[9].replace(',', ''))
                    except Exception:
                        continue
                    
                    if code not in stocks:
                        stocks[code] = {
                            'code': code,
                            'name': name,
                            'market': '上櫃',
                            'total_value': 0,
                            'total_volume': 0,
                            'daily_values': {},
                            'daily_closes': {}
                        }
                    stocks[code]['total_value'] += value
                    stocks[code]['total_volume'] += volume
                    stocks[code]['daily_values'][d] = value
                    stocks[code]['daily_closes'][d] = close
    except Exception as e:
        print(f"   [!] TPEx error on {tpex_d}: {e}")

    time.sleep(0.3)

# Sort by total value descending
ranked = sorted(stocks.values(), key=lambda x: x['total_value'], reverse=True)[:20]

# Structure final record list
final_records = []
for idx, item in enumerate(ranked, 1):
    c = item['code']
    total_val_yi = item['total_value'] / 1e8
    avg_val_yi = total_val_yi / 5
    total_vol_zhang = item['total_volume'] // 1000
    
    latest_close = item['daily_closes'].get('20260723', 0.0)
    first_close = item['daily_closes'].get('20260717', 0.0)
    change_val = latest_close - first_close
    change_pct = (change_val / first_close * 100) if first_close > 0 else 0.0
    
    sector = SECTOR_MAP.get(c, "一般產業")
    
    daily_vals = [item['daily_values'].get(d, 0) / 1e8 for d in reversed(dates)] # chronologically 7/17 -> 7/23
    daily_closes = [item['daily_closes'].get(d, 0.0) for d in reversed(dates)]
    
    rec = {
        'rank': idx,
        'code': c,
        'name': item['name'],
        'market': item['market'],
        'sector': sector,
        'total_value_yi': round(total_val_yi, 2),
        'avg_value_yi': round(avg_val_yi, 2),
        'total_volume_zhang': total_vol_zhang,
        'latest_close': latest_close,
        'first_close': first_close,
        'change_val': round(change_val, 2),
        'change_pct': round(change_pct, 2),
        'daily_values_yi': [round(v, 2) for v in daily_vals],
        'daily_closes': daily_closes
    }
    final_records.append(rec)

# Export to CSV
csv_path = os.path.join(OUTPUT_DIR, "taiwan_stock_top20_trading_value_5days.csv")
with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow([
        '名次', '股票代號', '股票名稱', '市場', '產業分類', 
        '近5日總成交額(億元)', '日均成交額(億元)', '近5日總成交量(張)', 
        '最新收盤價(元)', '期初收盤價(元)', '5日漲跌價', '5日漲跌幅(%)'
    ])
    for r in final_records:
        writer.writerow([
            r['rank'], r['code'], r['name'], r['market'], r['sector'],
            r['total_value_yi'], r['avg_value_yi'], r['total_volume_zhang'],
            r['latest_close'], r['first_close'], r['change_val'], f"{r['change_pct']:+.2f}%"
        ])
print(f"Saved CSV to {csv_path}")

# ==================== CARD 1 RENDERING (Top 20 Overview) ====================
def draw_card1_overview(records, out_path):
    W, H = 1200, 1600
    img = Image.new('RGB', (W, H), '#0D1117')
    draw = ImageDraw.Draw(img)
    
    f_title = get_font(FONT_BOLD_PATH, 42)
    f_subtitle = get_font(FONT_REG_PATH, 22)
    f_header = get_font(FONT_BOLD_PATH, 20)
    f_text_bold = get_font(FONT_BOLD_PATH, 20)
    f_text = get_font(FONT_REG_PATH, 19)
    f_subtext = get_font(FONT_REG_PATH, 16)
    f_badge = get_font(FONT_BOLD_PATH, 15)
    
    # Header Banner
    draw.rectangle([(0, 0), (W, 140)], fill='#161B22')
    draw.line([(0, 140), (W, 140)], fill='#30363D', width=2)
    
    # Title & Subtitle
    draw.text((40, 28), "台股近5日成交金額排行榜 TOP 20", font=f_title, fill='#58A6FF')
    draw.text((40, 85), "資料區間：2026/07/17 ~ 2026/07/23  |  涵蓋上市 (TWSE) 與上櫃 (TPEx)", font=f_subtitle, fill='#8B949E')
    
    # Summary Pills (Top Right)
    total_20_val = sum(r['total_value_yi'] for r in records)
    draw.rectangle([(840, 30), (1160, 110)], fill='#21262D', outline='#30363D', width=1)
    draw.text((860, 42), "Top 20 總成交額", font=f_subtext, fill='#8B949E')
    draw.text((860, 68), f"{total_20_val:,.1f} 億元", font=f_text_bold, fill='#F0F6FC')
    
    # Table Column Headers
    y_start = 160
    draw.rectangle([(40, y_start), (W-40, y_start+45)], fill='#21262D')
    
    headers_config = [
        ("名次", 60),
        ("代號 / 名稱", 140),
        ("市場/產業", 360),
        ("5日總成交額", 570),
        ("日均成交額", 750),
        ("最新價", 910),
        ("5日漲跌幅", 1040)
    ]
    for htext, hx in headers_config:
        draw.text((hx, y_start+10), htext, font=f_header, fill='#8B949E')
        
    y = y_start + 55
    row_h = 66
    
    max_val = records[0]['total_value_yi']
    
    for r in records:
        bg_color = '#161B22' if r['rank'] % 2 == 1 else '#0D1117'
        draw.rectangle([(40, y), (W-40, y+row_h-4)], fill=bg_color)
        
        # Rank Badge
        rank_bg = '#FFD700' if r['rank'] == 1 else ('#C0C0C0' if r['rank'] == 2 else ('#CD7F32' if r['rank'] == 3 else '#30363D'))
        rank_fg = '#000000' if r['rank'] <= 3 else '#F0F6FC'
        draw.rectangle([(50, y+15), (90, y+45)], fill=rank_bg)
        draw.text((60 if r['rank']<10 else 54, y+18), str(r['rank']), font=f_badge, fill=rank_fg)
        
        # Stock Name & Code
        draw.text((140, y+12), r['code'], font=f_text_bold, fill='#58A6FF')
        draw.text((140, y+36), r['name'], font=f_text, fill='#F0F6FC')
        
        # Market & Sector Badges
        mkt_bg = '#1F6FEB' if r['market'] == '上市' else '#D29922'
        draw.rectangle([(360, y+12), (410, y+34)], fill=mkt_bg)
        draw.text((366, y+14), r['market'], font=f_badge, fill='#FFFFFF')
        draw.text((360, y+38), r['sector'], font=f_subtext, fill='#8B949E')
        
        # Total Value & Bar
        draw.text((570, y+14), f"{r['total_value_yi']:,.1f} 億", font=f_text_bold, fill='#F0F6FC')
        # Mini bar chart background
        bar_w = int((r['total_value_yi'] / max_val) * 140)
        draw.rectangle([(570, y+42), (570+bar_w, y+48)], fill='#238636')
        
        # Daily Avg Value
        draw.text((750, y+20), f"{r['avg_value_yi']:,.1f} 億", font=f_text, fill='#C9D1D9')
        
        # Latest Close Price
        draw.text((910, y+20), f"${r['latest_close']:,.2f}", font=f_text_bold, fill='#F0F6FC')
        
        # 5-day Change Pct
        chg = r['change_pct']
        chg_str = f"{chg:+.2f}%"
        chg_color = '#F85149' if chg > 0 else ('#3FB950' if chg < 0 else '#8B949E')
        draw.rectangle([(1040, y+16), (1140, y+46)], fill=chg_color)
        draw.text((1048, y+20), chg_str, font=f_badge, fill='#FFFFFF')
        
        y += row_h
        
    # Footer
    draw.line([(40, H-40), (W-40, H-40)], fill='#30363D', width=1)
    draw.text((40, H-30), "註：台股市場採紅漲綠跌。成交金額依據臺灣證券交易所 (TWSE) 與證券櫃檯買賣中心 (TPEx) 官方公開數據統計。", font=f_subtext, fill='#8B949E')
    
    img.save(out_path)
    print(f"Saved Card 1 to {out_path}")

# ==================== CARD 2 RENDERING (Top 1-10 Deep Dive) ====================
def draw_card2_top10(records, out_path):
    W, H = 1200, 1500
    img = Image.new('RGB', (W, H), '#0D1117')
    draw = ImageDraw.Draw(img)
    
    f_title = get_font(FONT_BOLD_PATH, 40)
    f_subtitle = get_font(FONT_REG_PATH, 22)
    f_name = get_font(FONT_BOLD_PATH, 24)
    f_text_bold = get_font(FONT_BOLD_PATH, 20)
    f_text = get_font(FONT_REG_PATH, 18)
    f_subtext = get_font(FONT_REG_PATH, 15)
    f_badge = get_font(FONT_BOLD_PATH, 16)
    
    # Header Banner
    draw.rectangle([(0, 0), (W, 130)], fill='#161B22')
    draw.text((40, 25), "台股成交金額 Top 1 ~ 10 爆量巨頭深度剖析", font=f_title, fill='#3FB950')
    draw.text((40, 80), "權值領航與千億級吸金大戶  |  5日成交數據與每日量能走勢", font=f_subtitle, fill='#8B949E')
    
    y = 150
    card_h = 120
    
    for r in records[:10]:
        draw.rectangle([(40, y), (W-40, y+card_h-10)], fill='#161B22', outline='#30363D', width=1)
        
        # Rank pill
        rank_bg = '#FFD700' if r['rank'] == 1 else ('#C0C0C0' if r['rank'] == 2 else ('#CD7F32' if r['rank'] == 3 else '#21262D'))
        rank_fg = '#000000' if r['rank'] <= 3 else '#58A6FF'
        draw.rectangle([(55, y+15), (105, y+55)], fill=rank_bg)
        draw.text((70 if r['rank']<10 else 64, y+22), f"#{r['rank']}", font=f_badge, fill=rank_fg)
        
        # Stock Title
        draw.text((120, y+16), f"{r['code']} {r['name']}", font=f_name, fill='#F0F6FC')
        draw.text((120, y+52), f"{r['market']} | {r['sector']}", font=f_subtext, fill='#8B949E')
        
        # Price & Change
        draw.text((360, y+16), f"${r['latest_close']:,.2f}", font=f_name, fill='#F0F6FC')
        chg = r['change_pct']
        chg_color = '#F85149' if chg > 0 else ('#3FB950' if chg < 0 else '#8B949E')
        draw.text((360, y+52), f"5日漲跌 {chg:+.2f}%", font=f_text_bold, fill=chg_color)
        
        # 5-day Total Value & Daily Avg
        draw.text((560, y+16), f"5日成交金額", font=f_subtext, fill='#8B949E')
        draw.text((560, y+42), f"{r['total_value_yi']:,.1f} 億元", font=f_text_bold, fill='#F0F6FC')
        draw.text((560, y+70), f"日均: {r['avg_value_yi']:,.1f} 億", font=f_subtext, fill='#C9D1D9')
        
        # Mini Daily Bar Chart (7/17 -> 7/23)
        chart_x = 760
        chart_y = y + 20
        max_d_val = max(r['daily_values_yi']) if max(r['daily_values_yi']) > 0 else 1
        day_labels = ['7/17', '7/20', '7/21', '7/22', '7/23']
        
        draw.text((chart_x, y+10), "5日每日成交額走勢(億):", font=f_subtext, fill='#8B949E')
        for i, dv in enumerate(r['daily_values_yi']):
            bx = chart_x + i * 75
            bh = int((dv / max_d_val) * 45)
            # bar
            draw.rectangle([(bx, chart_y+65-bh), (bx+40, chart_y+65)], fill='#238636' if i==4 else '#1F6FEB')
            # label
            draw.text((bx+2, chart_y+70), day_labels[i], font=f_subtext, fill='#8B949E')
            draw.text((bx, chart_y+65-bh-16), f"{int(dv)}", font=f_subtext, fill='#C9D1D9')
            
        y += card_h
        
    img.save(out_path)
    print(f"Saved Card 2 to {out_path}")

# ==================== CARD 3 RENDERING (Top 11-20 Movers & OTC) ====================
def draw_card3_top11_20(records, out_path):
    W, H = 1200, 1500
    img = Image.new('RGB', (W, H), '#0D1117')
    draw = ImageDraw.Draw(img)
    
    f_title = get_font(FONT_BOLD_PATH, 40)
    f_subtitle = get_font(FONT_REG_PATH, 22)
    f_name = get_font(FONT_BOLD_PATH, 24)
    f_text_bold = get_font(FONT_BOLD_PATH, 20)
    f_text = get_font(FONT_REG_PATH, 18)
    f_subtext = get_font(FONT_REG_PATH, 15)
    f_badge = get_font(FONT_BOLD_PATH, 16)
    
    # Header Banner
    draw.rectangle([(0, 0), (W, 130)], fill='#161B22')
    draw.text((40, 25), "台股成交金額 Top 11 ~ 20 爆量潛力股與上櫃黑馬", font=f_title, fill='#A371F7')
    draw.text((40, 80), "中大型強勢飆股與櫃買熱門焦點  |  詳細交易數據與量能走勢", font=f_subtitle, fill='#8B949E')
    
    y = 150
    card_h = 120
    
    for r in records[10:20]:
        draw.rectangle([(40, y), (W-40, y+card_h-10)], fill='#161B22', outline='#30363D', width=1)
        
        # Rank pill
        draw.rectangle([(55, y+15), (105, y+55)], fill='#21262D')
        draw.text((62, y+22), f"#{r['rank']}", font=f_badge, fill='#A371F7')
        
        # Stock Title
        draw.text((120, y+16), f"{r['code']} {r['name']}", font=f_name, fill='#F0F6FC')
        mkt_clr = '#D29922' if r['market'] == '上櫃' else '#1F6FEB'
        draw.text((120, y+52), f"[{r['market']}] {r['sector']}", font=f_subtext, fill=mkt_clr)
        
        # Price & Change
        draw.text((360, y+16), f"${r['latest_close']:,.2f}", font=f_name, fill='#F0F6FC')
        chg = r['change_pct']
        chg_color = '#F85149' if chg > 0 else ('#3FB950' if chg < 0 else '#8B949E')
        draw.text((360, y+52), f"5日漲跌 {chg:+.2f}%", font=f_text_bold, fill=chg_color)
        
        # 5-day Total Value & Daily Avg
        draw.text((560, y+16), f"5日成交金額", font=f_subtext, fill='#8B949E')
        draw.text((560, y+42), f"{r['total_value_yi']:,.1f} 億元", font=f_text_bold, fill='#F0F6FC')
        draw.text((560, y+70), f"日均: {r['avg_value_yi']:,.1f} 億", font=f_subtext, fill='#C9D1D9')
        
        # Mini Daily Bar Chart
        chart_x = 760
        chart_y = y + 20
        max_d_val = max(r['daily_values_yi']) if max(r['daily_values_yi']) > 0 else 1
        day_labels = ['7/17', '7/20', '7/21', '7/22', '7/23']
        
        draw.text((chart_x, y+10), "5日每日成交額走勢(億):", font=f_subtext, fill='#8B949E')
        for i, dv in enumerate(r['daily_values_yi']):
            bx = chart_x + i * 75
            bh = int((dv / max_d_val) * 45)
            # bar
            draw.rectangle([(bx, chart_y+65-bh), (bx+40, chart_y+65)], fill='#8957E5' if i==4 else '#388BFD')
            # label
            draw.text((bx+2, chart_y+70), day_labels[i], font=f_subtext, fill='#8B949E')
            draw.text((bx, chart_y+65-bh-16), f"{int(dv)}", font=f_subtext, fill='#C9D1D9')
            
        y += card_h
        
    img.save(out_path)
    print(f"Saved Card 3 to {out_path}")

# Run Card Generators
card1_path = os.path.join(OUTPUT_DIR, "taiwan_stock_top20_card1_overview.png")
card2_path = os.path.join(OUTPUT_DIR, "taiwan_stock_top20_card2_top10_analysis.png")
card3_path = os.path.join(OUTPUT_DIR, "taiwan_stock_top11_20_card3_analysis.png")

draw_card1_overview(final_records, card1_path)
draw_card2_top10(final_records, card2_path)
draw_card3_top11_20(final_records, card3_path)

# Copy cards to artifact directory for embedding
import shutil
shutil.copy(card1_path, os.path.join(ARTIFACT_DIR, "taiwan_stock_top20_card1_overview.png"))
shutil.copy(card2_path, os.path.join(ARTIFACT_DIR, "taiwan_stock_top20_card2_top10_analysis.png"))
shutil.copy(card3_path, os.path.join(ARTIFACT_DIR, "taiwan_stock_top11_20_card3_analysis.png"))
shutil.copy(csv_path, os.path.join(ARTIFACT_DIR, "taiwan_stock_top20_trading_value_5days.csv"))

print("Finished generation and artifact copies successfully!")
