#!/usr/bin/env python3
import os
import sys
import json
import base64

OUTPUT_DIR = "/home/jrh/桌面/JRH20260720"
CSV_PATH = os.path.join(OUTPUT_DIR, "taiwan_stock_top20_trading_value_5days.csv")

CARD1_PATH = os.path.join(OUTPUT_DIR, "taiwan_stock_top20_card1_overview.png")
CARD2_PATH = os.path.join(OUTPUT_DIR, "taiwan_stock_top20_card2_top10_analysis.png")
CARD3_PATH = os.path.join(OUTPUT_DIR, "taiwan_stock_top11_20_card3_analysis.png")

def get_base64_image(path):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')
            return f"data:image/png;base64,{data}"
    return ""

b64_card1 = get_base64_image(CARD1_PATH)
b64_card2 = get_base64_image(CARD2_PATH)
b64_card3 = get_base64_image(CARD3_PATH)

# Stock records data
STOCKS_DATA = [
    {"rank": 1, "code": "2330", "name": "台積電", "market": "上市", "sector": "半導體 / 晶圓代工", "total_val": 5709.98, "avg_val": 1142.00, "volume": 239944, "price": 2405.00, "change_pct": 5.02},
    {"rank": 2, "code": "2327", "name": "國巨*", "market": "上市", "sector": "被動元件", "total_val": 2153.42, "avg_val": 430.68, "volume": 308610, "price": 696.00, "change_pct": -0.43},
    {"rank": 3, "code": "2454", "name": "聯發科", "market": "上市", "sector": "半導體 / IC設計", "total_val": 1834.64, "avg_val": 366.93, "volume": 49271, "price": 3875.00, "change_pct": 14.99},
    {"rank": 4, "code": "2408", "name": "南亞科", "market": "上市", "sector": "半導體 / 記憶體", "total_val": 1572.50, "avg_val": 314.50, "volume": 363222, "price": 426.00, "change_pct": 7.71},
    {"rank": 5, "code": "2303", "name": "聯電", "market": "上市", "sector": "半導體 / 晶圓代工", "total_val": 1508.97, "avg_val": 301.79, "volume": 1079067, "price": 138.50, "change_pct": -3.82},
    {"rank": 6, "code": "1303", "name": "南亞", "market": "上市", "sector": "塑膠塑化 / 原料", "total_val": 1169.16, "avg_val": 233.83, "volume": 586854, "price": 197.00, "change_pct": -1.01},
    {"rank": 7, "code": "0050", "name": "元大台灣50", "market": "上市", "sector": "指數型 / ETF", "total_val": 1166.48, "avg_val": 233.30, "volume": 1126897, "price": 103.90, "change_pct": 3.74},
    {"rank": 8, "code": "3037", "name": "欣興", "market": "上市", "sector": "電子 / ABF載板", "total_val": 1098.47, "avg_val": 219.69, "volume": 129566, "price": 896.00, "change_pct": 12.85},
    {"rank": 9, "code": "8046", "name": "南電", "market": "上市", "sector": "電子 / ABF載板", "total_val": 1051.94, "avg_val": 210.39, "volume": 88145, "price": 1230.00, "change_pct": 6.96},
    {"rank": 10, "code": "4958", "name": "臻鼎-KY", "market": "上市", "sector": "電子 / PCB軟板", "total_val": 1006.92, "avg_val": 201.38, "volume": 196448, "price": 506.00, "change_pct": -2.88},
    {"rank": 11, "code": "2308", "name": "台達電", "market": "上市", "sector": "電子 / 電源綠能", "total_val": 992.72, "avg_val": 198.54, "volume": 54342, "price": 1880.00, "change_pct": 8.05},
    {"rank": 12, "code": "2344", "name": "華邦電", "market": "上市", "sector": "半導體 / 記憶體", "total_val": 923.67, "avg_val": 184.73, "volume": 572217, "price": 161.00, "change_pct": 3.87},
    {"rank": 13, "code": "6182", "name": "合晶", "market": "上櫃", "sector": "上櫃 / 矽晶圓", "total_val": 828.94, "avg_val": 165.79, "volume": 660119, "price": 126.50, "change_pct": 0.00},
    {"rank": 14, "code": "3481", "name": "群創", "market": "上市", "sector": "光電 / 面板製造", "total_val": 806.00, "avg_val": 161.20, "volume": 1514547, "price": 51.90, "change_pct": -1.33},
    {"rank": 15, "code": "2317", "name": "鴻海", "market": "上市", "sector": "代工 / AI伺服器", "total_val": 738.10, "avg_val": 147.62, "volume": 291098, "price": 257.50, "change_pct": 10.04},
    {"rank": 16, "code": "3231", "name": "緯創", "market": "上市", "sector": "電腦 / AI伺服器", "total_val": 717.09, "avg_val": 143.42, "volume": 436819, "price": 173.50, "change_pct": 24.82},
    {"rank": 17, "code": "3711", "name": "日月光投控", "market": "上市", "sector": "半導體 / 封測", "total_val": 701.01, "avg_val": 140.20, "volume": 110637, "price": 649.00, "change_pct": 5.70},
    {"rank": 18, "code": "6274", "name": "台燿", "market": "上櫃", "sector": "上櫃 / CCL銅箔基板", "total_val": 671.10, "avg_val": 134.22, "volume": 50569, "price": 1335.00, "change_pct": 0.00},
    {"rank": 19, "code": "2383", "name": "台光電", "market": "上市", "sector": "電子 / CCL銅箔基板", "total_val": 615.77, "avg_val": 123.15, "volume": 12504, "price": 5095.00, "change_pct": 13.35},
    {"rank": 20, "code": "00631L", "name": "元大台灣50正2", "market": "上市", "sector": "槓桿型 / ETF", "total_val": 610.77, "avg_val": 122.15, "volume": 1733359, "price": 35.07, "change_pct": 9.01}
]

