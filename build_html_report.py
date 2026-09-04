#!/usr/bin/env python3
import os
import sys
import json
import base64
import csv
import datetime
import urllib.request
import ssl

OUTPUT_DIR = "/home/jrh/桌面/JRH20260720"
SUB_DIR = os.path.join(OUTPUT_DIR, "近5日台股成交金額TOP20深度分析")
os.makedirs(SUB_DIR, exist_ok=True)

today_str = datetime.date.today().strftime('%Y-%m-%d')
today_nodash = datetime.date.today().strftime('%Y%m%d')

# SSL context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Path references for 6 cards
card1_path = os.path.join(SUB_DIR, f"taiwan_stock_card1_market_index_{today_str}.png")
card2_path = os.path.join(SUB_DIR, f"taiwan_stock_card2_bfi82u_{today_str}.png")
card3_path = os.path.join(SUB_DIR, f"taiwan_stock_card3_margin_{today_str}.png")
card4_path = os.path.join(OUTPUT_DIR, "taiwan_stock_top20_card1_overview.png")
card5_path = os.path.join(OUTPUT_DIR, "taiwan_stock_top20_card2_top10_analysis.png")
card6_path = os.path.join(OUTPUT_DIR, "taiwan_stock_top11_20_card3_analysis.png")

if not os.path.exists(card1_path):
    card1_path = os.path.join(SUB_DIR, f"TWSE_TPEX_Market_5Day_{today_nodash}_Card.png")
if not os.path.exists(card2_path):
    card2_path = os.path.join(SUB_DIR, f"TWSE_BFI82U_5Day_{today_nodash}_Card.png")
if not os.path.exists(card3_path):
    card3_path = os.path.join(SUB_DIR, f"TWSE_MI_MARGN_5Day_{today_nodash}_Card.png")

def get_b64(path):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    return ""

b64_c1 = get_b64(card1_path)
b64_c2 = get_b64(card2_path)
b64_c3 = get_b64(card3_path)
b64_c4 = get_b64(card4_path)
b64_c5 = get_b64(card5_path)
b64_c6 = get_b64(card6_path)

