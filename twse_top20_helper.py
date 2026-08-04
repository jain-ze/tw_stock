#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import ssl
import datetime
import time
import csv
import base64
import argparse
import glob
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

DEFAULT_OUTDIR = "/home/jrh/桌面/JRH20260720/近5日台股成交金額TOP20深度分析"
FONT_BOLD_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REG_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
RCLONE_BIN = "/home/jrh/.local/bin/rclone"
GITHUB_REMOTE_URL = "https://github.com/jain-ze/tw_stock.git"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_rounded_rect(draw_obj, rect, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = rect
    draw_obj.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

SECTOR_MAP = {
    "2330": "半導體 / 晶圓代工",
    "2327": "被動元件",
    "2454": "半導體 / IC設計",
    "2408": "半導體 / 記憶體",
    "2303": "半導體 / 晶圓代工",
    "1303": "塑膠塑化 / 原料",
    "0050": "指數型 / ETF",
    "3037": "電子 / ABF載板",
    "8046": "電子 / ABF載板",
    "4958": "電子 / PCB軟板",
    "2308": "電子 / 電源綠能",
    "2344": "半導體 / 記憶體",
    "6182": "上櫃 / 矽晶圓",
    "3481": "光電 / 面板製造",
    "2317": "代工 / AI伺服器",
    "3231": "電腦 / AI伺服器",
    "3711": "半導體 / 封測龍頭",
    "6274": "上櫃 / CCL銅箔基板",
    "2383": "電子 / CCL銅箔基板",
    "00631L": "槓桿型 / ETF"
}

def fetch_json(url, use_ssl_ctx=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        ctx = ssl._create_unverified_context() if use_ssl_ctx else None
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return None

def fetch_valid_trading_days(n=5, start_date=None):
    """Dynamically fetch the most recent N valid trading days starting from start_date (default today) backward"""
    ctx = ssl._create_unverified_context()
    headers = {'User-Agent': 'Mozilla/5.0'}
    valid_dates = []
    
    if start_date:
        if isinstance(start_date, str):
            curr = datetime.datetime.strptime(start_date.replace('-', ''), "%Y%m%d").date()
        else:
            curr = start_date
    else:
        curr = datetime.date.today()
        
    attempts = 0

    while len(valid_dates) < n and attempts < 25:
        d_str = curr.strftime('%Y%m%d')
        url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d_str}&type=ALLBUT0999&response=json"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('stat') == 'OK' and (data.get('tables') or data.get('data')):
                    valid_dates.append(d_str)
        except Exception:
            pass
        curr -= datetime.timedelta(days=1)
        attempts += 1
        time.sleep(0.15)

    print(f"[+] Recent {len(valid_dates)} valid trading days (Start: {start_date or 'today'}): {valid_dates}")
    return valid_dates

def fetch_market_indices(dates):
    unique_yms = sorted(list(set(d[:6] for d in dates if len(d) >= 6)), reverse=True)
    twse_map = {}
    tpex_map = {}

    for ym in unique_yms:
        url_twse = f"https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date={ym}01&response=json"
        res_twse = fetch_json(url_twse)
        if res_twse and res_twse.get("data"):
            for r in res_twse["data"]:
                try:
                    parts = r[0].split("/")
                    y = int(parts[0]) + 1911
                    m = int(parts[1])
                    d = int(parts[2])
                    d_str = f"{y:04d}{m:02d}{d:02d}"
                    amount = int(r[2].replace(",", ""))
                    idx_val = float(r[4].replace(",", ""))
                    chg_val = float(r[5].replace(",", ""))
                    denom = idx_val - chg_val
                    twse_map[d_str] = {
                        "amount_yi": round(amount / 1e8, 2),
                        "index": idx_val,
                        "change": chg_val,
                        "change_pct": round((chg_val / denom) * 100, 2) if denom != 0 else 0
                    }
                except Exception:
                    pass

        try:
            roc_y = int(ym[:4]) - 1911
            m = int(ym[4:])
            url_tpex = f"https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_index/st41_result.php?l=zh-tw&d={roc_y}/{m:02d}"
            res_tpex = fetch_json(url_tpex, use_ssl_ctx=True)
            if res_tpex and res_tpex.get("tables") and res_tpex["tables"][0].get("data"):
                for r in res_tpex["tables"][0]["data"]:
                    try:
                        parts = r[0].split("/")
                        y = int(parts[0]) + 1911
                        m_val = int(parts[1])
                        d_val = int(parts[2])
                        d_str = f"{y:04d}{m_val:02d}{d_val:02d}"
                        amount = int(r[2].replace(",", "")) * 1000
                        idx_val = float(r[4]) if isinstance(r[4], (int, float)) else float(r[4].replace(",", ""))
                        chg_val = float(r[5]) if isinstance(r[5], (int, float)) else float(r[5].replace(",", ""))
                        denom = idx_val - chg_val
                        tpex_map[d_str] = {
                            "amount_yi": round(amount / 1e8, 2),
                            "index": idx_val,
                            "change": chg_val,
                            "change_pct": round((chg_val / denom) * 100, 2) if denom != 0 else 0
                        }
                    except Exception:
                        pass
        except Exception:
            pass

    market_history = []
    for d in dates:
        tw = twse_map.get(d, {"amount_yi": 0, "index": 0, "change": 0, "change_pct": 0})
        tp = tpex_map.get(d, {"amount_yi": 0, "index": 0, "change": 0, "change_pct": 0})
        market_history.append({
            "date": d,
            "date_short": f"{d[4:6]}/{d[6:]}",
            "twse": tw,
            "tpex": tp
        })
    return market_history

def fetch_bfi82u_data(dates):
    bfi_history = []
    for d in dates:
        url = f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?dayDate={d}&response=json"
        res = fetch_json(url)
        item = {
            "date": d,
            "date_short": f"{d[4:6]}/{d[6:]}",
            "foreign_diff_yi": 0.0,
            "trust_diff_yi": 0.0,
            "dealer_diff_yi": 0.0,
            "total_diff_yi": 0.0,
        }
        if res and res.get("stat") == "OK" and res.get("data"):
            foreign, trust, dealer_self, dealer_hedge, total = 0, 0, 0, 0, 0
            for r in res.get("data", []):
                name = r[0]
                try:
                    diff_v = int(r[3].replace(",", ""))
                except Exception:
                    diff_v = 0
                
                if "外資及陸資(不含外資自營" in name or ("外資及陸資" in name and "外資自營" not in name):
                    foreign = diff_v
                elif "投信" in name:
                    trust = diff_v
                elif "自營商(自行" in name:
                    dealer_self = diff_v
                elif "自營商(避險" in name:
                    dealer_hedge = diff_v
                elif "合計" in name:
                    total = diff_v
            
            dealer_tot = dealer_self + dealer_hedge
            item["foreign_diff_yi"] = round(foreign / 1e8, 2)
            item["trust_diff_yi"] = round(trust / 1e8, 2)
            item["dealer_diff_yi"] = round(dealer_tot / 1e8, 2)
            item["total_diff_yi"] = round(total / 1e8, 2)
        
        bfi_history.append(item)
        time.sleep(0.15)

    return bfi_history

def fetch_margin_data(dates):
    margin_history = []
    for d in dates:
        url = f"https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date={d}&selectType=MS&response=json"
        res = fetch_json(url)
        item = {
            "date": d,
            "date_short": f"{d[4:6]}/{d[6:]}",
            "is_updated": False,
            "margin_curr_yi": None,
            "margin_diff_yi": None,
            "short_curr_zhang": None,
            "short_diff_zhang": None
        }
        if res and res.get("stat") == "OK" and res.get("tables"):
            try:
                t0_data = res["tables"][0].get("data", [])
                if len(t0_data) >= 3 and t0_data[2][5] != '--' and t0_data[2][5] != '---':
                    m_prev = int(t0_data[2][4].replace(",", "")) * 1000
                    m_curr = int(t0_data[2][5].replace(",", "")) * 1000
                    s_prev = int(t0_data[1][4].replace(",", ""))
                    s_curr = int(t0_data[1][5].replace(",", ""))
                    
                    item["is_updated"] = True
                    item["margin_curr_yi"] = round(m_curr / 1e8, 2)
                    item["margin_diff_yi"] = round((m_curr - m_prev) / 1e8, 2)
                    item["short_curr_zhang"] = s_curr
                    item["short_diff_zhang"] = s_curr - s_prev
            except Exception:
                pass

        margin_history.append(item)
        time.sleep(0.15)

    return margin_history

def fetch_top20_stocks_data(dates):
    ctx = ssl._create_unverified_context()
    headers = {'User-Agent': 'Mozilla/5.0'}
    stocks = {}

    for d in dates:
        # TWSE
        url_twse = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d}&type=ALLBUT0999&response=json"
        try:
            req = urllib.request.Request(url_twse, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
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
                            stocks[code] = {'code': code, 'name': name, 'market': '上市', 'total_value': 0, 'total_volume': 0, 'daily_values': {}, 'daily_closes': {}, 'daily_volumes': {}}
                        stocks[code]['total_value'] += value
                        stocks[code]['total_volume'] += volume
                        stocks[code]['daily_values'][d] = value
                        stocks[code]['daily_closes'][d] = close
                        stocks[code]['daily_volumes'][d] = volume
        except Exception as e:
            print(f"[!] TWSE stock error on {d}: {e}")

        # TPEx
        y = int(d[:4]) - 1911
        m = d[4:6]
        day = d[6:8]
        tpex_d = f"{y}/{m}/{day}"
        url_tpex = f"https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d={tpex_d}"
        try:
            req = urllib.request.Request(url_tpex, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
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
                            stocks[code] = {'code': code, 'name': name, 'market': '上櫃', 'total_value': 0, 'total_volume': 0, 'daily_values': {}, 'daily_closes': {}, 'daily_volumes': {}}
                        stocks[code]['total_value'] += value
                        stocks[code]['total_volume'] += volume
                        stocks[code]['daily_values'][d] = value
                        stocks[code]['daily_closes'][d] = close
                        stocks[code]['daily_volumes'][d] = volume
        except Exception as e:
            print(f"[!] TPEx stock error on {tpex_d}: {e}")

        time.sleep(0.2)

    ranked = sorted(stocks.values(), key=lambda x: x['total_value'], reverse=True)[:20]
    latest_date_str = dates[0]
    prev_date_str = dates[1] if len(dates) > 1 else dates[0]
    first_date_str = dates[-1]

    final_records = []
    for idx, item in enumerate(ranked, 1):
        c = item['code']
        total_val_yi = item['total_value'] / 1e8
        avg_val_yi = total_val_yi / 5
        total_vol_zhang = item['total_volume'] // 1000
        
        latest_close = item['daily_closes'].get(latest_date_str, 0.0)
        prev_close = item['daily_closes'].get(prev_date_str, 0.0) if prev_date_str in item['daily_closes'] else latest_close
        today_change_val = latest_close - prev_close
        today_change_pct = (today_change_val / prev_close * 100) if prev_close > 0 else 0.0

        first_close = item['daily_closes'].get(first_date_str, 0.0)
        change_val = latest_close - first_close
        change_pct = (change_val / first_close * 100) if first_close > 0 else 0.0
        
        sector = SECTOR_MAP.get(c, "一般產業")
        
        daily_vals = [item['daily_values'].get(d, 0) / 1e8 for d in reversed(dates)]
        daily_closes = [item['daily_closes'].get(d, 0.0) for d in reversed(dates)]
        daily_vols = [item['daily_volumes'].get(d, 0) // 1000 for d in reversed(dates)]
        day_labels = [f"{d[4:6]}/{d[6:]}" for d in reversed(dates)]
        
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
            'prev_close': prev_close,
            'today_change_val': round(today_change_val, 2),
            'today_change_pct': round(today_change_pct, 2),
            'first_close': first_close,
            'change_val': round(change_val, 2),
            'change_pct': round(change_pct, 2),
            'daily_dates': day_labels,
            'daily_values_yi': [round(v, 2) for v in daily_vals],
            'daily_closes': daily_closes,
            'daily_volumes_zhang': daily_vols
        }
        final_records.append(rec)

    return final_records

def render_all_6_cards(records, dates, market_history, bfi_history, margin_history, outdir):
    today_date = dates[0]
    date_formatted = f"{today_date[:4]}-{today_date[4:6]}-{today_date[6:]}"
    
    f_title = get_font(FONT_BOLD_PATH, 40)
    f_subtitle = get_font(FONT_REG_PATH, 22)
    f_bold = get_font(FONT_BOLD_PATH, 20)
    f_text = get_font(FONT_REG_PATH, 19)
    f_subtext = get_font(FONT_REG_PATH, 16)
    f_badge = get_font(FONT_BOLD_PATH, 15)

    # CARD 1: Market Indices Card
    img1 = Image.new('RGB', (1200, 1650), '#0D1117')
    d1 = ImageDraw.Draw(img1)
    d1.rectangle([(0, 0), (1200, 130)], fill='#161B22')
    d1.text((40, 25), f"台股大盤與櫃買指數/成交量值 ({date_formatted})", font=f_title, fill='#58A6FF')
    d1.text((40, 80), "集中市場加權指數 vs 上櫃櫃買指數 5日雙指數折線圖與成交額", font=f_subtitle, fill='#8B949E')
    
    y = 150
    m_latest = market_history[0] if market_history else {}
    tw_idx = m_latest.get('twse', {})
    tp_idx = m_latest.get('tpex', {})
    
    d1.rectangle([(40, y), (570, y+140)], fill='#161B22', outline='#30363D', width=1)
    d1.text((60, y+20), "加權指數 (TWSE TAIEX)", font=f_bold, fill='#8B949E')
    d1.text((60, y+55), f"{tw_idx.get('index', 0):,.2f}", font=get_font(FONT_BOLD_PATH, 32), fill='#F0F6FC')
    tw_chg = tw_idx.get('change_pct', 0)
    tw_clr = '#F85149' if tw_chg > 0 else ('#3FB950' if tw_chg < 0 else '#8B949E')
    d1.text((60, y+100), f"今日漲跌: {tw_chg:+.2f}% ({tw_idx.get('change',0):+.2f} 點)", font=f_bold, fill=tw_clr)
    d1.text((360, y+55), "大盤成交金額", font=f_subtext, fill='#8B949E')
    d1.text((360, y+85), f"{tw_idx.get('amount_yi', 0):,.1f} 億元", font=f_bold, fill='#58A6FF')
    
    d1.rectangle([(630, y), (1160, y+140)], fill='#161B22', outline='#30363D', width=1)
    d1.text((650, y+20), "櫃買指數 (TPEx OTC)", font=f_bold, fill='#8B949E')
    d1.text((650, y+55), f"{tp_idx.get('index', 0):,.2f}", font=get_font(FONT_BOLD_PATH, 32), fill='#F0F6FC')
    tp_chg = tp_idx.get('change_pct', 0)
    tp_clr = '#F85149' if tp_chg > 0 else ('#3FB950' if tp_chg < 0 else '#8B949E')
    d1.text((650, y+100), f"今日漲跌: {tp_chg:+.2f}% ({tp_idx.get('change',0):+.2f} 點)", font=f_bold, fill=tp_clr)
    d1.text((950, y+55), "櫃買成交金額", font=f_subtext, fill='#8B949E')
    d1.text((950, y+85), f"{tp_idx.get('amount_yi', 0):,.1f} 億元", font=f_bold, fill='#D29922')

    # Line Chart Area
    y_chart = y + 160
    d1.text((40, y_chart), "📈 近 5 個交易日上市加權指數與櫃買指數雙線趨勢圖", font=f_bold, fill='#F0F6FC')
    y_chart += 35
    d1.rectangle([(40, y_chart), (1160, y_chart+320)], fill='#161B22', outline='#30363D', width=1)
    
    history_chrono = list(reversed(market_history))
    tw_indices = [h['twse']['index'] for h in history_chrono]
    tp_indices = [h['tpex']['index'] for h in history_chrono]
    
    min_tw, max_tw = min(tw_indices), max(tw_indices)
    range_tw = (max_tw - min_tw) if max_tw > min_tw else 1
    
    min_tp, max_tp = min(tp_indices), max(tp_indices)
    range_tp = (max_tp - min_tp) if max_tp > min_tp else 1

    x_step = 1000 // (len(history_chrono) - 1 or 1)
    
    for i in range(len(history_chrono) - 1):
        x1 = 90 + i * x_step
        y1 = y_chart + 260 - int(((tw_indices[i] - min_tw) / range_tw) * 200)
        x2 = 90 + (i + 1) * x_step
        y2 = y_chart + 260 - int(((tw_indices[i+1] - min_tw) / range_tw) * 200)
        d1.line([(x1, y1), (x2, y2)], fill='#58A6FF', width=4)
        
    for i, h in enumerate(history_chrono):
        x = 90 + i * x_step
        y_pos = y_chart + 260 - int(((tw_indices[i] - min_tw) / range_tw) * 200)
        d1.ellipse([(x-6, y_pos-6), (x+6, y_pos+6)], fill='#58A6FF', outline='#FFFFFF', width=2)
        d1.text((x-20, y_pos-24), f"{tw_indices[i]:,.0f}", font=f_subtext, fill='#58A6FF')
        d1.text((x-16, y_chart+285), h['date_short'], font=f_subtext, fill='#8B949E')

    for i in range(len(history_chrono) - 1):
        x1 = 90 + i * x_step
        y1 = y_chart + 260 - int(((tp_indices[i] - min_tp) / range_tp) * 200)
        x2 = 90 + (i + 1) * x_step
        y2 = y_chart + 260 - int(((tp_indices[i+1] - min_tp) / range_tp) * 200)
        d1.line([(x1, y1), (x2, y2)], fill='#D29922', width=3)
        
    for i, h in enumerate(history_chrono):
        x = 90 + i * x_step
        y_pos = y_chart + 260 - int(((tp_indices[i] - min_tp) / range_tp) * 200)
        d1.ellipse([(x-5, y_pos-5), (x+5, y_pos+5)], fill='#D29922', outline='#FFFFFF', width=1)
        d1.text((x-15, y_pos+10), f"{tp_indices[i]:,.1f}", font=f_subtext, fill='#D29922')

    d1.rectangle([(80, y_chart+15), (380, y_chart+45)], fill='#21262D')
    d1.line([(95, y_chart+30), (125, y_chart+30)], fill='#58A6FF', width=4)
    d1.text((135, y_chart+20), "加權指數 (TWSE)", font=f_subtext, fill='#58A6FF')
    d1.line([(245, y_chart+30), (275, y_chart+30)], fill='#D29922', width=3)
    d1.text((285, y_chart+20), "櫃買指數 (TPEx)", font=f_subtext, fill='#D29922')

    y_tbl = y_chart + 340
    d1.text((40, y_tbl), "📋 近 5 個交易日大盤與櫃買行情明細表", font=f_bold, fill='#F0F6FC')
    y_tbl += 35
    d1.rectangle([(40, y_tbl), (1160, y_tbl+40)], fill='#21262D')
    d1.text((60, y_tbl+10), "日期", font=f_bold, fill='#8B949E')
    d1.text((180, y_tbl+10), "加權指數", font=f_bold, fill='#8B949E')
    d1.text((360, y_tbl+10), "大盤漲跌%", font=f_bold, fill='#8B949E')
    d1.text((540, y_tbl+10), "大盤成交額", font=f_bold, fill='#8B949E')
    d1.text((720, y_tbl+10), "櫃買指數", font=f_bold, fill='#8B949E')
    d1.text((900, y_tbl+10), "櫃買漲跌%", font=f_bold, fill='#8B949E')
    d1.text((1040, y_tbl+10), "櫃買成交額", font=f_bold, fill='#8B949E')

    y_row = y_tbl + 45
    for m in market_history:
        d1.rectangle([(40, y_row), (1160, y_row+55)], fill='#161B22', outline='#30363D')
        d1.text((60, y_row+15), m['date_short'], font=f_bold, fill='#58A6FF')
        d1.text((180, y_row+15), f"{m['twse']['index']:,.2f}", font=f_text, fill='#F0F6FC')
        tw_c = m['twse']['change_pct']
        d1.text((360, y_row+15), f"{tw_c:+.2f}%", font=f_bold, fill='#F85149' if tw_c>0 else '#3FB950')
        d1.text((540, y_row+15), f"{m['twse']['amount_yi']:,.1f} 億", font=f_text, fill='#C9D1D9')
        d1.text((720, y_row+15), f"{m['tpex']['index']:,.2f}", font=f_text, fill='#F0F6FC')
        tp_c = m['tpex']['change_pct']
        d1.text((900, y_row+15), f"{tp_c:+.2f}%", font=f_bold, fill='#F85149' if tp_c>0 else '#3FB950')
        d1.text((1040, y_row+15), f"{m['tpex']['amount_yi']:,.1f} 億", font=f_text, fill='#C9D1D9')
        y_row += 62

    c1_path = os.path.join(outdir, f"taiwan_stock_card1_market_index_{date_formatted}.png")
    img1.save(c1_path)

    # CARD 2: BFI82U Three Major Institutional Investors Card
    img2 = Image.new('RGB', (1200, 1650), '#0D1117')
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([(0, 0), (1200, 130)], fill='#161B22')
    d2.text((40, 25), f"三大法人買賣金額與籌碼統計 ({date_formatted})", font=f_title, fill='#3FB950')
    d2.text((40, 80), "外資、投信與自營商買賣超金額動態與近5日籌碼獨立柱狀圖", font=f_subtitle, fill='#8B949E')
    
    b_latest = bfi_history[0] if bfi_history else {}
    y_bfi = 150
    cards_bfi = [
        ("外資及陸資買賣超", b_latest.get('foreign_diff_yi', 0), '#58A6FF'),
        ("投信買賣超", b_latest.get('trust_diff_yi', 0), '#BC8CFF'),
        ("自營商合計買賣超", b_latest.get('dealer_diff_yi', 0), '#D29922'),
        ("三大法人合計買賣超", b_latest.get('total_diff_yi', 0), '#3FB950')
    ]
    for i, (title_b, val_b, clr_b) in enumerate(cards_bfi):
        bx = 40 + (i % 2) * 580
        by = y_bfi + (i // 2) * 110
        d2.rectangle([(bx, by), (bx+540, by+95)], fill='#161B22', outline='#30363D')
        d2.text((bx+20, by+15), title_b, font=f_bold, fill='#8B949E')
        v_clr = '#F85149' if val_b > 0 else ('#3FB950' if val_b < 0 else '#8B949E')
        d2.text((bx+20, by+48), f"{val_b:+.2f} 億元", font=get_font(FONT_BOLD_PATH, 28), fill=v_clr)

    y_bchart = y_bfi + 240
    d2.text((40, y_bchart), "📊 近 5 個交易日三大法人與合計獨立買賣超柱狀圖 (億元)", font=f_bold, fill='#F0F6FC')
    y_bchart += 35
    d2.rectangle([(40, y_bchart), (1160, y_bchart+340)], fill='#161B22', outline='#30363D', width=1)
    
    d2.rectangle([(60, y_bchart+15), (780, y_bchart+45)], fill='#21262D')
    d2.rectangle([(75, y_bchart+23), (95, y_bchart+37)], fill='#58A6FF')
    d2.text((105, y_bchart+20), "外資", font=f_subtext, fill='#8B949E')
    d2.rectangle([(230, y_bchart+23), (250, y_bchart+37)], fill='#BC8CFF')
    d2.text((260, y_bchart+20), "投信", font=f_subtext, fill='#8B949E')
    d2.rectangle([(380, y_bchart+23), (400, y_bchart+37)], fill='#D29922')
    d2.text((410, y_bchart+20), "自營商", font=f_subtext, fill='#8B949E')
    d2.rectangle([(540, y_bchart+23), (560, y_bchart+37)], fill='#3FB950')
    d2.text((570, y_bchart+20), "三大法人合計", font=f_subtext, fill='#8B949E')

    history_chrono_b = list(reversed(bfi_history))
    all_bfi_vals = []
    for h in history_chrono_b:
        all_bfi_vals.extend([abs(h['foreign_diff_yi']), abs(h['trust_diff_yi']), abs(h['dealer_diff_yi']), abs(h['total_diff_yi'])])
    max_bfi_val = max(all_bfi_vals) or 1

    chart_mid_y = y_bchart + 190
    d2.line([(60, chart_mid_y), (1140, chart_mid_y)], fill='#30363D', width=2)

    group_w = 1040 // len(history_chrono_b)
    bw = 24
    for idx, item in enumerate(history_chrono_b):
        center_x = 120 + idx * group_w
        series = [
            (item['foreign_diff_yi'], '#58A6FF'),
            (item['trust_diff_yi'], '#BC8CFF'),
            (item['dealer_diff_yi'], '#D29922'),
            (item['total_diff_yi'], '#3FB950' if item['total_diff_yi']>=0 else '#F85149')
        ]
        for s_idx, (val, clr) in enumerate(series):
            bx = center_x + (s_idx - 1.5) * (bw + 6)
            bh = int((abs(val) / max_bfi_val) * 110)
            if bh < 3: bh = 3
            if val >= 0:
                d2.rectangle([(bx, chart_mid_y - bh), (bx + bw, chart_mid_y)], fill=clr)
            else:
                d2.rectangle([(bx, chart_mid_y), (bx + bw, chart_mid_y + bh)], fill=clr)
        d2.text((center_x - 18, y_bchart + 305), item['date_short'], font=f_subtext, fill='#8B949E')

    y_btbl = y_bchart + 395
    d2.text((40, y_btbl), "📋 近 5 個交易日三大法人買賣超數據表 (億元)", font=f_bold, fill='#F0F6FC')
    y_btbl += 35
    d2.rectangle([(40, y_btbl), (1160, y_btbl+40)], fill='#21262D')
    d2.text((60, y_btbl+10), "日期", font=f_bold, fill='#8B949E')
    d2.text((220, y_btbl+10), "外資買賣超", font=f_bold, fill='#8B949E')
    d2.text((460, y_btbl+10), "投信買賣超", font=f_bold, fill='#8B949E')
    d2.text((700, y_btbl+10), "自營商買賣超", font=f_bold, fill='#8B949E')
    d2.text((940, y_btbl+10), "三大法人合計", font=f_bold, fill='#8B949E')

    y_brow = y_btbl + 45
    for b in bfi_history:
        d2.rectangle([(40, y_brow), (1160, y_brow+55)], fill='#161B22', outline='#30363D')
        d2.text((60, y_brow+15), b['date_short'], font=f_bold, fill='#58A6FF')
        
        f_c = '#F85149' if b['foreign_diff_yi']>0 else '#3FB950'
        d2.text((220, y_brow+15), f"{b['foreign_diff_yi']:+.2f} 億", font=f_bold, fill=f_c)
        
        t_c = '#F85149' if b['trust_diff_yi']>0 else '#3FB950'
        d2.text((460, y_brow+15), f"{b['trust_diff_yi']:+.2f} 億", font=f_bold, fill=t_c)
        
        d_c = '#F85149' if b['dealer_diff_yi']>0 else '#3FB950'
        d2.text((700, y_brow+15), f"{b['dealer_diff_yi']:+.2f} 億", font=f_bold, fill=d_c)
        
        tot_c = '#F85149' if b['total_diff_yi']>0 else '#3FB950'
        d2.text((940, y_brow+15), f"{b['total_diff_yi']:+.2f} 億", font=f_bold, fill=tot_c)
        y_brow += 62

    c2_path = os.path.join(outdir, f"taiwan_stock_card2_bfi82u_{date_formatted}.png")
    img2.save(c2_path)

    # CARD 3: MI_MARGN Margin Trading Card
    img3 = Image.new('RGB', (1200, 1650), '#0D1117')
    d3 = ImageDraw.Draw(img3)
    d3.rectangle([(0, 0), (1200, 130)], fill='#161B22')
    d3.text((40, 25), f"信用交易融資融券餘額統計 ({date_formatted})", font=f_title, fill='#D29922')
    d3.text((40, 80), "散戶與內資籌碼指標  |  融資金額餘額增減與融券張數變動圖表", font=f_subtitle, fill='#8B949E')
    
    m_latest_margn = margin_history[0] if margin_history else {}
    y_mrg = 150
    d3.rectangle([(40, y_mrg), (570, y_mrg+140)], fill='#161B22', outline='#30363D')
    d3.text((60, y_mrg+20), "融資金額餘額 (Margin Balance)", font=f_bold, fill='#8B949E')
    
    if m_latest_margn.get('is_updated'):
        m_curr_str = f"{m_latest_margn.get('margin_curr_yi'):,.2f} 億"
        m_diff = m_latest_margn.get('margin_diff_yi', 0)
        m_clr = '#F85149' if m_diff > 0 else ('#3FB950' if m_diff < 0 else '#8B949E')
        m_diff_str = f"今日增減: {m_diff:+.2f} 億元"
    else:
        m_curr_str = "尚未更新"
        m_clr = '#8B949E'
        m_diff_str = "證交所晚間尚未公佈"

    d3.text((60, y_mrg+55), m_curr_str, font=get_font(FONT_BOLD_PATH, 32), fill='#F0F6FC' if m_latest_margn.get('is_updated') else '#D29922')
    d3.text((60, y_mrg+100), m_diff_str, font=f_bold, fill=m_clr)

    d3.rectangle([(630, y_mrg), (1160, y_mrg+140)], fill='#161B22', outline='#30363D')
    d3.text((650, y_mrg+20), "融券張數餘額 (Short Balance)", font=f_bold, fill='#8B949E')
    
    if m_latest_margn.get('is_updated'):
        s_curr_str = f"{m_latest_margn.get('short_curr_zhang'):,} 張"
        s_diff = m_latest_margn.get('short_diff_zhang', 0)
        s_clr = '#F85149' if s_diff > 0 else ('#3FB950' if s_diff < 0 else '#8B949E')
        s_diff_str = f"今日增減: {s_diff:+,} 張"
    else:
        s_curr_str = "尚未更新"
        s_clr = '#8B949E'
        s_diff_str = "證交所晚間尚未公佈"

    d3.text((650, y_mrg+55), s_curr_str, font=get_font(FONT_BOLD_PATH, 32), fill='#F0F6FC' if m_latest_margn.get('is_updated') else '#D29922')
    d3.text((650, y_mrg+100), s_diff_str, font=f_bold, fill=s_clr)

    y_mchart = y_mrg + 160
    d3.text((40, y_mchart), "📊 近 5 個交易日融資金額增減變動柱狀圖 (億元)", font=f_bold, fill='#F0F6FC')
    y_mchart += 35
    d3.rectangle([(40, y_mchart), (1160, y_mchart+320)], fill='#161B22', outline='#30363D', width=1)

    history_chrono_m = list(reversed(margin_history))
    m_diffs = [h['margin_diff_yi'] for h in history_chrono_m if h.get('is_updated') and h['margin_diff_yi'] is not None]
    max_m_diff = max([abs(v) for v in m_diffs]) if m_diffs else 1

    chart_mid_m = y_mchart + 160
    d3.line([(60, chart_mid_m), (1140, chart_mid_m)], fill='#30363D', width=2)

    group_wm = 1040 // len(history_chrono_m)
    for idx, item in enumerate(history_chrono_m):
        center_x = 130 + idx * group_wm
        if item.get('is_updated') and item['margin_diff_yi'] is not None:
            val = item['margin_diff_yi']
            bh = int((abs(val) / max_m_diff) * 100)
            if bh < 4: bh = 4
            clr = '#F85149' if val >= 0 else '#3FB950'
            if val >= 0:
                d3.rectangle([(center_x - 30, chart_mid_m - bh), (center_x + 30, chart_mid_m)], fill=clr)
            else:
                d3.rectangle([(center_x - 30, chart_mid_m), (center_x + 30, chart_mid_m + bh)], fill=clr)
            d3.text((center_x - 20, (chart_mid_m - bh - 20) if val >= 0 else (chart_mid_m + bh + 4)), f"{val:+.1f}億", font=f_subtext, fill=clr)
        else:
            d3.text((center_x - 30, chart_mid_m - 10), "尚未更新", font=f_subtext, fill='#D29922')
        d3.text((center_x - 18, y_mchart + 285), item['date_short'], font=f_subtext, fill='#8B949E')

    y_mtbl = y_mchart + 375
    d3.text((40, y_mtbl), "📋 近 5 個交易日信用交易融資融券變動表", font=f_bold, fill='#F0F6FC')
    y_mtbl += 35
    d3.rectangle([(40, y_mtbl), (1160, y_mtbl+40)], fill='#21262D')
    d3.text((60, y_mtbl+10), "日期", font=f_bold, fill='#8B949E')
    d3.text((220, y_mtbl+10), "融資餘額 (億元)", font=f_bold, fill='#8B949E')
    d3.text((460, y_mtbl+10), "融資今日增減", font=f_bold, fill='#8B949E')
    d3.text((700, y_mtbl+10), "融券餘額 (張)", font=f_bold, fill='#8B949E')
    d3.text((940, y_mtbl+10), "融券今日增減", font=f_bold, fill='#8B949E')

    y_mrow = y_mtbl + 45
    for mg in margin_history:
        d3.rectangle([(40, y_mrow), (1160, y_mrow+55)], fill='#161B22', outline='#30363D')
        d3.text((60, y_mrow+15), mg['date_short'], font=f_bold, fill='#58A6FF')
        
        if mg.get('is_updated'):
            d3.text((220, y_mrow+15), f"{mg['margin_curr_yi']:,.2f} 億", font=f_text, fill='#F0F6FC')
            md_c = '#F85149' if mg['margin_diff_yi']>0 else '#3FB950'
            d3.text((460, y_mrow+15), f"{mg['margin_diff_yi']:+.2f} 億", font=f_bold, fill=md_c)
            d3.text((700, y_mrow+15), f"{mg['short_curr_zhang']:,} 張", font=f_text, fill='#F0F6FC')
            sd_c = '#F85149' if mg['short_diff_zhang']>0 else '#3FB950'
            d3.text((940, y_mrow+15), f"{mg['short_diff_zhang']:+,} 張", font=f_bold, fill=sd_c)
        else:
            d3.text((220, y_mrow+15), "尚未更新", font=f_text, fill='#D29922')
            d3.text((460, y_mrow+15), "尚未更新", font=f_bold, fill='#D29922')
            d3.text((700, y_mrow+15), "尚未更新", font=f_text, fill='#D29922')
            d3.text((940, y_mrow+15), "尚未更新", font=f_bold, fill='#D29922')
        y_mrow += 62

    c3_path = os.path.join(outdir, f"taiwan_stock_card3_margin_{date_formatted}.png")
    img3.save(c3_path)

    # CARD 4: TOP 20 Overview Card
    img4 = Image.new('RGB', (1200, 1600), '#0D1117')
    d4 = ImageDraw.Draw(img4)
    d4.rectangle([(0, 0), (1200, 140)], fill='#161B22')
    d4.text((40, 28), f"台股近5日成交金額 TOP 20 ({date_formatted})", font=f_title, fill='#58A6FF')
    d4.text((40, 85), f"統計區間：{dates[-1]} ~ {dates[0]}  |  涵蓋上市 (TWSE) 與上櫃 (TPEx)", font=f_subtitle, fill='#8B949E')
    
    total_20_val = sum(r['total_value_yi'] for r in records)
    d4.rectangle([(840, 30), (1160, 110)], fill='#21262D', outline='#30363D')
    d4.text((860, 42), "Top 20 總成交額", font=f_subtext, fill='#8B949E')
    d4.text((860, 68), f"{total_20_val:,.1f} 億元", font=f_bold, fill='#F0F6FC')
    
    y_start = 160
    d4.rectangle([(40, y_start), (1160, y_start+45)], fill='#21262D')
    headers_config = [("名次", 60), ("代號 / 名稱", 140), ("市場/產業", 360), ("5日總成交額", 570), ("日均成交額", 750), ("最新價", 910), ("5日漲跌幅", 1040)]
    for htext, hx in headers_config:
        d4.text((hx, y_start+10), htext, font=f_bold, fill='#8B949E')
        
    y = y_start + 55
    row_h = 66
    max_val = records[0]['total_value_yi'] if records else 1
    
    for r in records:
        bg_color = '#161B22' if r['rank'] % 2 == 1 else '#0D1117'
        d4.rectangle([(40, y), (1160, y+row_h-4)], fill=bg_color)
        rank_bg = '#FFD700' if r['rank'] == 1 else ('#C0C0C0' if r['rank'] == 2 else ('#CD7F32' if r['rank'] == 3 else '#30363D'))
        rank_fg = '#000000' if r['rank'] <= 3 else '#F0F6FC'
        d4.rectangle([(50, y+15), (90, y+45)], fill=rank_bg)
        d4.text((60 if r['rank']<10 else 54, y+18), str(r['rank']), font=f_badge, fill=rank_fg)
        
        d4.text((140, y+12), r['code'], font=f_bold, fill='#58A6FF')
        d4.text((140, y+36), r['name'], font=f_text, fill='#F0F6FC')
        
        mkt_bg = '#1F6FEB' if r['market'] == '上市' else '#D29922'
        d4.rectangle([(360, y+12), (410, y+34)], fill=mkt_bg)
        d4.text((366, y+14), r['market'], font=f_badge, fill='#FFFFFF')
        d4.text((360, y+38), r['sector'], font=f_subtext, fill='#8B949E')
        
        d4.text((570, y+14), f"{r['total_value_yi']:,.1f} 億", font=f_bold, fill='#F0F6FC')
        bar_w = int((r['total_value_yi'] / max_val) * 140)
        d4.rectangle([(570, y+42), (570+bar_w, y+48)], fill='#238636')
        
        d4.text((750, y+20), f"{r['avg_value_yi']:,.1f} 億", font=f_text, fill='#C9D1D9')
        d4.text((910, y+20), f"${r['latest_close']:,.2f}", font=f_bold, fill='#F0F6FC')
        
        chg = r['change_pct']
        chg_color = '#F85149' if chg > 0 else ('#3FB950' if chg < 0 else '#8B949E')
        d4.rectangle([(1040, y+16), (1140, y+46)], fill=chg_color)
        d4.text((1048, y+20), f"{chg:+.2f}%", font=f_badge, fill='#FFFFFF')
        y += row_h

    c4_path = os.path.join(outdir, f"taiwan_stock_card4_top20_overview_{date_formatted}.png")
    img4.save(c4_path)

    # CARD 5: Top 1-10 Giants Card
    img5 = Image.new('RGB', (1200, 1500), '#0D1117')
    d5 = ImageDraw.Draw(img5)
    d5.rectangle([(0, 0), (1200, 130)], fill='#161B22')
    d5.text((40, 25), f"台股 Top 1 ~ 10 爆量巨頭深度剖析 ({date_formatted})", font=get_font(FONT_BOLD_PATH, 40), fill='#3FB950')
    d5.text((40, 80), "權值領航與千億級吸金大戶  |  5日成交數據與每日量能走勢", font=f_subtitle, fill='#8B949E')
    
    y = 150
    for r in records[:10]:
        d5.rectangle([(40, y), (1160, y+110)], fill='#161B22', outline='#30363D', width=1)
        rank_bg = '#FFD700' if r['rank'] == 1 else ('#C0C0C0' if r['rank'] == 2 else ('#CD7F32' if r['rank'] == 3 else '#21262D'))
        rank_fg = '#000000' if r['rank'] <= 3 else '#58A6FF'
        d5.rectangle([(55, y+15), (105, y+55)], fill=rank_bg)
        d5.text((70 if r['rank']<10 else 64, y+22), f"#{r['rank']}", font=f_badge, fill=rank_fg)
        d5.text((120, y+16), f"{r['code']} {r['name']}", font=get_font(FONT_BOLD_PATH, 24), fill='#F0F6FC')
        d5.text((120, y+52), f"{r['market']} | {r['sector']}", font=f_subtext, fill='#8B949E')
        d5.text((360, y+16), f"${r['latest_close']:,.2f}", font=get_font(FONT_BOLD_PATH, 24), fill='#F0F6FC')
        chg_color = '#F85149' if r['change_pct'] > 0 else ('#3FB950' if r['change_pct'] < 0 else '#8B949E')
        d5.text((360, y+52), f"5日漲跌 {r['change_pct']:+.2f}%", font=f_bold, fill=chg_color)
        d5.text((560, y+16), "5日成交金額", font=f_subtext, fill='#8B949E')
        d5.text((560, y+42), f"{r['total_value_yi']:,.1f} 億元", font=f_bold, fill='#F0F6FC')
        d5.text((560, y+70), f"日均: {r['avg_value_yi']:,.1f} 億", font=f_subtext, fill='#C9D1D9')
        
        chart_x, chart_y = 760, y + 20
        max_d_val = max(r['daily_values_yi']) if max(r['daily_values_yi']) > 0 else 1
        day_labels = [f"{d[4:6]}/{d[6:]}" for d in reversed(dates)]
        d5.text((chart_x, y+10), "5日每日成交額走勢(億):", font=f_subtext, fill='#8B949E')
        for i, dv in enumerate(r['daily_values_yi']):
            bx = chart_x + i * 75
            bh = int((dv / max_d_val) * 45)
            d5.rectangle([(bx, chart_y+65-bh), (bx+40, chart_y+65)], fill='#238636' if i==4 else '#1F6FEB')
            d5.text((bx+2, chart_y+70), day_labels[i], font=f_subtext, fill='#8B949E')
            d5.text((bx, chart_y+65-bh-16), f"{int(dv)}", font=f_subtext, fill='#C9D1D9')
        y += 120

    c5_path = os.path.join(outdir, f"taiwan_stock_card5_top1_10_{date_formatted}.png")
    img5.save(c5_path)

    # CARD 6: Top 11-20 Movers & OTC Card
    img6 = Image.new('RGB', (1200, 1500), '#0D1117')
    d6 = ImageDraw.Draw(img6)
    d6.rectangle([(0, 0), (1200, 130)], fill='#161B22')
    d6.text((40, 25), f"台股 Top 11 ~ 20 爆量潛力股與上櫃黑馬 ({date_formatted})", font=get_font(FONT_BOLD_PATH, 40), fill='#A371F7')
    d6.text((40, 80), "中大型強勢飆股與櫃買熱門焦點  |  詳細交易數據與量能走勢", font=f_subtitle, fill='#8B949E')
    
    y = 150
    for r in records[10:20]:
        d6.rectangle([(40, y), (1160, y+110)], fill='#161B22', outline='#30363D', width=1)
        d6.rectangle([(55, y+15), (105, y+55)], fill='#21262D')
        d6.text((62, y+22), f"#{r['rank']}", font=f_badge, fill='#A371F7')
        d6.text((120, y+16), f"{r['code']} {r['name']}", font=get_font(FONT_BOLD_PATH, 24), fill='#F0F6FC')
        mkt_clr = '#D29922' if r['market'] == '上櫃' else '#1F6FEB'
        d6.text((120, y+52), f"[{r['market']}] {r['sector']}", font=f_subtext, fill=mkt_clr)
        d6.text((360, y+16), f"${r['latest_close']:,.2f}", font=get_font(FONT_BOLD_PATH, 24), fill='#F0F6FC')
        chg_color = '#F85149' if r['change_pct'] > 0 else ('#3FB950' if r['change_pct'] < 0 else '#8B949E')
        d6.text((360, y+52), f"5日漲跌 {r['change_pct']:+.2f}%", font=f_bold, fill=chg_color)
        d6.text((560, y+16), "5日成交金額", font=f_subtext, fill='#8B949E')
        d6.text((560, y+42), f"{r['total_value_yi']:,.1f} 億元", font=f_bold, fill='#F0F6FC')
        d6.text((560, y+70), f"日均: {r['avg_value_yi']:,.1f} 億", font=f_subtext, fill='#C9D1D9')
        
        chart_x, chart_y = 760, y + 20
        max_d_val = max(r['daily_values_yi']) if max(r['daily_values_yi']) > 0 else 1
        day_labels = [f"{d[4:6]}/{d[6:]}" for d in reversed(dates)]
        d6.text((chart_x, y+10), "5日每日成交額走勢(億):", font=f_subtext, fill='#8B949E')
        for i, dv in enumerate(r['daily_values_yi']):
            bx = chart_x + i * 75
            bh = int((dv / max_d_val) * 45)
            d6.rectangle([(bx, chart_y+65-bh), (bx+40, chart_y+65)], fill='#8957E5' if i==4 else '#388BFD')
            d6.text((bx+2, chart_y+70), day_labels[i], font=f_subtext, fill='#8B949E')
            d6.text((bx, chart_y+65-bh-16), f"{int(dv)}", font=f_subtext, fill='#C9D1D9')
        y += 120

    c6_path = os.path.join(outdir, f"taiwan_stock_card6_top11_20_{date_formatted}.png")
    img6.save(c6_path)

    return c1_path, c2_path, c3_path, c4_path, c5_path, c6_path

def build_comprehensive_daily_html(records, dates, market_history, bfi_history, margin_history, outdir, card_paths):
    today_date = dates[0]
    today_formatted = f"{today_date[:4]}-{today_date[4:6]}-{today_date[6:]}"
    date_range_str = f"{dates[-1][:4]}/{dates[-1][4:6]}/{dates[-1][6:]} ～ {dates[0][:4]}/{dates[0][4:6]}/{dates[0][6:]}"

    def to_b64(p):
        if os.path.exists(p):
            with open(p, 'rb') as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        return ""

    b64_cards = [to_b64(p) for p in card_paths]

    # Export CSVs
    csv_path = os.path.join(outdir, f"taiwan_stock_top20_trading_value_5days_{today_formatted}.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['名次', '代號', '名稱', '市場', '產業', '5日總成交額(億)', '日均成交額(億)', '5日成交量(張)', '最新價', '5日漲跌幅(%)'])
        for r in records:
            writer.writerow([r['rank'], r['code'], r['name'], r['market'], r['sector'], r['total_value_yi'], r['avg_value_yi'], r['total_volume_zhang'], r['latest_close'], f"{r['change_pct']:+.2f}%"])

    m_latest = market_history[0] if market_history else {}
    tw_idx = m_latest.get('twse', {})
    tp_idx = m_latest.get('tpex', {})
    
    b_latest = bfi_history[0] if bfi_history else {}
    m_latest_margn = margin_history[0] if margin_history else {}
    
    total_20_val = sum(r['total_value_yi'] for r in records)
    top_gainer = max(records, key=lambda x: x['change_pct']) if records else {'name':'--', 'change_pct':0}
    top_gainers_list = sorted(records, key=lambda x: x['change_pct'], reverse=True)[:5]

    stocks_detail_json = json.dumps({r['code']: r for r in records}, ensure_ascii=False)

    if m_latest_margn.get('is_updated'):
        m_header_val = f"{m_latest_margn.get('margin_curr_yi',0):,.1f} 億 ({m_latest_margn.get('margin_diff_yi',0):+.2f}億)"
        m_header_clr = 'var(--amber)'
    else:
        m_header_val = "尚未更新 (證交所晚間公佈)"
        m_header_clr = 'var(--muted)'

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台股盤後大數據與籌碼動向觀測站 ({today_formatted})</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg-dark:#0d1117; --bg-card:#161b22; --bg-hover:#1f242d; --border:#30363d; --text:#f0f6fc; --muted:#8b949e; --blue:#58a6ff; --green:#3fb950; --red:#f85149; --amber:#d29922; --purple:#bc8cff; }}
        * {{ box-sizing:border-box; margin:0; padding:0; }}
        body {{ font-family:'Noto Sans TC','Inter',sans-serif; background-color:var(--bg-dark); color:var(--text); line-height:1.6; padding-bottom:60px; }}
        .nav-header {{ display:flex; justify-content:space-between; align-items:center; max-width:1200px; margin:0 auto; padding:15px 20px 0; }}
        .btn-home {{ display:inline-flex; align-items:center; gap:6px; background:#21262d; color:var(--blue); border:1px solid var(--border); font-weight:700; font-size:14px; padding:8px 16px; border-radius:8px; text-decoration:none; transition:all 0.2s; }}
        .btn-home:hover {{ background:var(--blue); color:#000; border-color:var(--blue); transform:translateY(-1px); }}
        .hero {{ background:linear-gradient(135deg, #161b22 0%, #0d1117 100%); border-bottom:1px solid var(--border); padding:30px 20px 30px; text-align:center; position:relative; }}
        .hero::before {{ content:''; position:absolute; top:0; left:0; right:0; height:4px; background:linear-gradient(90deg, #58a6ff, #bc8cff, #3fb950); }}
        .badge {{ display:inline-block; background:rgba(88,166,255,0.15); color:var(--blue); padding:6px 16px; border-radius:20px; font-size:14px; font-weight:700; margin-bottom:12px; border:1px solid rgba(88,166,255,0.3); }}
        h1 {{ font-size:32px; font-weight:900; margin-bottom:10px; }}
        .sub {{ color:var(--muted); font-size:15px; margin-bottom:25px; }}
        .metrics {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(220px,1fr)); gap:16px; max-width:1200px; margin:0 auto; }}
        .m-card {{ background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:18px 20px; text-align:left; }}
        .m-label {{ font-size:13px; color:var(--muted); }}
        .m-val {{ font-size:22px; font-weight:800; margin-top:4px; }}
        .container {{ max-width:1200px; margin:30px auto; padding:0 20px; }}
        
        .view-nav {{ display:flex; gap:12px; margin-bottom:25px; border-bottom:2px solid var(--border); padding-bottom:12px; flex-wrap:wrap; }}
        .view-tab-btn {{ background:#161b22; border:1px solid var(--border); color:var(--muted); padding:12px 24px; border-radius:10px; font-size:16px; font-weight:800; cursor:pointer; transition:all 0.2s; }}
        .view-tab-btn:hover {{ background:var(--bg-hover); color:var(--text); }}
        .view-tab-btn.active {{ background:var(--blue); color:#000; border-color:var(--blue); box-shadow:0 4px 12px rgba(88,166,255,0.3); }}

        .s-header {{ border-left:4px solid var(--blue); padding-left:12px; margin-bottom:20px; font-size:22px; font-weight:800; }}
        .card-tabs {{ display:flex; gap:10px; margin-bottom:20px; border-bottom:1px solid var(--border); padding-bottom:10px; flex-wrap:wrap; }}
        .card-tab {{ background:var(--bg-card); border:1px solid var(--border); color:var(--muted); padding:10px 18px; border-radius:8px; cursor:pointer; font-weight:700; font-size:14px; }}
        .card-tab.active {{ background:var(--blue); color:#000; border-color:var(--blue); }}
        .card-view {{ text-align:center; background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:20px; margin-bottom:40px; }}
        .card-view img {{ max-width:100%; height:auto; border-radius:8px; }}
        .tbl-container {{ overflow-x:auto; background:var(--bg-card); border:1px solid var(--border); border-radius:12px; margin-bottom:40px; }}
        table {{ width:100%; border-collapse:collapse; font-size:14px; text-align:left; }}
        th, td {{ padding:14px 16px; border-bottom:1px solid var(--border); white-space:nowrap; }}
        th {{ background:#161b22; color:var(--muted); }}
        tr.stock-row {{ cursor:pointer; transition:background 0.2s; }}
        tr.stock-row:hover {{ background:var(--bg-hover); }}
        .r-badge {{ display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px; border-radius:6px; font-weight:800; font-size:13px; }}
        .r-1 {{ background:#ffd700; color:#000; }} .r-2 {{ background:#c0c0c0; color:#000; }} .r-3 {{ background:#cd7f32; color:#000; }} .r-o {{ background:#21262d; color:var(--muted); }}
        .m-twse {{ background:rgba(31,111,235,0.2); color:#58a6ff; border:1px solid rgba(31,111,235,0.4); padding:2px 8px; border-radius:4px; font-size:12px; font-weight:700; }}
        .m-tpex {{ background:rgba(210,153,34,0.2); color:#d29922; border:1px solid rgba(210,153,34,0.4); padding:2px 8px; border-radius:4px; font-size:12px; font-weight:700; }}
        .chg {{ padding:4px 10px; border-radius:6px; font-weight:700; font-size:13px; }}
        .chg-up {{ background:rgba(248,81,73,0.2); color:var(--red); border:1px solid rgba(248,81,73,0.4); }}
        .chg-down {{ background:rgba(63,185,80,0.2); color:var(--green); border:1px solid rgba(63,185,80,0.4); }}
        .chg-flat {{ background:rgba(139,148,158,0.2); color:var(--muted); border:1px solid rgba(139,148,158,0.4); }}
        .analysis-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(340px, 1fr)); gap:20px; margin-bottom:40px; }}
        .analysis-card {{ background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:24px; }}
        .analysis-card h3 {{ font-size:18px; color:var(--blue); margin-bottom:12px; display:flex; align-items:center; gap:8px; }}
        .analysis-card p, .analysis-card ul {{ font-size:14px; color:#c9d1d9; }}
        .analysis-card ul {{ padding-left:18px; margin-top:8px; }}
        .analysis-card li {{ margin-bottom:8px; }}
        
        .modal-overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.75); z-index:1000; align-items:center; justify-content:center; padding:20px; backdrop-filter:blur(4px); }}
        .modal-card {{ background:var(--bg-card); border:1px solid var(--border); border-radius:16px; max-width:850px; width:100%; padding:24px; box-shadow:0 20px 50px rgba(0,0,0,0.6); position:relative; max-height:90vh; overflow-y:auto; }}
        .modal-close {{ position:absolute; top:18px; right:20px; background:none; border:none; color:var(--muted); font-size:24px; cursor:pointer; transition:color 0.2s; }}
        .modal-close:hover {{ color:var(--text); }}
        .modal-header {{ display:flex; align-items:center; gap:12px; margin-bottom:16px; border-bottom:1px solid var(--border); padding-bottom:14px; }}
        .modal-title {{ font-size:24px; font-weight:900; }}
        .chart-box {{ background:#0d1117; border:1px solid var(--border); border-radius:12px; padding:16px; margin:20px 0; text-align:center; }}
        .detail-table {{ width:100%; border-collapse:collapse; margin-top:16px; font-size:14px; }}
        .detail-table th, .detail-table td {{ padding:10px 14px; border-bottom:1px solid var(--border); text-align:center; }}
        .detail-table th {{ background:#21262d; color:var(--muted); }}
        footer {{ text-align:center; color:var(--muted); font-size:13px; border-top:1px solid var(--border); padding-top:30px; margin-top:50px; }}
    </style>
</head>
<body>
    <div class="hero">
        <div class="nav-header">
            <a href="index.html" class="btn-home">🏠 回首頁 (Portal)</a>
        </div>
        <div class="badge">台股盤後大數據與籌碼動向觀測站 ({today_formatted})</div>
        <h1>台股盤後大數據與籌碼動向觀測站</h1>
        <p class="sub">統計資料日期：{today_formatted} (最近5交易日：{date_range_str})  |  整合大盤指數、三大法人買賣超、信用交易與 TOP 20 爆量強勢股</p>
        <div class="metrics">
            <div class="m-card">
                <div class="m-label">加權指數 (TAIEX)</div>
                <div class="m-val" style="color:{'var(--red)' if tw_idx.get('change_pct',0)>0 else 'var(--green)'};">{tw_idx.get('index',0):,.2f} ({tw_idx.get('change_pct',0):+.2f}%)</div>
            </div>
            <div class="m-card">
                <div class="m-label">三大法人買賣超</div>
                <div class="m-val" style="color:{'var(--red)' if b_latest.get('total_diff_yi',0)>0 else 'var(--green)'};">{b_latest.get('total_diff_yi',0):+.2f} 億元</div>
            </div>
            <div class="m-card">
                <div class="m-label">融資餘額 (增減)</div>
                <div class="m-val" style="color:{m_header_clr};">{m_header_val}</div>
            </div>
            <div class="m-card">
                <div class="m-label">Top 20 總成交額</div>
                <div class="m-val" style="color:var(--blue);">{total_20_val/10000:.2f} 兆台幣</div>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Main Navigation View Tabs -->
        <div class="view-nav">
            <button id="nav-btn-table" class="view-tab-btn active" onclick="switchMainView('table')">📈 大盤籌碼與 TOP 20 成交金額數據榜單 (獨立頁)</button>
            <button id="nav-btn-cards" class="view-tab-btn" onclick="switchMainView('cards')">🖼️ 6 大視覺化高解析圖卡展示區 (含雙折線與柱狀圖)</button>
        </div>

        <!-- SECTION A: TOP 20 TABLE & INDEPENDENT DETAILED ANALYSIS -->
        <div id="section-table-view">
            <!-- 1. Market Indices & Three Major Institutional Investors Table -->
            <div class="s-header">🏛️ 近 5 日大盤指數、三大法人買賣超與融資融券籌碼統計表</div>
            <div class="tbl-container">
                <table>
                    <thead>
                        <tr>
                            <th>日期</th>
                            <th>加權指數 (大盤)</th>
                            <th>大盤成交額</th>
                            <th>櫃買指數 (TPEx)</th>
                            <th>外資買賣超</th>
                            <th>投信買賣超</th>
                            <th>自營商買賣超</th>
                            <th>三大法人合計</th>
                            <th>融資餘額 (增減)</th>
                        </tr>
                    </thead>
                    <tbody>"""

    for i in range(len(dates)):
        m_item = market_history[i] if i < len(market_history) else {}
        b_item = bfi_history[i] if i < len(bfi_history) else {}
        mg_item = margin_history[i] if i < len(margin_history) else {}
        
        tw = m_item.get('twse', {})
        tp = m_item.get('tpex', {})
        
        tw_c = tw.get('change_pct', 0)
        tw_c_clr = 'var(--red)' if tw_c > 0 else ('var(--green)' if tw_c < 0 else 'var(--muted)')
        
        b_tot = b_item.get('total_diff_yi', 0)
        b_tot_clr = 'var(--red)' if b_tot > 0 else ('var(--green)' if b_tot < 0 else 'var(--muted)')
        
        if mg_item.get('is_updated'):
            mg_diff = mg_item.get('margin_diff_yi', 0)
            mg_diff_clr = 'var(--red)' if mg_diff > 0 else ('var(--green)' if mg_diff < 0 else 'var(--muted)')
            mg_txt = f"{mg_item.get('margin_curr_yi',0):,.1f} 億 (<span style='color:{mg_diff_clr};font-weight:700;'>{mg_diff:+.2f}億</span>)"
        else:
            mg_txt = "<span style='color:var(--amber);font-weight:700;'>尚未更新</span>"

        html += f"""
                        <tr>
                            <td><strong>{dates[i][4:6]}/{dates[i][6:]}</strong></td>
                            <td><strong>{tw.get('index',0):,.2f}</strong> (<span style="color:{tw_c_clr};font-weight:700;">{tw_c:+.2f}%</span>)</td>
                            <td>{tw.get('amount_yi',0):,.1f} 億</td>
                            <td>{tp.get('index',0):,.2f}</td>
                            <td style="color:{'var(--red)' if b_item.get('foreign_diff_yi',0)>0 else 'var(--green)'};">{b_item.get('foreign_diff_yi',0):+.2f} 億</td>
                            <td style="color:{'var(--red)' if b_item.get('trust_diff_yi',0)>0 else 'var(--green)'};">{b_item.get('trust_diff_yi',0):+.2f} 億</td>
                            <td style="color:{'var(--red)' if b_item.get('dealer_diff_yi',0)>0 else 'var(--green)'};">{b_item.get('dealer_diff_yi',0):+.2f} 億</td>
                            <td style="color:{b_tot_clr};font-weight:800;">{b_tot:+.2f} 億</td>
                            <td>{mg_txt}</td>
                        </tr>"""

    html += f"""
                    </tbody>
                </table>
            </div>

            <!-- 2. TOP 20 Stocks Table -->
            <div class="s-header">📈 近 5 日成交金額 TOP 20 獨立榜單 (點擊個股可查看近5日走勢與成交明細)</div>
            <div class="tbl-container">
                <table>
                    <thead>
                        <tr><th>名次</th><th>代號 / 股票名稱</th><th>市場</th><th>產業分類</th><th>5日總成交額(億)</th><th>日均成交額(億)</th><th>5日成交量(張)</th><th>最新價</th><th>當日漲跌 (元/%)</th><th>5日漲跌幅</th><th>走勢明細</th></tr>
                    </thead>
                    <tbody>"""

    for s in records:
        r_cls = f"r-{s['rank']}" if s['rank'] <= 3 else "r-o"
        m_cls = "m-twse" if s['market'] == "上市" else "m-tpex"
        c_cls = "chg-up" if s['change_pct'] > 0 else ("chg-down" if s['change_pct'] < 0 else "chg-flat")
        c_sign = "+" if s['change_pct'] > 0 else ""
        
        today_c_cls = "chg-up" if s['today_change_val'] > 0 else ("chg-down" if s['today_change_val'] < 0 else "chg-flat")
        today_c_sign = "+" if s['today_change_val'] > 0 else ""

        html += f"""
                        <tr class="stock-row" onclick="openStockModal('{s['code']}')">
                            <td><span class="r-badge {r_cls}">{s['rank']}</span></td>
                            <td><strong>{s['code']}</strong> {s['name']}</td>
                            <td><span class="{m_cls}">{s['market']}</span></td>
                            <td style="color:var(--muted);">{s['sector']}</td>
                            <td><strong>{s['total_value_yi']:,.1f} 億</strong></td>
                            <td>{s['avg_value_yi']:,.1f} 億</td>
                            <td>{s['total_volume_zhang']:,} 張</td>
                            <td><strong>${s['latest_close']:,.2f}</strong></td>
                            <td><span class="chg {today_c_cls}">{today_c_sign}${s['today_change_val']:.2f} ({today_c_sign}{s['today_change_pct']:.2f}%)</span></td>
                            <td><span class="chg {c_cls}">{c_sign}{s['change_pct']:.2f}%</span></td>
                            <td><button style="background:var(--blue);color:#000;border:none;padding:4px 10px;border-radius:4px;font-weight:700;cursor:pointer;">📊 走勢圖</button></td>
                        </tr>"""

    gainers_html = "".join([f"<li><strong>{g['code']} {g['name']}</strong>：漲幅 <span style='color:var(--red);font-weight:700;'>+{g['change_pct']:.2f}%</span> (收盤 ${g['latest_close']:,.2f}，5日成交額 {g['total_value_yi']:,.1f} 億)</li>" for g in top_gainers_list])

    html += f"""
                    </tbody>
                </table>
            </div>

            <!-- 3. Comprehensive Market & Capital Analysis -->
            <div class="s-header">🔍 全方位盤後大數據與籌碼趨勢深度剖析</div>
            <div class="analysis-grid">
                <div class="analysis-card">
                    <h3>⚡ 大盤與三大法人籌碼趨勢</h3>
                    <p>今日台股加權指數收在 <strong>{tw_idx.get('index',0):,.2f} 點</strong>，三大法人今日合計買賣超金額為 <strong>{b_latest.get('total_diff_yi',0):+.2f} 億元</strong>：</p>
                    <ul>
                        <li><strong>外資動向</strong>：今日買賣超金額為 <strong style="color:{'var(--red)' if b_latest.get('foreign_diff_yi',0)>0 else 'var(--green)'};">{b_latest.get('foreign_diff_yi',0):+.2f} 億元</strong>。</li>
                        <li><strong>投信動向</strong>：買賣超金額為 <strong style="color:{'var(--red)' if b_latest.get('trust_diff_yi',0)>0 else 'var(--green)'};">{b_latest.get('trust_diff_yi',0):+.2f} 億元</strong>。</li>
                        <li><strong>自營商動向</strong>：合計買賣超金額為 <strong style="color:{'var(--red)' if b_latest.get('dealer_diff_yi',0)>0 else 'var(--green)'};">{b_latest.get('dealer_diff_yi',0):+.2f} 億元</strong>。</li>
                    </ul>
                </div>

                <div class="analysis-card">
                    <h3>💳 信用交易 (融資融券) 變化</h3>
                    <p>市場散戶與內資籌碼浮動情況：</p>
                    <ul>
                        <li><strong>融資金額餘額</strong>：{"<strong>" + f"{m_latest_margn.get('margin_curr_yi'):,.2f} 億元" + "</strong> (今日變動 <span style='color:var(--amber);font-weight:700;'>" + f"{m_latest_margn.get('margin_diff_yi'):+.2f} 億" + "</span>)" if m_latest_margn.get('is_updated') else "<span style='color:var(--amber);font-weight:700;'>尚未更新 (證交所晚間公佈)</span>"}</li>
                        <li><strong>融券張數餘額</strong>：{"<strong>" + f"{m_latest_margn.get('short_curr_zhang'):,} 張" + "</strong> (今日變動 <span style='color:var(--amber);font-weight:700;'>" + f"{m_latest_margn.get('short_diff_zhang'):+,} 張" + "</span>)" if m_latest_margn.get('is_updated') else "<span style='color:var(--amber);font-weight:700;'>尚未更新 (證交所晚間公佈)</span>"}</li>
                    </ul>
                </div>

                <div class="analysis-card">
                    <h3>🏆 近 5 日 Top 20 爆量王者與產業集中度</h3>
                    <p>近 5 個交易日 Top 20 檔股票合計成交金額高達 <strong>{total_20_val/10000:.2f} 兆台幣</strong>：</p>
                    <ul>
                        {gainers_html}
                    </ul>
                </div>
            </div>
        </div>

        <!-- SECTION B: CARDS GALLERY -->
        <div id="section-cards-view" style="display:none;">
            <div class="s-header">🖼️ 全套 6 大高解析視覺化圖卡展示區 (含雙折線與獨立柱狀圖)</div>
            <div class="card-tabs">
                <button class="card-tab active" onclick="switchCard(1)">圖卡一：大盤與櫃買雙折線圖</button>
                <button class="card-tab" onclick="switchCard(2)">圖卡二：三大法人4系列柱狀圖</button>
                <button class="card-tab" onclick="switchCard(3)">圖卡三：融資金額變動柱狀圖</button>
                <button class="card-tab" onclick="switchCard(4)">圖卡四：TOP 20 總覽卡</button>
                <button class="card-tab" onclick="switchCard(5)">圖卡五：Top 1-10 巨頭卡</button>
                <button class="card-tab" onclick="switchCard(6)">圖卡六：Top 11-20 潛力卡</button>
            </div>
            <div class="card-view">
                <img id="c1" src="{b64_cards[0]}">
                <img id="c2" src="{b64_cards[1]}" style="display:none;">
                <img id="c3" src="{b64_cards[2]}" style="display:none;">
                <img id="c4" src="{b64_cards[3]}" style="display:none;">
                <img id="c5" src="{b64_cards[4]}" style="display:none;">
                <img id="c6" src="{b64_cards[5]}" style="display:none;">
            </div>
        </div>

    </div>

    <!-- STOCK DETAIL MODAL -->
    <div id="stockModal" class="modal-overlay" onclick="closeModalOutside(event)">
        <div class="modal-card">
            <button class="modal-close" onclick="closeStockModal()">✕</button>
            <div class="modal-header">
                <div class="modal-title" id="m-title">--</div>
                <span id="m-market" class="m-twse">--</span>
                <span id="m-sector" style="color:var(--muted);font-size:14px;">--</span>
            </div>
            
            <div class="metrics" style="margin-bottom:15px;grid-template-columns:repeat(auto-fit, minmax(160px,1fr));">
                <div class="m-card"><div class="m-label">最新收盤價</div><div class="m-val" id="m-price">--</div></div>
                <div class="m-card"><div class="m-label">當日漲跌 (元/%)</div><div class="m-val" id="m-today-chg">--</div></div>
                <div class="m-card"><div class="m-label">5日波段漲跌</div><div class="m-val" id="m-chg">--</div></div>
                <div class="m-card"><div class="m-label">5日總成交金額</div><div class="m-val" id="m-total-val">--</div></div>
                <div class="m-card"><div class="m-label">5日總成交量</div><div class="m-val" id="m-total-vol">--</div></div>
            </div>

            <div class="chart-box">
                <div style="font-weight:700;margin-bottom:10px;color:var(--blue);">📈 近 5 日股價走勢與每日成交金額雙軸圖</div>
                <canvas id="stockCanvas" height="240"></canvas>
            </div>

            <div style="font-weight:700;font-size:16px;margin-top:20px;">📅 近 5 個交易日詳細數據明細表</div>
            <table class="detail-table">
                <thead>
                    <tr><th>日期</th><th>收盤價 (元)</th><th>當日漲跌 (元/%)</th><th>5日累計漲跌</th><th>成交金額 (億元)</th><th>成交量 (張)</th></tr>
                </thead>
                <tbody id="m-table-body">
                </tbody>
            </table>
        </div>
    </div>

    <footer><p>台股盤後大數據與籌碼動向觀測站 | <a href="index.html" style="color:var(--blue);text-decoration:none;font-weight:700;">🏠 回首頁 Portal</a> | 產生時間：{today_formatted}</p></footer>

    <script>
        const STOCKS_DATA = {stocks_detail_json};

        function switchMainView(viewName) {{
            const tblSec = document.getElementById('section-table-view');
            const cardSec = document.getElementById('section-cards-view');
            const btnTbl = document.getElementById('nav-btn-table');
            const btnCard = document.getElementById('nav-btn-cards');

            if (viewName === 'table') {{
                tblSec.style.display = 'block';
                cardSec.style.display = 'none';
                btnTbl.classList.add('active');
                btnCard.classList.remove('active');
            }} else {{
                tblSec.style.display = 'none';
                cardSec.style.display = 'block';
                btnTbl.classList.remove('active');
                btnCard.classList.add('active');
            }}
        }}

        function switchCard(n) {{
            for (let i = 1; i <= 6; i++) {{
                const el = document.getElementById('c' + i);
                if (el) el.style.display = (i === n) ? 'block' : 'none';
            }}
            document.querySelectorAll('.card-tab').forEach((b, i) => b.classList.toggle('active', i === n - 1));
        }}

        function openStockModal(code) {{
            const s = STOCKS_DATA[code];
            if (!s) return;

            document.getElementById('m-title').textContent = `${{s.code}} ${{s.name}}`;
            document.getElementById('m-market').textContent = s.market;
            document.getElementById('m-market').className = s.market === '上市' ? 'm-twse' : 'm-tpex';
            document.getElementById('m-sector').textContent = s.sector;

            document.getElementById('m-price').textContent = `$${{s.latest_close.toFixed(2)}}`;
            const todaySign = s.today_change_val > 0 ? '+' : '';
            const todayClr = s.today_change_val > 0 ? 'var(--red)' : (s.today_change_val < 0 ? 'var(--green)' : 'var(--muted)');
            document.getElementById('m-today-chg').innerHTML = `<span style="color:${{todayClr}}">${{todaySign}}$${{s.today_change_val.toFixed(2)}} (${{todaySign}}${{s.today_change_pct.toFixed(2)}}%)</span>`;

            const chgSign = s.change_pct > 0 ? '+' : '';
            const chgColor = s.change_pct > 0 ? 'var(--red)' : (s.change_pct < 0 ? 'var(--green)' : 'var(--muted)');
            document.getElementById('m-chg').innerHTML = `<span style="color:${{chgColor}}">${{chgSign}}${{s.change_pct.toFixed(2)}}%</span>`;
            document.getElementById('m-total-val').textContent = `${{s.total_value_yi.toFixed(1)}} 億`;
            document.getElementById('m-total-vol').textContent = `${{s.total_volume_zhang.toLocaleString()}} 張`;

            let tbody = '';
            for (let i = 0; i < s.daily_dates.length; i++) {{
                let dateStr = s.daily_dates[i];
                let p = s.daily_closes[i];
                let v = s.daily_values_yi[i];
                let vol = s.daily_volumes_zhang[i];

                let prevP = i > 0 ? s.daily_closes[i-1] : (s.prev_close || p);
                let dayDiff = p - prevP;
                let dayDiffPct = prevP > 0 ? ((p - prevP) / prevP * 100) : 0;
                let dClr = dayDiff > 0 ? 'var(--red)' : (dayDiff < 0 ? 'var(--green)' : 'var(--muted)');
                let dSign = dayDiff > 0 ? '+' : '';

                let firstP = s.first_close;
                let chgP = p > 0 && firstP > 0 ? ((p - firstP) / firstP * 100).toFixed(2) : '0.00';
                let cClr = chgP > 0 ? 'var(--red)' : (chgP < 0 ? 'var(--green)' : 'var(--muted)');
                let cSign = chgP > 0 ? '+' : '';

                tbody += `<tr>
                    <td><strong>${{dateStr}}</strong></td>
                    <td>$${{p.toFixed(2)}}</td>
                    <td style="color:${{dClr}};font-weight:700;">${{dSign}}$${{dayDiff.toFixed(2)}} (${{dSign}}${{dayDiffPct.toFixed(2)}}%)</td>
                    <td style="color:${{cClr}};font-weight:700;">${{cSign}}${{chgP}}%</td>
                    <td>${{v.toFixed(1)}} 億</td>
                    <td>${{vol.toLocaleString()}} 張</td>
                </tr>`;
            }}
            document.getElementById('m-table-body').innerHTML = tbody;

            document.getElementById('stockModal').style.display = 'flex';

            setTimeout(() => {{
                drawStockCanvasChart('stockCanvas', s.daily_dates, s.daily_closes, s.daily_values_yi);
            }}, 50);
        }}

        function closeStockModal() {{
            document.getElementById('stockModal').style.display = 'none';
        }}

        function closeModalOutside(e) {{
            if (e.target.id === 'stockModal') {{
                closeStockModal();
            }}
        }}

        function drawStockCanvasChart(canvasId, dates, prices, values) {{
            const canvas = document.getElementById(canvasId);
            const ctx = canvas.getContext('2d');
            const parentW = canvas.parentElement.clientWidth - 40;
            canvas.width = parentW > 300 ? parentW : 600;
            canvas.height = 220;

            const W = canvas.width;
            const H = canvas.height;

            ctx.clearRect(0, 0, W, H);

            ctx.strokeStyle = '#30363d';
            ctx.lineWidth = 1;
            for (let i = 0; i <= 3; i++) {{
                let y = 20 + i * 45;
                ctx.beginPath();
                ctx.moveTo(40, y);
                ctx.lineTo(W - 20, y);
                ctx.stroke();
            }}

            const maxVal = Math.max(...values) || 1;
            const minP = Math.min(...prices);
            const maxP = Math.max(...prices);
            const rangeP = (maxP - minP) || 1;
            const stepX = (W - 80) / (dates.length - 1 || 1);

            dates.forEach((d, i) => {{
                let x = 50 + i * stepX;
                let barH = (values[i] / maxVal) * 70;
                ctx.fillStyle = (i === dates.length - 1) ? '#238636' : '#1f6feb';
                ctx.fillRect(x - 16, 175 - barH, 32, barH);

                ctx.fillStyle = '#8b949e';
                ctx.font = '12px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(d, x, 195);

                ctx.fillStyle = '#c9d1d9';
                ctx.fillText(values[i].toFixed(1) + '億', x, 170 - barH);
            }});

            ctx.beginPath();
            ctx.strokeStyle = '#f85149';
            ctx.lineWidth = 3;
            dates.forEach((d, i) => {{
                let x = 50 + i * stepX;
                let y = 95 - ((prices[i] - minP) / rangeP) * 55;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }});
            ctx.stroke();

            dates.forEach((d, i) => {{
                let x = 50 + i * stepX;
                let y = 95 - ((prices[i] - minP) / rangeP) * 55;

                ctx.beginPath();
                ctx.arc(x, y, 5, 0, Math.PI * 2);
                ctx.fillStyle = '#f85149';
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.stroke();

                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 12px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('$' + prices[i].toFixed(1), x, y - 10);
            }});
        }}
    </script>
</body>
</html>"""

    html_file1 = os.path.join(outdir, f"{today_formatted}.html")
    html_file2 = os.path.join(outdir, f"{today_date}.html")

    with open(html_file1, 'w', encoding='utf-8') as f:
        f.write(html)
    with open(html_file2, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[+] Written daily HTML report to {html_file1}")
    return html_file1

def purge_old_files(outdir, days=30):
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    print(f"[+] Purging files older than {days} days (Cutoff date: {cutoff})...")
    
    purged_count = 0
    all_files = glob.glob(os.path.join(outdir, "*"))
    for fpath in all_files:
        filename = os.path.basename(fpath)
        if filename in ["index.html", "twse_top20_helper.py", "build_html_report.py", "process_top20_trading_value.py"]:
            continue
            
        file_date = None
        for part in filename.replace('.', '_').split('_'):
            if len(part) == 10 and part[4] == '-' and part[7] == '-':
                try:
                    file_date = datetime.datetime.strptime(part, "%Y-%m-%d").date()
                    break
                except Exception:
                    pass
        
        if not file_date:
            mtime = os.path.getmtime(fpath)
            file_date = datetime.date.fromtimestamp(mtime)
            
        if file_date < cutoff:
            try:
                os.remove(fpath)
                print(f"   [-] Purged old file: {filename} (Date: {file_date})")
                purged_count += 1
            except Exception as e:
                print(f"   [!] Failed to purge {filename}: {e}")

    print(f"[+] Total old files purged: {purged_count}")

def sync_to_google_drive(outdir):
    if not os.path.exists(RCLONE_BIN):
        print("[-] Rclone binary not found.")
        return False

    try:
        res = subprocess.run([RCLONE_BIN, "listremotes"], capture_output=True, text=True)
        if "gdrive:" in res.stdout:
            print("[+] Syncing files to Google Drive 'gdrive:近5日台股成交金額TOP20深度分析'...")
            sync_cmd = [RCLONE_BIN, "copy", outdir, "gdrive:近5日台股成交金額TOP20深度分析", "--update"]
            sync_res = subprocess.run(sync_cmd, capture_output=True, text=True)
            if sync_res.returncode == 0:
                print("[+] Successfully synced files to Google Drive!")
                return True
            else:
                print(f"[!] Sync error: {sync_res.stderr}")
        else:
            print("[-] Google Drive remote 'gdrive:' is not configured yet in rclone.")
    except Exception as e:
        print(f"[!] Google Drive sync error: {e}")
    return False

def sync_to_github(outdir):
    """Sync all reports and cards to GitHub repository 'tw_stock' with force overwrite if duplicated"""
    print("[+] Syncing files to GitHub repository 'tw_stock'...")
    try:
        os.chdir(outdir)
        if not os.path.exists(os.path.join(outdir, ".git")):
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "config", "user.name", "jrh"], check=True)
            subprocess.run(["git", "config", "user.email", "jrh2005@gmail.com"], check=True)

        remotes = subprocess.run(["git", "remote"], capture_output=True, text=True).stdout
        if "origin" not in remotes:
            subprocess.run(["git", "remote", "add", "origin", GITHUB_REMOTE_URL], check=True)
        else:
            subprocess.run(["git", "remote", "set-url", "origin", GITHUB_REMOTE_URL], check=True)

        subprocess.run(["git", "branch", "-M", "main"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        
        status_out = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if status_out.strip():
            commit_msg = f"Auto update TW Stock analysis reports & cards: {datetime.date.today().strftime('%Y-%m-%d')}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            
        push_res = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
        if push_res.returncode == 0:
            print("[+] Successfully pushed reports and cards to GitHub repository 'tw_stock'!")
            return True
        else:
            print(f"[!] GitHub push output: {push_res.stdout} {push_res.stderr}")
    except Exception as e:
        print(f"[!] GitHub sync error: {e}")
    return False

def update_index_portal(outdir):
    update_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_files = sorted(glob.glob(os.path.join(outdir, "20??-??-??.html")), reverse=True)
    
    reports = []
    for hf in html_files:
        basename = os.path.basename(hf)
        date_str = basename.replace(".html", "")
        reports.append({
            'date': date_str,
            'file': basename,
            'c1': f"taiwan_stock_card1_market_index_{date_str}.png",
            'c2': f"taiwan_stock_card2_bfi82u_{date_str}.png",
            'c3': f"taiwan_stock_card3_margin_{date_str}.png",
            'c4': f"taiwan_stock_card4_top20_overview_{date_str}.png",
            'c5': f"taiwan_stock_card5_top1_10_{date_str}.png",
            'c6': f"taiwan_stock_card6_top11_20_{date_str}.png",
            'csv': f"taiwan_stock_top20_trading_value_5days_{date_str}.csv"
        })

    latest_file = reports[0]['file'] if reports else "2026-07-24.html"
    latest_date = reports[0]['date'] if reports else "2026-07-24"

    cards_html = ""
    for r in reports:
        cards_html += f"""
            <div class="report-card">
                <div>
                    <div class="card-date">📊 {r['date']} 全方位大數據分析報告</div>
                    <div class="card-desc">整合雙折線圖與柱狀圖 (6張圖卡)、三大法人籌碼、信用交易與 CSV 數據檔</div>
                </div>
                <div class="links-bar">
                    <a href="{r['file']}" class="btn-action primary">開啟完整分析網頁 →</a>
                    <a href="{r['c1']}" class="btn-action secondary" target="_blank">雙折線圖卡</a>
                    <a href="{r['c2']}" class="btn-action secondary" target="_blank">法人柱狀圖卡</a>
                    <a href="{r['c3']}" class="btn-action secondary" target="_blank">融資柱狀圖卡</a>
                    <a href="{r['c4']}" class="btn-action secondary" target="_blank">TOP20圖卡</a>
                    <a href="{r['csv']}" class="btn-action csv">下載 CSV</a>
                </div>
            </div>"""

    list_html = ""
    for r in reports:
        list_html += f"""
            <tr>
                <td><strong>{r['date']}</strong></td>
                <td>台股全方位盤後大數據深度分析與籌碼動向報告 (含雙折線與柱狀統計圖)</td>
                <td>
                    <a href="{r['file']}" class="btn-action primary">開啟網頁</a>
                    <a href="{r['c1']}" class="btn-action secondary" target="_blank">雙折線圖卡</a>
                    <a href="{r['c2']}" class="btn-action secondary" target="_blank">法人柱狀圖卡</a>
                    <a href="{r['c3']}" class="btn-action secondary" target="_blank">融資柱狀圖卡</a>
                    <a href="{r['c4']}" class="btn-action secondary" target="_blank">TOP20圖卡</a>
                    <a href="{r['csv']}" class="btn-action csv">CSV</a>
                </td>
            </tr>"""

    index_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台股盤後大數據與籌碼動向觀測站 - 報告入口總覽 Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg-dark:#0d1117; --bg-card:#161b22; --bg-hover:#1f242d; --border:#30363d; --text:#f0f6fc; --muted:#8b949e; --blue:#58a6ff; --green:#3fb950; --purple:#bc8cff; }}
        * {{ box-sizing:border-box; margin:0; padding:0; }}
        body {{ font-family:'Noto Sans TC','Inter',sans-serif; background-color:var(--bg-dark); color:var(--text); line-height:1.6; padding-bottom:60px; }}
        .hero {{ background:linear-gradient(135deg, #161b22 0%, #0d1117 100%); border-bottom:1px solid var(--border); padding:45px 20px 35px; text-align:center; position:relative; }}
        .hero::before {{ content:''; position:absolute; top:0; left:0; right:0; height:4px; background:linear-gradient(90deg, #58a6ff, #bc8cff, #3fb950); }}
        .badge {{ display:inline-block; background:rgba(188,140,255,0.15); color:var(--purple); padding:6px 16px; border-radius:20px; font-size:14px; font-weight:700; margin-bottom:12px; border:1px solid rgba(188,140,255,0.3); }}
        h1 {{ font-size:34px; font-weight:900; margin-bottom:10px; background:linear-gradient(90deg, #ffffff, #c9d1d9); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
        .sub {{ color:var(--muted); font-size:16px; margin-bottom:15px; }}
        .update-time-box {{ display:inline-block; background:#21262d; border:1px solid var(--border); border-radius:8px; padding:6px 14px; font-size:14px; color:var(--blue); font-weight:700; margin-bottom:20px; }}
        .btn-latest {{ display:inline-block; background:var(--blue); color:#000; font-weight:800; font-size:16px; padding:12px 28px; border-radius:8px; text-decoration:none; transition:all 0.2s; box-shadow:0 4px 15px rgba(88,166,255,0.3); }}
        .btn-latest:hover {{ transform:translateY(-2px); box-shadow:0 6px 20px rgba(88,166,255,0.5); }}
        .container {{ max-width:1100px; margin:40px auto; padding:0 20px; }}
        .view-controls {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; flex-wrap:wrap; gap:12px; }}
        .s-title {{ border-left:4px solid var(--blue); padding-left:12px; font-size:22px; font-weight:800; }}
        .toggle-group {{ display:flex; gap:6px; background:#161b22; padding:4px; border-radius:8px; border:1px solid var(--border); }}
        .toggle-btn {{ background:transparent; border:none; color:var(--muted); padding:6px 14px; border-radius:6px; font-weight:700; font-size:14px; cursor:pointer; transition:all 0.2s; }}
        .toggle-btn.active {{ background:var(--blue); color:#000; }}
        .grid-view {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:20px; }}
        .report-card {{ background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:22px; transition:transform 0.2s, border-color 0.2s; display:flex; flex-direction:column; justify-content:space-between; }}
        .report-card:hover {{ transform:translateY(-3px); border-color:var(--blue); }}
        .card-date {{ font-size:18px; font-weight:800; color:var(--blue); margin-bottom:8px; }}
        .card-desc {{ font-size:13px; color:var(--muted); margin-bottom:16px; }}
        .links-bar {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }}
        .btn-action {{ display:inline-block; font-weight:700; font-size:13px; text-align:center; padding:7px 12px; border-radius:6px; text-decoration:none; transition:all 0.2s; }}
        .btn-action.primary {{ background:var(--blue); color:#000; }}
        .btn-action.secondary {{ background:#21262d; color:var(--text); border:1px solid var(--border); }}
        .btn-action.secondary:hover {{ background:var(--bg-hover); border-color:var(--blue); }}
        .btn-action.csv {{ background:rgba(63,185,80,0.15); color:var(--green); border:1px solid rgba(63,185,80,0.4); }}
        .btn-action.csv:hover {{ background:var(--green); color:#000; }}
        .list-view {{ width:100%; background:var(--bg-card); border:1px solid var(--border); border-radius:12px; overflow:hidden; border-collapse:collapse; font-size:14px; text-align:left; }}
        .list-view th, .list-view td {{ padding:14px 18px; border-bottom:1px solid var(--border); }}
        .list-view th {{ background:#161b22; color:var(--muted); }}
        .list-view tr:hover {{ background:var(--bg-hover); }}
        footer {{ text-align:center; color:var(--muted); font-size:13px; border-top:1px solid var(--border); padding-top:30px; margin-top:60px; }}
    </style>
</head>
<body>
    <div class="hero">
        <div class="badge">台股盤後大數據與籌碼動向觀測站 Portal 入口網頁</div>
        <h1>台股盤後大數據與籌碼動向觀測站</h1>
        <p class="sub">自動整合加權與櫃買雙折線圖、三大法人4系列柱狀圖、信用交易與成交金額 TOP 20 爆量強勢股</p>
        <div class="update-time-box">🕒 最新系統資料更新時間：{update_time_str}</div><br>
        <div style="margin-top: 15px; display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
            <a href="{latest_file}" class="btn-latest">🚀 閱讀最新全方位日報 ({latest_date})</a>
            <a href="etf_dashboard.html" class="btn-latest" style="background: linear-gradient(135deg, #bc8cff 0%, #58a6ff 100%); color: #000; box-shadow: 0 4px 15px rgba(188,140,255,0.4);">📊 進入 ETF 5日大數據與排行榜觀測站 →</a>
        </div>
    </div>

    <div class="container">
        <div class="view-controls">
            <div class="s-title">📅 歷日分析報告典藏歸檔 (日期由新到舊排序)</div>
            <div class="toggle-group">
                <button id="btn-cards" class="toggle-btn active" onclick="setView('cards')">🎴 卡片檢視</button>
                <button id="btn-list" class="toggle-btn" onclick="setView('list')">📋 條列檢視</button>
            </div>
        </div>

        <div id="cards-container" class="grid-view">
            {cards_html}
        </div>

        <div id="list-container" style="display:none;">
            <table class="list-view">
                <thead>
                    <tr>
                        <th>報告日期</th>
                        <th>報告標題</th>
                        <th>操作與下載</th>
                    </tr>
                </thead>
                <tbody>
                    {list_html}
                </tbody>
            </table>
        </div>
    </div>
    <footer>
        <p>自動化系統排程：每週一至週五 16:00 (盤後初版) 與 21:00 (信用交易完整版) 每日自動更新 2 次 | 🕒 最新資料更新時間：{update_time_str} | 數據來源：TWSE / TPEx</p>
    </footer>

    <script>
        function setView(viewType) {{
            const cardsView = document.getElementById('cards-container');
            const listView = document.getElementById('list-container');
            const btnCards = document.getElementById('btn-cards');
            const btnList = document.getElementById('btn-list');

            if (viewType === 'cards') {{
                cardsView.style.display = 'grid';
                listView.style.display = 'none';
                btnCards.classList.add('active');
                btnList.classList.remove('active');
            }} else {{
                cardsView.style.display = 'none';
                listView.style.display = 'block';
                btnCards.classList.remove('active');
                btnList.classList.add('active');
            }}
            try {{ localStorage.setItem('tw_stock_portal_view', viewType); }} catch(e){{}}
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            try {{
                const savedView = localStorage.getItem('tw_stock_portal_view');
                if (savedView) {{
                    setView(savedView);
                }}
            }} catch(e){{}}
        }});
    </script>
</body>
</html>"""

    index_path = os.path.join(outdir, "index.html")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    print(f"[+] Updated index.html portal at {index_path}")
    return index_path

def run_pipeline_for_date(target_date_str, outdir):
    print(f"[+] Running comprehensive pipeline for target date: {target_date_str}...")
    dates = fetch_valid_trading_days(5, start_date=target_date_str)
    if not dates:
        print(f"[!] Could not fetch valid trading dates for {target_date_str}!")
        return False

    market_history = fetch_market_indices(dates)
    bfi_history = fetch_bfi82u_data(dates)
    margin_history = fetch_margin_data(dates)
    records = fetch_top20_stocks_data(dates)

    card_paths = render_all_6_cards(records, dates, market_history, bfi_history, margin_history, outdir)
    build_comprehensive_daily_html(records, dates, market_history, bfi_history, margin_history, outdir, card_paths)

    # Automatically trigger ETF 5-Day Data Pipeline & Dashboard Builder
    print("[+] Triggering ETF 5-day dataset & ranking dashboard synchronization...")
    try:
        root_dir = "/home/jrh/桌面/JRH20260720"
        b_etf = os.path.join(root_dir, "build_etf_dataset.py")
        b_strict = os.path.join(root_dir, "build_twse_strict_dataset.py")
        b_dash = os.path.join(root_dir, "build_etf_dashboard.py")
        s_portal = os.path.join(root_dir, "sync_etf_portal.py")
        
        if os.path.exists(b_etf):
            subprocess.run([sys.executable, b_etf], check=False)
        if os.path.exists(b_strict):
            subprocess.run([sys.executable, b_strict], check=False)
        if os.path.exists(b_dash):
            subprocess.run([sys.executable, b_dash], check=False)
        if os.path.exists(s_portal):
            subprocess.run([sys.executable, s_portal], check=False)
    except Exception as e:
        print(f"[!] Warning syncing ETF pipeline: {e}")
    return True

def main():
    parser = argparse.ArgumentParser(description="TWSE/TPEx Comprehensive Market & Top 20 Pipeline")
    parser.add_argument("action", nargs="?", default="pipeline", choices=["pipeline", "index", "sync", "purge", "update_all"])
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help="Output directory")
    parser.add_argument("--purge-days", type=int, default=30, help="Days threshold for purging old files")
    parser.add_argument("--target-date", default=None, help="Target date YYYYMMDD or YYYY-MM-DD")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    if args.action == "purge":
        purge_old_files(args.outdir, args.purge_days)
        update_index_portal(args.outdir)
        return

    if args.action == "pipeline":
        print("[+] Starting comprehensive pipeline...")
        target = args.target_date or datetime.date.today().strftime('%Y%m%d')
        run_pipeline_for_date(target, args.outdir)
        purge_old_files(args.outdir, args.purge_days)
        update_index_portal(args.outdir)
        sync_to_google_drive(args.outdir)
        sync_to_github(args.outdir)
        print("[+] Comprehensive pipeline completed successfully!")

    elif args.action == "update_all":
        print("[+] Updating all recent dates (today and 2026-07-23)...")
        run_pipeline_for_date("2026-07-23", args.outdir)
        run_pipeline_for_date(datetime.date.today().strftime('%Y%m%d'), args.outdir)
        purge_old_files(args.outdir, args.purge_days)
        update_index_portal(args.outdir)
        sync_to_google_drive(args.outdir)
        sync_to_github(args.outdir)
        print("[+] Update all completed successfully!")

    elif args.action == "index":
        update_index_portal(args.outdir)
    elif args.action == "sync":
        sync_to_google_drive(args.outdir)
        sync_to_github(args.outdir)

if __name__ == "__main__":
    main()