html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台股近5日成交金額前20名分析與視覺化圖卡報告 (2026/07/17-07/23)</title>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap" rel="stylesheet">

    <style>
        :root {{
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --bg-card-hover: #1f242d;
            --border-color: #30363d;
            --text-main: #f0f6fc;
            --text-muted: #8b949e;
            --accent-blue: #58a6ff;
            --accent-purple: #bc8cff;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-amber: #d29922;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Noto Sans TC', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            line-height: 1.6;
            padding-bottom: 60px;
        }}

        /* Header / Hero Section */
        .hero {{
            background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 40px 20px 30px;
            text-align: center;
            position: relative;
        }}

        .hero::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 4px;
            background: linear-gradient(90deg, #58a6ff, #bc8cff, #3fb950);
        }}

        .title-badge {{
            display: inline-block;
            background: rgba(88, 166, 255, 0.15);
            color: var(--accent-blue);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 12px;
            border: 1px solid rgba(88, 166, 255, 0.3);
        }}

        h1 {{
            font-size: 32px;
            font-weight: 900;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #ffffff, #c9d1d9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .hero-subtitle {{
            color: var(--text-muted);
            font-size: 15px;
            margin-bottom: 25px;
        }}

        /* Metric Cards Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            max-width: 1200px;
            margin: 0 auto;
        }}

        .metric-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 18px 20px;
            text-align: left;
            transition: transform 0.2s, border-color 0.2s;
        }}

        .metric-card:hover {{
            transform: translateY(-2px);
            border-color: var(--accent-blue);
        }}

        .metric-label {{
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 6px;
        }}

        .metric-value {{
            font-size: 24px;
            font-weight: 800;
            color: var(--text-main);
        }}

        .metric-sub {{
            font-size: 12px;
            margin-top: 4px;
        }}

        .text-red {{ color: var(--accent-red); }}
        .text-green {{ color: var(--accent-green); }}
        .text-blue {{ color: var(--accent-blue); }}
        .text-amber {{ color: var(--accent-amber); }}

        /* Main Container */
        .container {{
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }}

        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            border-left: 4px solid var(--accent-blue);
            padding-left: 12px;
        }}

        .section-title {{
            font-size: 22px;
            font-weight: 800;
        }}

        /* Infographic Gallery Tabs */
        .card-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
        }}

        .tab-btn {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 700;
            transition: all 0.2s;
        }}

        .tab-btn:hover {{
            color: var(--text-main);
            background: var(--bg-card-hover);
        }}

        .tab-btn.active {{
            background: var(--accent-blue);
            color: #000;
            border-color: var(--accent-blue);
        }}

        .card-display {{
            text-align: center;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 40px;
        }}

        .card-display img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }}

        /* Filter Controls */
        .controls-bar {{
            display: flex;
            gap: 15px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}

        .search-input {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 10px 16px;
            border-radius: 8px;
            font-size: 14px;
            min-width: 250px;
            outline: none;
        }}

        .search-input:focus {{
            border-color: var(--accent-blue);
        }}

        /* Data Table Styling */
        .table-responsive {{
            overflow-x: auto;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 40px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            text-align: left;
        }}

        th {{
            background: #161b22;
            color: var(--text-muted);
            font-weight: 700;
            padding: 14px 16px;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
        }}

        td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
        }}

        tr:hover {{
            background: var(--bg-card-hover);
        }}

        /* Badges & Pills */
        .rank-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 6px;
            font-weight: 800;
            font-size: 13px;
        }}

        .rank-1 {{ background: #ffd700; color: #000; }}
        .rank-2 {{ background: #c0c0c0; color: #000; }}
        .rank-3 {{ background: #cd7f32; color: #000; }}
        .rank-other {{ background: #21262d; color: var(--text-muted); }}

        .market-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 700;
        }}

        .market-twse {{ background: rgba(31, 111, 235, 0.2); color: #58a6ff; border: 1px solid rgba(31, 111, 235, 0.4); }}
        .market-tpex {{ background: rgba(210, 153, 34, 0.2); color: #d29922; border: 1px solid rgba(210, 153, 34, 0.4); }}

        .change-tag {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 13px;
        }}

        .change-up {{ background: rgba(248, 81, 73, 0.2); color: var(--accent-red); border: 1px solid rgba(248, 81, 73, 0.4); }}
        .change-down {{ background: rgba(63, 185, 80, 0.2); color: var(--accent-green); border: 1px solid rgba(63, 185, 80, 0.4); }}
        .change-flat {{ background: rgba(139, 148, 158, 0.2); color: var(--text-muted); border: 1px solid rgba(139, 148, 158, 0.4); }}

        /* Bar visual indicator in table */
        .bar-container {{
            width: 100px;
            height: 6px;
            background: #21262d;
            border-radius: 3px;
            overflow: hidden;
            display: inline-block;
            vertical-align: middle;
            margin-left: 8px;
        }}

        .bar-fill {{
            height: 100%;
            background: var(--accent-blue);
        }}

        /* Markdown Analysis Section */
        .analysis-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .analysis-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
        }}

        .analysis-card h3 {{
            font-size: 18px;
            color: var(--accent-blue);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .analysis-card p, .analysis-card ul {{
            font-size: 14px;
            color: #c9d1d9;
        }}

        .analysis-card ul {{
            padding-left: 18px;
            margin-top: 8px;
        }}

        .analysis-card li {{
            margin-bottom: 8px;
        }}

        /* Footer */
        footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 13px;
            border-top: 1px solid var(--border-color);
            padding-top: 30px;
            margin-top: 50px;
        }}
    </style>
</head>
<body>

    <!-- HERO SECTION -->
    <div class="hero">
        <div class="title-badge">台股盤後數據專題報告</div>
        <h1>近 5 日台股成交金額 TOP 20 深度分析</h1>
        <p class="hero-subtitle">統計區間：2026/07/17（五）～ 2026/07/23（四） | 涵蓋上市 (TWSE) 與上櫃 (TPEx)</p>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Top 20 總成交金額</div>
                <div class="metric-value text-blue">2.81 兆元</div>
                <div class="metric-sub text-muted">佔全市場巨量資金重心</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Top 20 日均成交額</div>
                <div class="metric-value">5,616.7 億</div>
                <div class="metric-sub text-muted">平均每日交易熱度</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">5日漲幅王者</div>
                <div class="metric-value text-red">緯創 (+24.82%)</div>
                <div class="metric-sub text-muted">AI 伺服器資金強烈追捧</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">市場結構</div>
                <div class="metric-value text-amber">18 檔上市 / 2 檔上櫃</div>
                <div class="metric-sub text-muted">合晶、台燿 攻入前 20 強</div>
            </div>
        </div>
    </div>

    <div class="container">

        <!-- INFOGRAPHIC CARDS GALLERY -->
        <div class="section-header">
            <div class="section-title">🖼️ 視覺化高解析圖卡展示 (Infographic Cards)</div>
        </div>

        <div class="card-tabs">
            <button class="tab-btn active" onclick="switchCard(1)">圖卡一：TOP 20 總覽卡</button>
            <button class="tab-btn" onclick="switchCard(2)">圖卡二：Top 1-10 爆量巨頭</button>
            <button class="tab-btn" onclick="switchCard(3)">圖卡三：Top 11-20 潛力/上櫃黑馬</button>
        </div>

        <div class="card-display">
            <img id="card-img-1" src="{b64_card1}" alt="圖卡一：Top 20 總覽卡">
            <img id="card-img-2" src="{b64_card2}" alt="圖卡二：Top 1-10 巨頭卡" style="display:none;">
            <img id="card-img-3" src="{b64_card3}" alt="圖卡三：Top 11-20 潛力卡" style="display:none;">
        </div>

        <!-- TOP 20 DATA TABLE -->
        <div class="section-header">
            <div class="section-title">📈 近 5 日成交金額 TOP 20 完整榜單</div>
        </div>

        <div class="controls-bar">
            <input type="text" id="searchInput" class="search-input" placeholder="🔍 搜尋股票代號、名稱或產業..." onkeyup="filterTable()">
        </div>

        <div class="table-responsive">
            <table id="stockTable">
                <thead>
                    <tr>
                        <th>名次</th>
                        <th>代號 / 股票名稱</th>
                        <th>市場</th>
                        <th>產業分類</th>
                        <th>5日總成交額 (億)</th>
                        <th>日均成交額 (億)</th>
                        <th>5日成交量 (張)</th>
                        <th>最新收盤價</th>
                        <th>5日漲跌幅</th>
                    </tr>
                </thead>
                <tbody>
"""

# Build table rows dynamically
max_val = STOCKS_DATA[0]["total_val"]
for s in STOCKS_DATA:
    rank_cls = f"rank-{s['rank']}" if s['rank'] <= 3 else "rank-other"
    mkt_cls = "market-twse" if s['market'] == "上市" else "market-tpex"
    chg_cls = "change-up" if s['change_pct'] > 0 else ("change-down" if s['change_pct'] < 0 else "change-flat")
    chg_sign = "+" if s['change_pct'] > 0 else ""
    bar_w = int((s['total_val'] / max_val) * 100)
    
    html_content += f"""
                    <tr>
                        <td><span class="rank-badge {rank_cls}">{s['rank']}</span></td>
                        <td><strong>{s['code']}</strong> {s['name']}</td>
                        <td><span class="market-badge {mkt_cls}">{s['market']}</span></td>
                        <td style="color:var(--text-muted);">{s['sector']}</td>
                        <td>
                            <strong>{s['total_val']:,.1f} 億</strong>
                            <div class="bar-container"><div class="bar-fill" style="width:{bar_w}%;"></div></div>
                        </td>
                        <td>{s['avg_val']:,.1f} 億</td>
                        <td>{s['volume']:,} 張</td>
                        <td><strong>${s['price']:,.2f}</strong></td>
                        <td><span class="change-tag {chg_cls}">{chg_sign}{s['change_pct']:.2f}%</span></td>
                    </tr>"""

html_content += """
                </tbody>
            </table>
        </div>

        <!-- MARKET ANALYSIS GRID -->
        <div class="section-header">
            <div class="section-title">🔍 詳細市場與籌碼亮點解析</div>
        </div>

        <div class="analysis-grid">
            <div class="analysis-card">
                <h3>⚡ 產業吸金集中度剖析</h3>
                <p>資金極度集中於<strong>半導體供應鏈、AI 伺服器與高階 PCB/ABF 載板</strong>四大族群：</p>
                <ul>
                    <li><strong>半導體板塊（7 檔）</strong>：包含台積電、聯發科、南亞科、聯電、華邦電、日月光投控與上櫃合晶。台積電單檔吸金 5,709 億佔 Top 20 的 20.3%。</li>
                    <li><strong>AI 伺服器與硬體代工</strong>：緯創（+24.82%）與鴻海（+10.04%）量價齊揚，反映市場對 AI 伺服器強勁需求。</li>
                    <li><strong>PCB / ABF / 銅箔基板</strong>：欣興（+12.85%）、南電、臻鼎-KY、台光電（+13.35%）及台燿受到高階伺服器材料拉貨帶動。</li>
                </ul>
            </div>

            <div class="analysis-card">
                <h3>🏆 近 5 日漲幅前 5 大強勢指標</h3>
                <p>前 20 大成交金額股中，最具波段爆發力的個股為：</p>
                <ul>
                    <li>🥇 <strong>3231 緯創 (+24.82%)</strong>：收盤價 $173.50，5 日狂吸 717 億元，短期資金凝聚力第一。</li>
                    <li>🥈 <strong>2454 聯發科 (+14.99%)</strong>：收盤價 $3,875.00，高價千金股帶頭領漲 IC 設計。</li>
                    <li>🥉 <strong>2383 台光電 (+13.35%)</strong>：收盤價 $5,095.00，銅箔基板出貨亮眼。</li>
                    <li>4️⃣ <strong>3037 欣興 (+12.85%)</strong>：ABF 載板量能顯著增溫。</li>
                    <li>5️⃣ <strong>2317 鴻海 (+10.04%)</strong>：重回 250 元大關之上。</li>
                </ul>
            </div>

            <div class="analysis-card">
                <h3>🏬 上市與上櫃市場比對</h3>
                <p>上市股票大獲全勝，但上櫃亦有兩大亮眼黑馬：</p>
                <ul>
                    <li><strong>上市 (TWSE) 18 檔</strong>：佔絕對主導地位，涵蓋絕大多數兆元與千億級權值股。</li>
                    <li><strong>上櫃 (TPEx) 2 檔</strong>：
                        <br>1. <strong>6182 合晶</strong> (第 13 名)：5 日總成交額達 828.9 億元，交易量突破 66 萬張。
                        <br>2. <strong>6274 台燿</strong> (第 18 名)：5 日總成交額達 671.1 億元，展現高單價 CCL 強勢追捧。
                    </li>
                </ul>
            </div>
        </div>

        <footer>
            <p>數據來源：臺灣證券交易所 (TWSE) 與 證券櫃檯買賣中心 (TPEx) 官方盤後公開數據 | 統計時間：2026/07/23</p>
        </footer>

    </div>

    <!-- JavaScript Interactive Code -->
    <script>
        function switchCard(num) {
            document.getElementById('card-img-1').style.display = num === 1 ? 'block' : 'none';
            document.getElementById('card-img-2').style.display = num === 2 ? 'block' : 'none';
            document.getElementById('card-img-3').style.display = num === 3 ? 'block' : 'none';

            const btns = document.querySelectorAll('.tab-btn');
            btns.forEach((btn, idx) => {
                if (idx === num - 1) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        }

        function filterTable() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('stockTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {
                const tdText = tr[i].textContent || tr[i].innerText;
                if (tdText.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                } else {
                    tr[i].style.display = "none";
                }
            }
        }
    </script>
</body>
</html>
"""

# Save to 2026-07-23.html and 20260723.html
html_path1 = os.path.join(OUTPUT_DIR, "2026-07-23.html")
html_path2 = os.path.join(OUTPUT_DIR, "20260723.html")

with open(html_path1, 'w', encoding='utf-8') as f:
    f.write(html_content)

with open(html_path2, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Successfully generated standalone HTML report at:\n - {html_path1}\n - {html_path2}")