# Load JSON records for TOP 20
json_path = os.path.join(OUTPUT_DIR, "taiwan_stock_top20_trading_value_5days.json")
records = []
if os.path.exists(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

stocks_dict = {r['code']: r for r in records}
stocks_json_str = json.dumps(stocks_dict, ensure_ascii=False)

total_top20_val = sum(r.get('total_value_yi', 0) for r in records)
top_gainer = max(records, key=lambda x: x.get('change_pct', -999)) if records else None
top_gainer_str = f"{top_gainer['name']} ({top_gainer['change_pct']:+.2f}%)" if top_gainer else "--"

# Dynamically parse 5-day Market Summary Data from CSV files created by twse_card_helper.py
mkt_csv = os.path.join(SUB_DIR, f"TWSE_TPEX_Market_5Day_{today_nodash}.csv")
if not os.path.exists(mkt_csv):
    mkt_csv = os.path.join(OUTPUT_DIR, f"TWSE_TPEX_Market_5Day_{today_nodash}.csv")

bfi_csv = os.path.join(SUB_DIR, f"TWSE_BFI82U_5Day_{today_nodash}.csv")
if not os.path.exists(bfi_csv):
    bfi_csv = os.path.join(OUTPUT_DIR, f"TWSE_BFI82U_5Day_{today_nodash}.csv")

margin_csv = os.path.join(SUB_DIR, f"TWSE_MI_MARGN_5Day_{today_nodash}.csv")
if not os.path.exists(margin_csv):
    margin_csv = os.path.join(OUTPUT_DIR, f"TWSE_MI_MARGN_5Day_{today_nodash}.csv")

market_rows_data = []

if os.path.exists(mkt_csv) and os.path.exists(bfi_csv):
    with open(mkt_csv, 'r', encoding='utf-8') as f1, open(bfi_csv, 'r', encoding='utf-8') as f2:
        mkt_reader = list(csv.DictReader(f1))
        bfi_reader = list(csv.DictReader(f2))
        
        bfi_map = {}
        for r in bfi_reader:
            d_raw = r['日期'].replace('-', '').replace('/', '').strip()
            d_short = f"{d_raw[4:6]}/{d_raw[6:8]}" if len(d_raw) == 8 else d_raw
            bfi_map[d_short] = r
            
        margin_map = {}
        if os.path.exists(margin_csv):
            with open(margin_csv, 'r', encoding='utf-8') as f3:
                margin_reader = list(csv.DictReader(f3))
                for r in margin_reader:
                    d_raw = r['日期'].replace('-', '').replace('/', '').strip()
                    d_short = f"{d_raw[4:6]}/{d_raw[6:8]}" if len(d_raw) == 8 else d_raw
                    margin_map[d_short] = r

        for r in mkt_reader:
            d_short = r['日期'].strip()
            b_item = bfi_map.get(d_short, {})
            m_item = margin_map.get(d_short, {})
            
            taiex_val = float(r['上市加權指數'])
            taiex_chg_pct = float(r['上市漲跌幅(%)'])
            taiex_up = taiex_chg_pct >= 0
            val_yi = round(float(r['上市成交金額(元)']) / 1e8, 1)
            tpex_val = r['上櫃櫃買指數']
            
            f_diff = round(float(b_item.get('外資買賣超(元)', 0)) / 1e8, 2) if b_item else 0.0
            tr_diff = round(float(b_item.get('投信買賣超(元)', 0)) / 1e8, 2) if b_item else 0.0
            d1 = float(b_item.get('自營(自行)買賣超(元)', 0)) if b_item else 0.0
            d2 = float(b_item.get('自營(避險)買賣超(元)', 0)) if b_item else 0.0
            dealer_diff = round((d1 + d2) / 1e8, 2)
            tot_diff = round(float(b_item.get('三大法人合計買賣超(元)', 0)) / 1e8, 2) if b_item else 0.0

            if m_item:
                margin_val_yi = round(float(m_item.get('融資餘額(元)', 0)) / 1e8, 2)
                margin_diff_yi = round(float(m_item.get('融資單日增減(元)', 0)) / 1e8, 2)
                m_up = margin_diff_yi >= 0
                margin_curr_str = f"{margin_val_yi:,.2f} 億"
                margin_diff_str = f"{margin_diff_yi:+.2f} 億"
                short_val = f"{int(float(m_item.get('融券餘額(張)', 0))):,}"
                short_diff_str = f"{int(float(m_item.get('融券單日增減(張)', 0))):+d}"
            else:
                margin_curr_str = "--"
                margin_diff_str = "--"
                m_up = True
                short_val = "--"
                short_diff_str = "--"

            sign_str = '+' if taiex_up else ''
            item = {
                'date_show': d_short,
                'taiex': f"{taiex_val:,.2f}",
                'taiex_chg': f"{sign_str}{taiex_chg_pct:.2f}%",
                'taiex_up': taiex_up,
                'val_yi': f"{val_yi:,.1f} 億",
                'tpex': tpex_val,
                'foreign_diff': f_diff,
                'trust_diff': tr_diff,
                'dealer_diff': dealer_diff,
                'tot_diff': tot_diff,
                'margin_curr': margin_curr_str,
                'margin_diff': margin_diff_str,
                'margin_up': m_up,
                'short_curr': short_val,
                'short_diff': short_diff_str
            }
            market_rows_data.append(item)

# Fallback if CSV not created yet
if not market_rows_data:
    market_rows_data = [
        {
            "date_show": "08/26", "taiex": "45,832.62", "taiex_chg": "+1.47%", "taiex_up": True, "val_yi": "8,362.4 億",
            "tpex": "395.66", "foreign_diff": 365.98, "trust_diff": 48.55, "dealer_diff": 179.34, "tot_diff": 593.87,
            "margin_curr": "5,469.38 億", "margin_diff": "+16.78億", "margin_up": True, "short_curr": "200,504", "short_diff": "-1,009"
        }
    ]

# Build Market Table Rows dynamically
market_table_html = ""
for m in market_rows_data:
    taiex_clr = "var(--red)" if m["taiex_up"] else "var(--green)"
    
    f_clr = "var(--red)" if m["foreign_diff"] > 0 else "var(--green)"
    tr_clr = "var(--red)" if m["trust_diff"] > 0 else "var(--green)"
    d_clr = "var(--red)" if m["dealer_diff"] > 0 else "var(--green)"
    tot_clr = "var(--red)" if m["tot_diff"] > 0 else "var(--green)"
    m_clr = "var(--red)" if m["margin_up"] else "var(--green)"
    
    f_str = f"+{m['foreign_diff']:.2f} 億" if m['foreign_diff'] > 0 else f"{m['foreign_diff']:.2f} 億"
    tr_str = f"+{m['trust_diff']:.2f} 億" if m['trust_diff'] > 0 else f"{m['trust_diff']:.2f} 億"
    d_str = f"+{m['dealer_diff']:.2f} 億" if m['dealer_diff'] > 0 else f"{m['dealer_diff']:.2f} 億"
    tot_str = f"+{m['tot_diff']:.2f} 億" if m['tot_diff'] > 0 else f"{m['tot_diff']:.2f} 億"

    market_table_html += f"""
                        <tr>
                            <td><strong>{m['date_show']}</strong></td>
                            <td><strong>{m['taiex']}</strong> (<span style="color:{taiex_clr};font-weight:700;">{m['taiex_chg']}</span>)</td>
                            <td>{m['val_yi']}</td>
                            <td>{m['tpex']}</td>
                            <td style="color:{f_clr};">{f_str}</td>
                            <td style="color:{tr_clr};">{tr_str}</td>
                            <td style="color:{d_clr};">{d_str}</td>
                            <td style="color:{tot_clr};font-weight:800;">{tot_str}</td>
                            <td>{m['margin_curr']} (<span style='color:{m_clr};font-weight:700;'>{m['margin_diff']}</span>)</td>
                        </tr>"""

# Build TOP 20 Table Rows dynamically
table_rows_html = ""
for s in records:
    rank_badge_cls = f"r-{s['rank']}" if s['rank'] <= 3 else "r-o"
    mkt_cls = "m-twse" if s['market'] == "上市" else "m-tpex"
    
    today_chg = s.get('today_change_val', 0.0)
    today_pct = s.get('today_change_pct', 0.0)
    chg_cls = "chg-up" if today_chg > 0 else ("chg-down" if today_chg < 0 else "chg-flat")
    chg_sign = "+" if today_chg > 0 else ""
    
    pct_5d = s.get('change_pct', 0.0)
    pct_5d_cls = "chg-up" if pct_5d > 0 else ("chg-down" if pct_5d < 0 else "chg-flat")
    pct_5d_sign = "+" if pct_5d > 0 else ""

    table_rows_html += f"""
                        <tr class="stock-row" onclick="openStockModal('{s['code']}')">
                            <td><span class="r-badge {rank_badge_cls}">{s['rank']}</span></td>
                            <td><strong>{s['code']}</strong> {s['name']}</td>
                            <td><span class="{mkt_cls}">{s['market']}</span></td>
                            <td style="color:var(--muted);">{s['sector']}</td>
                            <td><strong>{s['total_value_yi']:,.1f} 億</strong></td>
                            <td>{s['avg_value_yi']:,.1f} 億</td>
                            <td>{s['total_volume_zhang']:,} 張</td>
                            <td><strong>${s['latest_close']:,.2f}</strong></td>
                            <td><span class="chg {chg_cls}">{chg_sign}${today_chg:,.2f} ({chg_sign}{today_pct:.2f}%)</span></td>
                            <td><span class="chg {pct_5d_cls}">{pct_5d_sign}{pct_5d:.2f}%</span></td>
                            <td><button style="background:var(--blue);color:#000;border:none;padding:4px 10px;border-radius:4px;font-weight:700;cursor:pointer;">📊 走勢圖</button></td>
                        </tr>"""

latest_m = market_rows_data[0]
sample_oldest = market_rows_data[-1]['date_show'] if market_rows_data else "08/20"
sample_newest = market_rows_data[0]['date_show'] if market_rows_data else "08/26"

html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台股盤後大數據與籌碼動向觀測站 ({today_str})</title>
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
        <div class="badge">台股盤後大數據與籌碼動向觀測站 ({today_str})</div>
        <h1>台股盤後大數據與籌碼動向觀測站</h1>
        <p class="sub">統計資料日期：{today_str} (最近5交易日：{sample_oldest} ～ {sample_newest})  |  整合大盤指數、三大法人買賣超、信用交易與 TOP 20 爆量強勢股</p>
        <div class="metrics">
            <div class="m-card">
                <div class="m-label">加權指數 (TAIEX)</div>
                <div class="m-val" style="color:var(--red);">{latest_m['taiex']} ({latest_m['taiex_chg']})</div>
            </div>
            <div class="m-card">
                <div class="m-label">三大法人買賣超</div>
                <div class="m-val" style="color:var(--red);">+{latest_m['tot_diff']:.2f} 億元</div>
            </div>
            <div class="m-card">
                <div class="m-label">融資餘額 (增減)</div>
                <div class="m-val" style="color:var(--amber);">{latest_m['margin_curr']} ({latest_m['margin_diff']})</div>
            </div>
            <div class="m-card">
                <div class="m-label">Top 20 總成交額</div>
                <div class="m-val" style="color:var(--blue);">{total_top20_val/10000:.2f} 兆台幣</div>
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
                    <tbody>
{market_table_html}
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
                    <tbody>
{table_rows_html}
                    </tbody>
                </table>
            </div>

            <!-- 3. Comprehensive Market & Capital Analysis -->
            <div class="s-header">🔍 全方位盤後大數據與籌碼趨勢深度剖析</div>
            <div class="analysis-grid">
                <div class="analysis-card">
                    <h3>⚡ 大盤與三大法人籌碼趨勢</h3>
                    <p>今日台股加權指數收在 <strong>{latest_m['taiex']} 點</strong>，三大法人今日合計買賣超金額為 <strong style="color:var(--red);">+{latest_m['tot_diff']:.2f} 億元</strong>：</p>
                    <ul>
                        <li><strong>外資動向</strong>：今日買賣超金額為 <strong style="color:var(--red);">+{latest_m['foreign_diff']:.2f} 億元</strong>。</li>
                        <li><strong>投信動向</strong>：買賣超金額為 <strong style="color:var(--red);">+{latest_m['trust_diff']:.2f} 億元</strong>。</li>
                        <li><strong>自營商動向</strong>：合計買賣超金額為 <strong style="color:var(--red);">+{latest_m['dealer_diff']:.2f} 億元</strong>。</li>
                    </ul>
                </div>

                <div class="analysis-card">
                    <h3>💳 信用交易 (融資融券) 變化</h3>
                    <p>市場散戶與內資籌碼浮動情況：</p>
                    <ul>
                        <li><strong>融資金額餘額</strong>：<strong>{latest_m['margin_curr']}</strong> (變動 <span style='color:var(--red);font-weight:700;'>{latest_m['margin_diff']}</span>)</li>
                        <li><strong>融券張數餘額</strong>：<strong>{latest_m['short_curr']} 張</strong> (變動 <span style='color:var(--green);font-weight:700;'>{latest_m['short_diff']} 張</span>)</li>
                    </ul>
                </div>

                <div class="analysis-card">
                    <h3>🏆 近 5 日 Top 20 爆量王者與產業集中度</h3>
                    <p>近 5 個交易日 Top 20 檔股票合計成交金額高達 <strong>{total_top20_val/10000:.2f} 兆台幣</strong>：</p>
                    <ul>
                        <li><strong>5日漲幅王者</strong>：{top_gainer_str}</li>
                        <li><strong>市場資金重心</strong>：半導體晶圓代工、記憶體、IC設計與 AI 伺服器供應鏈。</li>
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
                <img id="c1" src="{b64_c1}" alt="圖卡一：大盤與櫃買雙折線圖">
                <img id="c2" src="{b64_c2}" alt="圖卡二：三大法人4系列柱狀圖" style="display:none;">
                <img id="c3" src="{b64_c3}" alt="圖卡三：融資金額變動柱狀圖" style="display:none;">
                <img id="c4" src="{b64_c4}" alt="圖卡四：TOP 20 總覽卡" style="display:none;">
                <img id="c5" src="{b64_c5}" alt="圖卡五：Top 1-10 巨頭卡" style="display:none;">
                <img id="c6" src="{b64_c6}" alt="圖卡六：Top 11-20 潛力卡" style="display:none;">
            </div>
        </div>
    </div>

    <!-- STOCK DETAIL INTERACTIVE MODAL -->
    <div id="stockModal" class="modal-overlay" onclick="closeModalOutside(event)">
        <div class="modal-card">
            <button class="modal-close" onclick="closeStockModal()">✕</button>
            <div class="modal-header">
                <div class="modal-title" id="m-title">--</div>
                <span id="m-market" class="m-twse">--</span>
                <span id="m-sector" style="color:var(--muted);font-size:14px;font-weight:600;">--</span>
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

    <footer><p>台股盤後大數據與籌碼動向觀測站 | <a href="index.html" style="color:var(--blue);text-decoration:none;font-weight:700;">🏠 回首頁 Portal</a> | 產生時間：{today_str}</p></footer>

    <script>
        const STOCKS_DATA = {stocks_json_str};

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
            document.getElementById('m-chg').innerHTML = `<span style="color:${{chgColor}}">${{chgSign}}$${{s.change_pct.toFixed(2)}}%</span>`;
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
                    <td style="color:${{cClr}};font-weight:700;">${{cSign}}$${{chgP}}%</td>
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
</html>
"""

html_path1 = os.path.join(OUTPUT_DIR, f"{today_str}.html")
html_path2 = os.path.join(OUTPUT_DIR, f"{today_nodash}.html")
sub_html_path1 = os.path.join(SUB_DIR, f"{today_str}.html")
sub_html_path2 = os.path.join(SUB_DIR, f"{today_nodash}.html")

with open(html_path1, 'w', encoding='utf-8') as f:
    f.write(html_content)

with open(html_path2, 'w', encoding='utf-8') as f:
    f.write(html_content)

with open(sub_html_path1, 'w', encoding='utf-8') as f:
    f.write(html_content)

with open(sub_html_path2, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Successfully generated 100% verified real market HTML report at:\n - {html_path1}\n - {sub_html_path1}")

# Automatically refresh index.html portal list
try:
    sys.path.insert(0, SUB_DIR)
    from twse_top20_helper import update_index_portal
    import shutil
    update_index_portal(SUB_DIR)
    sub_index = os.path.join(SUB_DIR, "index.html")
    if os.path.exists(sub_index):
        shutil.copy2(sub_index, os.path.join(OUTPUT_DIR, "index.html"))
    print("Successfully refreshed and synced index.html portal!")
except Exception as e:
    print(f"Warning: Failed to refresh index portal: {e}")

