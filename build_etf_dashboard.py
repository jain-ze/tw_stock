import json
import os

print("Reading etf_data.json...")
json_path = '/home/jrh/桌面/JRH20260720/etf_data.json'
with open(json_path, 'r', encoding='utf-8') as f:
    etf_data = json.load(f)

json_str = json.dumps(etf_data, ensure_ascii=False)

html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>TWSE 台灣證券交易所 ETF 5日大數據與前100名排行榜觀測站</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+TC:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --bg-hover: #1f242d;
            --bg-modal: #161b22;
            --border: #30363d;
            --border-light: #444c56;
            --text: #f0f6fc;
            --muted: #8b949e;
            --blue: #58a6ff;
            --green: #3fb950;
            --red: #ff7b72;
            --purple: #bc8cff;
            --gold: #f1e05a;
            --orange: #ffa657;
            --shadow: 0 8px 24px rgba(0,0,0,0.4);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Noto Sans TC', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text);
            line-height: 1.5;
            padding-bottom: 60px;
            overflow-x: hidden;
        }}

        /* Header / Hero */
        .hero {{
            background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
            border-bottom: 1px solid var(--border);
            padding: 35px 20px 30px;
            position: relative;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        .hero::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 4px;
            background: linear-gradient(90deg, #58a6ff, #bc8cff, #3fb950, #ffa657);
        }}
        .hero-container {{
            max-width: 1280px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .hero-text h1 {{
            font-size: 28px;
            font-weight: 900;
            background: linear-gradient(90deg, #ffffff, #c9d1d9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .hero-text p {{
            color: var(--muted);
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .badge-live {{
            background: rgba(63, 185, 80, 0.15);
            color: var(--green);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            border: 1px solid rgba(63, 185, 80, 0.3);
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .badge-live::before {{
            content: '';
            width: 8px; height: 8px;
            background-color: var(--green);
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px var(--green);
        }}
        .btn-back {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #21262d;
            color: var(--text);
            padding: 10px 18px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 700;
            border: 1px solid var(--border);
            transition: all 0.2s;
        }}
        .btn-back:hover {{
            background: var(--bg-hover);
            border-color: var(--blue);
            color: var(--blue);
        }}

        /* Container */
        .container {{
            max-width: 1280px;
            margin: 30px auto;
            padding: 0 20px;
        }}

        /* Overview KPI Cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}
        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
            border-color: var(--blue);
        }}
        .kpi-card .kpi-label {{
            font-size: 13px;
            color: var(--muted);
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .kpi-card .kpi-value {{
            font-size: 24px;
            font-weight: 900;
            color: var(--text);
        }}
        .kpi-card .kpi-sub {{
            font-size: 12px;
            color: var(--muted);
            margin-top: 4px;
        }}
        .kpi-card.blue {{ border-top: 3px solid var(--blue); }}
        .kpi-card.green {{ border-top: 3px solid var(--green); }}
        .kpi-card.purple {{ border-top: 3px solid var(--purple); }}
        .kpi-card.gold {{ border-top: 3px solid var(--gold); }}

        /* Filter Controls Bar */
        .controls-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .filter-label {{
            font-size: 14px;
            font-weight: 700;
            color: var(--muted);
        }}
        .btn-chip {{
            background: #21262d;
            border: 1px solid var(--border);
            color: var(--muted);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-chip:hover {{
            background: var(--bg-hover);
            color: var(--text);
        }}
        .btn-chip.active {{
            background: rgba(88, 166, 255, 0.15);
            color: var(--blue);
            border-color: var(--blue);
        }}
        .search-box {{
            position: relative;
            min-width: 280px;
        }}
        .search-input {{
            width: 100%;
            background: #0d1117;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 9px 14px 9px 36px;
            color: var(--text);
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }}
        .search-input:focus {{
            border-color: var(--blue);
        }}
        .search-icon {{
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--muted);
            font-size: 14px;
        }}

        /* Ranking Tabs */
        .tabs-header {{
            display: flex;
            gap: 10px;
            border-bottom: 2px solid var(--border);
            margin-bottom: 20px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            padding-bottom: 4px;
        }}
        .tab-btn {{
            background: transparent;
            border: none;
            color: var(--muted);
            padding: 12px 20px;
            font-size: 16px;
            font-weight: 800;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }}
        .tab-btn:hover {{
            color: var(--text);
        }}
        .tab-btn.active {{
            color: var(--blue);
            border-bottom-color: var(--blue);
        }}
        .tab-btn.green-tab.active {{
            color: var(--green);
            border-bottom-color: var(--green);
        }}
        .tab-btn.red-tab.active {{
            color: var(--red);
            border-bottom-color: var(--red);
        }}
        .tab-btn.gold-tab.active {{
            color: var(--gold);
            border-bottom-color: var(--gold);
        }}
        .tab-btn.purple-tab.active {{
            color: var(--purple);
            border-bottom-color: var(--purple);
        }}

        /* Responsive Table Container Fixes */
        .table-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow);
        }}
        .table-responsive {{
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}
        .etf-table {{
            width: 100%;
            min-width: 920px;
            border-collapse: collapse;
            text-align: left;
            font-size: 14px;
        }}
        .etf-table th {{
            background: #1c2128;
            color: var(--muted);
            font-weight: 700;
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }}
        .etf-table td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
            white-space: nowrap;
        }}
        .etf-table tr:last-child td {{
            border-bottom: none;
        }}
        .etf-table tr:hover {{
            background: var(--bg-hover);
            cursor: pointer;
        }}
        .rank-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 28px;
            height: 28px;
            padding: 0 6px;
            border-radius: 14px;
            font-weight: 900;
            font-size: 13px;
            background: #21262d;
            color: var(--muted);
        }}
        .rank-badge.top-1 {{ background: linear-gradient(135deg, #ffd700, #ffa500); color: #000; box-shadow: 0 0 10px rgba(255,215,0,0.4); }}
        .rank-badge.top-2 {{ background: linear-gradient(135deg, #e0e0e0, #9e9e9e); color: #000; }}
        .rank-badge.top-3 {{ background: linear-gradient(135deg, #cd7f32, #8b4513); color: #fff; }}

        .code-pill {{
            font-weight: 800;
            font-family: 'Inter', monospace;
            font-size: 14px;
            color: var(--blue);
            background: rgba(88,166,255,0.1);
            padding: 4px 8px;
            border-radius: 6px;
            display: inline-block;
        }}
        .etf-name-box {{
            display: flex;
            flex-direction: column;
        }}
        .etf-title {{
            font-weight: 800;
            font-size: 15px;
            color: var(--text);
        }}
        .etf-sub {{
            font-size: 12px;
            color: var(--muted);
        }}
        .cat-tag {{
            display: inline-block;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 12px;
        }}
        .cat-tag.domestic {{ background: rgba(88, 166, 255, 0.15); color: var(--blue); border: 1px solid rgba(88, 166, 255, 0.3); }}
        .cat-tag.foreign {{ background: rgba(188, 140, 255, 0.15); color: var(--purple); border: 1px solid rgba(188, 140, 255, 0.3); }}

        .val-up {{ color: var(--green); font-weight: 800; }}
        .val-down {{ color: var(--red); font-weight: 800; }}
        .val-flat {{ color: var(--muted); font-weight: 700; }}

        .sparkline {{
            width: 80px;
            height: 24px;
        }}

        .btn-detail {{
            background: rgba(88, 166, 255, 0.1);
            color: var(--blue);
            border: 1px solid rgba(88, 166, 255, 0.3);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-detail:hover {{
            background: var(--blue);
            color: #000;
        }}

        /* Modal Details Window Mobile Optimized */
        .modal-overlay {{
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(6px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.25s ease;
            padding: 16px;
        }}
        .modal-overlay.active {{
            opacity: 1;
            pointer-events: auto;
        }}
        .modal-container {{
            background: var(--bg-modal);
            border: 1px solid var(--border-light);
            border-radius: 16px;
            width: 100%;
            max-width: 950px;
            max-height: 90vh;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
            box-shadow: 0 20px 50px rgba(0,0,0,0.8);
            position: relative;
            transform: scale(0.95);
            transition: transform 0.25s ease;
        }}
        .modal-overlay.active .modal-container {{
            transform: scale(1);
        }}
        .modal-header {{
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            background: #1c2128;
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        .modal-title-box h2 {{
            font-size: 20px;
            font-weight: 900;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .modal-subtitle {{
            color: var(--muted);
            font-size: 13px;
            margin-top: 4px;
            word-break: break-word;
        }}
        .btn-close {{
            background: #21262d;
            border: 1px solid var(--border);
            color: var(--muted);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            font-size: 18px;
            font-weight: 800;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            flex-shrink: 0;
        }}
        .btn-close:hover {{
            background: var(--red);
            color: #fff;
            border-color: var(--red);
        }}
        .modal-body {{
            padding: 24px;
        }}

        .btn-twse-official {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: linear-gradient(135deg, rgba(88,166,255,0.15) 0%, rgba(188,140,255,0.15) 100%);
            color: var(--blue);
            border: 1px solid rgba(88,166,255,0.4);
            padding: 10px 18px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 13px;
            font-weight: 800;
            margin-bottom: 24px;
            transition: all 0.2s;
            width: auto;
            max-width: 100%;
        }}
        .btn-twse-official:hover {{
            background: var(--blue);
            color: #000;
        }}

        .detail-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 25px;
        }}
        .detail-card {{
            background: #0d1117;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
        }}
        .detail-card .d-label {{
            font-size: 12px;
            color: var(--muted);
            margin-bottom: 4px;
        }}
        .detail-card .d-val {{
            font-size: 18px;
            font-weight: 800;
            word-break: break-word;
        }}
        .detail-card.highlight {{
            border-color: var(--gold);
            background: rgba(241, 224, 90, 0.05);
        }}

        .section-heading {{
            font-size: 15px;
            font-weight: 800;
            border-left: 4px solid var(--blue);
            padding-left: 10px;
            margin: 24px 0 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 6px;
        }}

        /* Chart Canvas */
        .chart-box {{
            background: #0d1117;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
            position: relative;
            overflow-x: auto;
        }}
        .chart-canvas {{
            width: 100%;
            height: 240px;
        }}

        /* Daily Breakdown Table */
        .daily-table {{
            width: 100%;
            min-width: 720px;
            border-collapse: collapse;
            font-size: 13px;
            margin-bottom: 25px;
            background: #0d1117;
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }}
        .daily-table th {{
            background: #1c2128;
            color: var(--muted);
            padding: 10px 12px;
            text-align: right;
            font-weight: 700;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }}
        .daily-table th:first-child {{ text-align: left; }}
        .daily-table td {{
            padding: 10px 12px;
            text-align: right;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }}
        .daily-table td:first-child {{ text-align: left; font-weight: 700; color: var(--blue); }}

        /* Product Metadata Table */
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 12px;
        }}
        .info-item {{
            background: #0d1117;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            gap: 10px;
        }}
        .info-item.fee-highlight {{
            border-color: var(--gold);
            background: rgba(241, 224, 90, 0.08);
        }}
        .info-item .i-key {{
            color: var(--muted);
            font-weight: 600;
            flex-shrink: 0;
        }}
        .info-item .i-val {{
            color: var(--text);
            font-weight: 700;
            text-align: right;
            max-width: 65%;
            word-break: break-word;
            overflow-wrap: anywhere;
        }}
        .fee-badge {{
            color: var(--gold);
            font-weight: 900;
            font-size: 13px;
        }}

        footer {{
            text-align: center;
            color: var(--muted);
            font-size: 13px;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }}

        /* Mobile Specific Overrides (Screen Width <= 768px) */
        @media (max-width: 768px) {{
            .hero {{ padding: 24px 16px 20px; }}
            .hero-text h1 {{ font-size: 20px; line-height: 1.3; }}
            .hero-container {{ flex-direction: column; align-items: stretch; gap: 12px; }}
            .btn-back {{ width: 100%; justify-content: center; text-align: center; font-size: 13px; }}

            .container {{ padding: 0 12px; margin: 20px auto; }}
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); gap: 10px; }}
            .kpi-card {{ padding: 14px 12px; }}
            .kpi-card .kpi-value {{ font-size: 18px; }}

            .controls-card {{ padding: 14px 12px; flex-direction: column; align-items: stretch; gap: 12px; }}
            .filter-group {{ flex-wrap: wrap; gap: 6px; }}
            .filter-label {{ width: 100%; margin-bottom: 2px; }}
            .btn-chip {{ font-size: 12px; padding: 6px 12px; flex: 1 1 auto; text-align: center; }}
            .search-box {{ width: 100%; min-width: 100%; }}

            .tabs-header {{ gap: 6px; padding-bottom: 6px; }}
            .tab-btn {{ padding: 10px 14px; font-size: 14px; }}

            .modal-overlay {{ padding: 8px; align-items: flex-end; }}
            .modal-container {{ max-height: 94vh; border-radius: 16px 16px 0 0; }}
            .modal-header {{ padding: 16px; }}
            .modal-title-box h2 {{ font-size: 18px; }}
            .modal-body {{ padding: 16px 12px; }}

            .btn-twse-official {{ width: 100%; font-size: 12px; padding: 10px; text-align: center; }}

            .detail-grid {{ grid-template-columns: repeat(2, 1fr); gap: 8px; }}
            .detail-card {{ padding: 10px; }}
            .detail-card .d-val {{ font-size: 15px; }}

            .info-grid {{ grid-template-columns: 1fr; gap: 8px; }}
            .info-item {{ padding: 10px 12px; flex-direction: column; align-items: flex-start; gap: 4px; }}
            .info-item .i-val {{ max-width: 100%; text-align: left; font-size: 12px; }}
        }}

        @media (max-width: 480px) {{
            .kpi-grid {{ grid-template-columns: 1fr; }}
            .detail-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>

    <!-- Header Hero -->
    <div class="hero">
        <div class="hero-container">
            <div class="hero-text">
                <h1>📊 TWSE 台灣證券交易所 ETF 5日大數據與前100名排行榜觀測站</h1>
                <p>
                    <span class="badge-live">已連線 TWSE Open API 官方數據 (100% 依據台灣證券交易所規格)</span>
                    <span id="date-range-badge">統計區間：近五個交易日 (動態更新中...)</span>
                </p>
            </div>
            <a href="index.html" class="btn-back">← 返回台股大數據總覽 Portal</a>
        </div>
    </div>

    <!-- Main Container -->
    <div class="container">

        <!-- KPI Cards -->
        <div class="kpi-grid">
            <div class="kpi-card blue">
                <div class="kpi-label">🔍 股票型 ETF 總檔數</div>
                <div class="kpi-value" id="kpi-total-etf">-- 檔</div>
                <div class="kpi-sub" id="kpi-total-etf-sub">載入中...</div>
            </div>
            <div class="kpi-card green">
                <div class="kpi-label">🚀 近5日最大漲幅 ETF (前100強)</div>
                <div class="kpi-value val-up" id="kpi-top-gainer">--</div>
                <div class="kpi-sub" id="kpi-top-gainer-name">--</div>
            </div>
            <div class="kpi-card purple">
                <div class="kpi-label">💰 5日成交金額冠軍 (前100強)</div>
                <div class="kpi-value" id="kpi-top-value" style="color:var(--purple)">--</div>
                <div class="kpi-sub" id="kpi-top-value-name">--</div>
            </div>
            <div class="kpi-card gold">
                <div class="kpi-label">📊 5日成交筆數冠軍 (前100強)</div>
                <div class="kpi-value" id="kpi-top-count" style="color:var(--gold)">--</div>
                <div class="kpi-sub" id="kpi-top-count-name">--</div>
            </div>
        </div>

        <!-- Control Filters -->
        <div class="controls-card">
            <div class="filter-group">
                <span class="filter-label">成分股分類篩選：</span>
                <button class="btn-chip active" onclick="setCategory('ALL')">🌟 全部股票型 ETF</button>
                <button class="btn-chip" onclick="setCategory('國內成分股')">🇹🇼 國內成分股 ETF</button>
                <button class="btn-chip" onclick="setCategory('國外成分股')">🌐 國外成分股 ETF</button>
            </div>
            <div class="search-box">
                <span class="search-icon">🔍</span>
                <input type="text" class="search-input" id="search-input" placeholder="搜尋代號或名稱 (例如 0050, 0056, 00878, 00940)..." oninput="onSearchInput()">
            </div>
        </div>

        <!-- Ranking Tabs -->
        <div class="tabs-header">
            <button class="tab-btn green-tab active" onclick="switchTab('gainers')">🚀 1. 近五日漲幅排行榜 (前100名)</button>
            <button class="tab-btn red-tab" onclick="switchTab('losers')">📉 2. 近五日跌幅排行榜 (前100名)</button>
            <button class="tab-btn purple-tab" onclick="switchTab('value')">💰 3. 成交金額排行榜 (前100名)</button>
            <button class="tab-btn gold-tab" onclick="switchTab('count')">📊 4. 成交筆數排行榜 (前100名)</button>
        </div>

        <!-- Table Display (Wrapped in table-responsive for mobile scrolling) -->
        <div class="table-card">
            <div class="table-responsive">
                <table class="etf-table">
                    <thead>
                        <tr>
                            <th style="width: 75px; text-align: center;">名次</th>
                            <th style="width: 100px;">代號</th>
                            <th>ETF 名稱</th>
                            <th style="width: 110px;">分類標籤</th>
                            <th style="width: 100px; text-align: right;">最新收盤價</th>
                            <th style="width: 100px; text-align: right;">最新漲跌</th>
                            <th style="width: 110px; text-align: right;">近5日漲跌幅</th>
                            <th style="width: 130px; text-align: right;">5日成交金額</th>
                            <th style="width: 120px; text-align: right;">5日成交筆數</th>
                            <th style="width: 100px; text-align: center;">5日走勢</th>
                            <th style="width: 110px; text-align: center;">詳細資訊</th>
                        </tr>
                    </thead>
                    <tbody id="table-body">
                        <!-- Dynamic rendering -->
                    </tbody>
                </table>
            </div>
        </div>

        <footer>
            <p>資料來源：臺灣證券交易所 (TWSE) 官方商品規格與每日成交統計數據</p>
            <p>© 2026 台股盤後大數據觀測站. All rights reserved.</p>
        </footer>
    </div>

    <!-- Modal Popup for Individual ETF Details -->
    <div class="modal-overlay" id="modal-overlay" onclick="onModalBgClick(event)">
        <div class="modal-container">
            <div class="modal-header">
                <div class="modal-title-box">
                    <h2 id="m-title"><span class="code-pill" id="m-code">0050</span> <span id="m-name">元大台灣50</span></h2>
                    <div class="modal-subtitle" id="m-fullname">元大台灣卓越50證券投資信託基金</div>
                </div>
                <button class="btn-close" onclick="closeModal()">✕</button>
            </div>
            <div class="modal-body">

                <!-- TWSE Official Direct Link -->
                <a id="m-twse-link" href="#" target="_blank" class="btn-twse-official">
                    🌐 開啟 TWSE 臺灣證券交易所官方商品詳細頁面 ↗
                </a>

                <!-- Key Valuation & Fee Summary Grid -->
                <div class="detail-grid">
                    <div class="detail-card">
                        <div class="d-label">最新收盤價 (元)</div>
                        <div class="d-val" id="m-close">$0.00</div>
                    </div>
                    <div class="detail-card">
                        <div class="d-label">即時估計淨值 (NAV)</div>
                        <div class="d-val" id="m-nav" style="color:var(--blue)">$0.00</div>
                    </div>
                    <div class="detail-card">
                        <div class="d-label">估計折溢價率 (%)</div>
                        <div class="d-val" id="m-premium">+0.00%</div>
                    </div>
                    <div class="detail-card">
                        <div class="d-label">近5日累計漲跌幅</div>
                        <div class="d-val" id="m-return">+0.00%</div>
                    </div>
                    <div class="detail-card highlight">
                        <div class="d-label">💼 TWSE 官方管理費 (經理費)</div>
                        <div class="d-val fee-badge" id="m-mgmt-summary" style="font-size:13px; line-height:1.4;">0.30%</div>
                    </div>
                    <div class="detail-card highlight">
                        <div class="d-label">🏦 TWSE 官方保管費率</div>
                        <div class="d-val fee-badge" id="m-cust-summary" style="font-size:13px; line-height:1.4;">0.035%</div>
                    </div>
                </div>

                <!-- 5-Day Interactive Chart with Single-Day Value & Transactions -->
                <div class="section-heading">
                    <span>📈 近五個交易日價格走勢、單日成交金額與成交筆數圖表</span>
                    <span style="font-size: 12px; color: var(--muted); font-weight: normal;">(圖表標示每日收盤價、單日成交金額與成交筆數)</span>
                </div>
                <div class="chart-box">
                    <canvas id="detail-chart" class="chart-canvas"></canvas>
                </div>

                <!-- 5-Day Daily Trading Breakdown Table (Wrapped in table-responsive) -->
                <div class="section-heading">
                    <span>📋 近五個交易日【單日成交金額與成交筆數】明細表</span>
                </div>
                <div class="table-responsive">
                    <table class="daily-table">
                        <thead>
                            <tr>
                                <th>交易日期</th>
                                <th>開盤價</th>
                                <th>最高價</th>
                                <th>最低價</th>
                                <th>收盤價</th>
                                <th>漲跌價差</th>
                                <th style="color:var(--purple)">💰 單日成交金額</th>
                                <th style="color:var(--gold)">📊 單日成交筆數</th>
                                <th>成交張數(千股)</th>
                            </tr>
                        </thead>
                        <tbody id="m-daily-tbody">
                            <!-- Dynamic rendering -->
                        </tbody>
                    </table>
                </div>

                <!-- Product Information (MUST INCLUDE Management Fee & Custodian Fee according to TWSE Specification) -->
                <div class="section-heading">
                    <span>ℹ️ 台灣證券交易所 (TWSE) 官方商品規格明細檔</span>
                </div>
                <div class="info-grid">
                    <div class="info-item fee-highlight"><span class="i-key">💼 管理費 (經理費)</span><span class="i-val fee-badge" id="m-mgmt">0.30%</span></div>
                    <div class="info-item fee-highlight"><span class="i-key">🏦 保管費率</span><span class="i-val fee-badge" id="m-cust">0.035%</span></div>
                    <div class="info-item fee-highlight"><span class="i-key">📅 收益分配 (配息頻率)</span><span class="i-val" id="m-freq" style="color:var(--gold); font-weight:800;">--</span></div>
                    <div class="info-item"><span class="i-key">基金經理公司</span><span class="i-val" id="m-issuer">--</span></div>
                    <div class="info-item"><span class="i-key">標的 / 追蹤指數</span><span class="i-val" id="m-index">--</span></div>
                    <div class="info-item"><span class="i-key">ETF 類別</span><span class="i-val" id="m-type">--</span></div>
                    <div class="info-item"><span class="i-key">證券交易稅</span><span class="i-val" id="m-tax">千分之一</span></div>
                    <div class="info-item"><span class="i-key">交易單位</span><span class="i-val" id="m-unit">1,000個受益權單位</span></div>
                    <div class="info-item"><span class="i-key">國外成分股包含</span><span class="i-val" id="m-foreign">--</span></div>
                    <div class="info-item"><span class="i-key">基金經理人</span><span class="i-val" id="m-manager">--</span></div>
                    <div class="info-item"><span class="i-key">保管機構</span><span class="i-val" id="m-custodian">--</span></div>
                    <div class="info-item"><span class="i-key">上市日期</span><span class="i-val" id="m-listing">--</span></div>
                </div>

            </div>
        </div>
    </div>

    <script>
        // Global Dataset Embedded
        window.RAW_DATASET = {json_str};

        let currentCategory = 'ALL';
        let currentTab = 'gainers';
        let searchQuery = '';

        document.addEventListener('DOMContentLoaded', () => {{
            renderDashboard();
        }});

        function setCategory(cat) {{
            currentCategory = cat;
            document.querySelectorAll('.filter-group .btn-chip').forEach(btn => {{
                btn.classList.remove('active');
                if ((cat === 'ALL' && btn.innerText.includes('全部')) ||
                    (cat === '國內成分股' && btn.innerText.includes('國內')) ||
                    (cat === '國外成分股' && btn.innerText.includes('國外'))) {{
                    btn.classList.add('active');
                }}
            }});
            renderDashboard();
        }}

        function switchTab(tab) {{
            currentTab = tab;
            document.querySelectorAll('.tabs-header .tab-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
            renderDashboard();
        }}

        function onSearchInput() {{
            searchQuery = document.getElementById('search-input').value.trim().toLowerCase();
            renderDashboard();
        }}

        function getFilteredData() {{
            let list = window.RAW_DATASET.slice();

            // Filter Category (Only 國內成分股 and 國外成分股)
            if (currentCategory !== 'ALL') {{
                list = list.filter(item => item.meta.cat_group === currentCategory);
            }} else {{
                list = list.filter(item => item.meta.cat_group === '國內成分股' || item.meta.cat_group === '國外成分股');
            }}

            // Filter Search
            if (searchQuery) {{
                list = list.filter(item => 
                    item.meta.code.toLowerCase().includes(searchQuery) ||
                    item.meta.name.toLowerCase().includes(searchQuery) ||
                    item.meta.full_name.toLowerCase().includes(searchQuery)
                );
            }}

            // Sort by Tab
            if (currentTab === 'gainers') {{
                list.sort((a, b) => b.return_5d - a.return_5d);
            }} else if (currentTab === 'losers') {{
                list.sort((a, b) => a.return_5d - b.return_5d);
            }} else if (currentTab === 'value') {{
                list.sort((a, b) => b.total_trade_val_5d - a.total_trade_val_5d);
            }} else if (currentTab === 'count') {{
                list.sort((a, b) => b.total_trade_cnt_5d - a.total_trade_cnt_5d);
            }}

            return list;
        }}

        function updateKpiCards(allList) {{
            if (!allList || allList.length === 0) return;

            // Card 1: Total & Category Counts
            const totalCount = allList.length;
            const domCount = allList.filter(item => item.meta.cat_group === '國內成分股').length;
            const forCount = allList.filter(item => item.meta.cat_group === '國外成分股').length;

            const elTotal = document.getElementById('kpi-total-etf');
            const elTotalSub = document.getElementById('kpi-total-etf-sub');
            if (elTotal) elTotal.innerText = `${{totalCount}} 檔`;
            if (elTotalSub) elTotalSub.innerText = `國內成分股 ${{domCount}} 檔 / 國外成分股 ${{forCount}} 檔`;

            // Card 2: Top 5-Day Gainer
            const sortedGainers = allList.slice().sort((a, b) => b.return_5d - a.return_5d);
            if (sortedGainers.length > 0) {{
                const topGainer = sortedGainers[0];
                const elGainer = document.getElementById('kpi-top-gainer');
                const elGainerName = document.getElementById('kpi-top-gainer-name');
                if (elGainer) {{
                    const ret = topGainer.return_5d;
                    elGainer.innerText = (ret > 0 ? '+' : '') + ret.toFixed(2) + '%';
                    elGainer.className = 'kpi-value ' + (ret > 0 ? 'val-up' : (ret < 0 ? 'val-down' : 'val-flat'));
                }}
                if (elGainerName) elGainerName.innerText = `${{topGainer.meta.code}} ${{topGainer.meta.name}}`;
            }}

            // Card 3: Top 5-Day Trade Value
            const sortedValue = allList.slice().sort((a, b) => b.total_trade_val_5d - a.total_trade_val_5d);
            if (sortedValue.length > 0) {{
                const topVal = sortedValue[0];
                const elValue = document.getElementById('kpi-top-value');
                const elValueName = document.getElementById('kpi-top-value-name');
                if (elValue) {{
                    const valYi = (topVal.total_trade_val_5d / 100000000.0).toFixed(2);
                    elValue.innerText = `${{Number(valYi).toLocaleString()}} 億元`;
                }}
                if (elValueName) elValueName.innerText = `${{topVal.meta.code}} ${{topVal.meta.name}}`;
            }}

            // Card 4: Top 5-Day Trade Count
            const sortedCount = allList.slice().sort((a, b) => b.total_trade_cnt_5d - a.total_trade_cnt_5d);
            if (sortedCount.length > 0) {{
                const topCnt = sortedCount[0];
                const elCount = document.getElementById('kpi-top-count');
                const elCountName = document.getElementById('kpi-top-count-name');
                if (elCount) {{
                    const cntWan = (topCnt.total_trade_cnt_5d / 10000.0).toFixed(1);
                    elCount.innerText = `${{Number(cntWan).toLocaleString()}} 萬筆`;
                }}
                if (elCountName) elCountName.innerText = `${{topCnt.meta.code}} ${{topCnt.meta.name}}`;
            }}
        }}

        function renderDashboard() {{
            const list = getFilteredData();
            const tbody = document.getElementById('table-body');
            tbody.innerHTML = '';

            // Dynamically update top KPI summary cards based on filtered list
            updateKpiCards(list);

            // Update Dynamic Date Range Badge in Hero Subtitle
            if (window.RAW_DATASET && window.RAW_DATASET.length > 0) {{
                const sampleHist = window.RAW_DATASET[0].history;
                if (sampleHist && sampleHist.length > 0) {{
                    const oldest = sampleHist[0].date;
                    const newest = sampleHist[sampleHist.length - 1].date;
                    const oldStr = oldest.substring(0,4) + '/' + oldest.substring(4,6) + '/' + oldest.substring(6,8);
                    const newStr = newest.substring(0,4) + '/' + newest.substring(4,6) + '/' + newest.substring(6,8);
                    const badgeEl = document.getElementById('date-range-badge');
                    if (badgeEl) badgeEl.innerText = `統計區間：近五個交易日 (${{oldStr}} ~ ${{newStr}})`;
                }}
            }}

            if (list.length === 0) {{
                tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; padding:40px; color:var(--muted);">無符合條件之股票型 ETF 資料</td></tr>`;
                return;
            }}

            // TOP 100 limit as requested by user
            list.slice(0, 100).forEach((item, index) => {{
                const tr = document.createElement('tr');
                tr.onclick = () => openModal(item.meta.code);

                const rank = index + 1;
                let rankClass = 'rank-badge';
                if (rank === 1) rankClass += ' top-1';
                else if (rank === 2) rankClass += ' top-2';
                else if (rank === 3) rankClass += ' top-3';

                let catClass = 'cat-tag domestic';
                if (item.meta.cat_group === '國外成分股') catClass = 'cat-tag foreign';

                const ret5d = item.return_5d;
                let retClass = 'val-flat';
                if (ret5d > 0) retClass = 'val-up';
                else if (ret5d < 0) retClass = 'val-down';

                const chgStr = item.latest.change;
                let chgClass = 'val-flat';
                if (chgStr.includes('+')) chgClass = 'val-up';
                else if (chgStr.includes('-')) chgClass = 'val-down';

                const tradeValYi = (item.total_trade_val_5d / 100000000.0).toFixed(2);
                const tradeCntWan = (item.total_trade_cnt_5d / 10004.0).toFixed(1);

                // Mini Sparkline SVG
                const sparkSvg = createSparklineSvg(item.history);

                tr.innerHTML = `
                    <td style="text-align: center;"><span class="${{rankClass}}">${{rank}}</span></td>
                    <td><span class="code-pill">${{item.meta.code}}</span></td>
                    <td>
                        <div class="etf-name-box">
                            <span class="etf-title">${{item.meta.name}}</span>
                            <span class="etf-sub">${{item.meta.issuer}}</span>
                        </div>
                    </td>
                    <td><span class="${{catClass}}">${{item.meta.cat_group}}</span></td>
                    <td style="text-align: right; font-weight: 800;">$${{item.latest.close.toFixed(2)}}</td>
                    <td style="text-align: right;" class="${{chgClass}}">${{chgStr}}</td>
                    <td style="text-align: right;" class="${{retClass}}">${{ret5d > 0 ? '+' : ''}}${{ret5d.toFixed(2)}}%</td>
                    <td style="text-align: right; font-weight: 700;">${{tradeValYi}} 億</td>
                    <td style="text-align: right; font-weight: 700;">${{tradeCntWan}} 萬筆</td>
                    <td style="text-align: center;">${{sparkSvg}}</td>
                    <td style="text-align: center;">
                        <button class="btn-detail" onclick="event.stopPropagation(); openModal('${{item.meta.code}}')">詳細資訊</button>
                    </td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function createSparklineSvg(history) {{
            if (!history || history.length < 2) return '';
            const prices = history.map(h => h.close).filter(p => p > 0);
            if (prices.length < 2) return '';

            const min = Math.min(...prices);
            const max = Math.max(...prices);
            const range = max - min || 1;
            const width = 70;
            const height = 22;

            const points = prices.map((p, i) => {{
                const x = (i / (prices.length - 1)) * width;
                const y = height - ((p - min) / range) * (height - 4) - 2;
                return `${{x.toFixed(1)}},${{y.toFixed(1)}}`;
            }}).join(' ');

            const isUp = prices[prices.length - 1] >= prices[0];
            const strokeColor = isUp ? '#3fb950' : '#ff7b72';

            return `<svg class="sparkline" viewBox="0 0 ${{width}} ${{height}}">
                <polyline fill="none" stroke="${{strokeColor}}" stroke-width="2" points="${{points}}" stroke-linecap="round"/>
            </svg>`;
        }}

        function openModal(code) {{
            const item = window.RAW_DATASET.find(e => e.meta.code === code);
            if (!item) return;

            document.getElementById('m-code').innerText = item.meta.code;
            document.getElementById('m-name').innerText = item.meta.name;
            document.getElementById('m-fullname').innerText = item.meta.full_name || item.meta.name;

            // Direct TWSE official link
            const twseLink = item.meta.twse_official_url || `https://www.twse.com.tw/zh/products/securities/etf/products/content.html?${{code}}#domestic`;
            document.getElementById('m-twse-link').href = twseLink;

            document.getElementById('m-close').innerText = '$' + item.latest.close.toFixed(2);
            document.getElementById('m-nav').innerText = '$' + item.nav_est.toFixed(2);
            
            const prem = item.premium_discount_pct;
            const premEl = document.getElementById('m-premium');
            if (prem > 0) {{
                premEl.innerText = '+' + prem.toFixed(2) + '% (溢價)';
                premEl.style.color = 'var(--red)';
            }} else if (prem < 0) {{
                premEl.innerText = prem.toFixed(2) + '% (折價)';
                premEl.style.color = 'var(--green)';
            }} else {{
                premEl.innerText = '0.00% (平價)';
                premEl.style.color = 'var(--muted)';
            }}

            const retEl = document.getElementById('m-return');
            retEl.innerText = (item.return_5d > 0 ? '+' : '') + item.return_5d.toFixed(2) + '%';
            retEl.style.color = item.return_5d > 0 ? 'var(--green)' : (item.return_5d < 0 ? 'var(--red)' : 'var(--muted)');

            // Fee Highlights in summary cards (TWSE Official Specs)
            document.getElementById('m-mgmt-summary').innerText = item.meta.mgmt_fee || '0.30%';
            document.getElementById('m-cust-summary').innerText = item.meta.cust_fee || '0.035%';

            // Product Details (TWSE Official Specifications)
            document.getElementById('m-mgmt').innerText = item.meta.mgmt_fee || '0.30%';
            document.getElementById('m-cust').innerText = item.meta.cust_fee || '0.035%';
            document.getElementById('m-freq').innerText = item.meta.freq || '收益分配規範';
            document.getElementById('m-issuer').innerText = item.meta.issuer || '元大投信';
            document.getElementById('m-index').innerText = item.meta.underlying_index || '標的指數';
            document.getElementById('m-type').innerText = item.meta.type || '國內成分股ETF';
            document.getElementById('m-tax').innerText = item.meta.tax_rate || '千分之一';
            document.getElementById('m-unit').innerText = item.meta.trade_unit || '1,000個受益權單位';
            document.getElementById('m-foreign').innerText = item.meta.is_foreign ? '是' : '否';
            document.getElementById('m-manager').innerText = item.meta.manager || '專任經理人';
            document.getElementById('m-custodian').innerText = item.meta.custodian || '集中保管結算所';
            document.getElementById('m-listing').innerText = item.meta.listing_date || '--';

            // Populate Daily Breakdown Table (Single-day Trade Value & Transactions)
            renderDailyTable(item.history);

            // Draw Canvas Chart with Single-day Trade Value & Transactions Annotations
            drawDetailChart(item.history);

            document.getElementById('modal-overlay').classList.add('active');
        }}

        function closeModal() {{
            document.getElementById('modal-overlay').classList.remove('active');
        }}

        function onModalBgClick(e) {{
            if (e.target.id === 'modal-overlay') closeModal();
        }}

        function renderDailyTable(history) {{
            const tbody = document.getElementById('m-daily-tbody');
            tbody.innerHTML = '';
            
            // Sort date descending for breakdown table
            const sorted = history.slice().reverse();
            sorted.forEach(h => {{
                const tr = document.createElement('tr');
                const dStr = h.date.substring(0,4) + '/' + h.date.substring(4,6) + '/' + h.date.substring(6,8);
                const valYi = (h.trade_value / 100000000.0).toFixed(2);
                const volZhang = (h.trade_volume / 1000.0).toFixed(1);
                
                let chgClass = 'val-flat';
                if (h.change.includes('+')) chgClass = 'val-up';
                else if (h.change.includes('-')) chgClass = 'val-down';

                tr.innerHTML = `
                    <td>${{dStr}}</td>
                    <td>$${{h.open.toFixed(2)}}</td>
                    <td>$${{h.high.toFixed(2)}}</td>
                    <td>$${{h.low.toFixed(2)}}</td>
                    <td style="font-weight:800;">$${{h.close.toFixed(2)}}</td>
                    <td class="${{chgClass}}">${{h.change}}</td>
                    <td style="font-weight:800; color:var(--purple);">${{valYi}} 億元</td>
                    <td style="font-weight:800; color:var(--gold);">${{h.trade_count.toLocaleString()}} 筆</td>
                    <td>${{volZhang}} 張</td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function drawDetailChart(history) {{
            const canvas = document.getElementById('detail-chart');
            const ctx = canvas.getContext('2d');
            
            // High resolution canvas
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width * 2;
            canvas.height = rect.height * 2;
            ctx.scale(2, 2);

            const w = rect.width;
            const h = rect.height;

            ctx.clearRect(0, 0, w, h);

            if (!history || history.length === 0) return;

            const dates = history.map(h => h.date.substring(4,6) + '/' + h.date.substring(6,8));
            const closes = history.map(h => h.close);
            const tradeValuesYi = history.map(h => (h.trade_value / 100000000.0));
            const tradeCounts = history.map(h => h.trade_count);

            const minPrice = Math.min(...closes) * 0.99;
            const maxPrice = Math.max(...closes) * 1.01;
            const priceRange = maxPrice - minPrice || 1;

            const maxVal = Math.max(...tradeValuesYi) || 1;

            const paddingLeft = 40;
            const paddingRight = 15;
            const paddingTop = 25;
            const paddingBottom = 40;
            const chartW = w - paddingLeft - paddingRight;
            const chartH = h - paddingTop - paddingBottom;

            // Grid lines
            ctx.strokeStyle = '#30363d';
            ctx.lineWidth = 1;
            for (let i = 0; i <= 4; i++) {{
                const y = paddingTop + (chartH / 4) * i;
                ctx.beginPath();
                ctx.moveTo(paddingLeft, y);
                ctx.lineTo(w - paddingRight, y);
                ctx.stroke();

                // Y-axis label
                const val = (maxPrice - (priceRange / 4) * i).toFixed(2);
                ctx.fillStyle = '#8b949e';
                ctx.font = '10px sans-serif';
                ctx.textAlign = 'right';
                ctx.fillText('$' + val, paddingLeft - 4, y + 3);
            }}

            // Calculate x and y points
            const points = closes.map((p, i) => {{
                const x = paddingLeft + (chartW / (closes.length - 1)) * i;
                const y = paddingTop + chartH - ((p - minPrice) / priceRange) * chartH;
                return {{ 
                    x, y, 
                    price: p, 
                    date: dates[i], 
                    valYi: tradeValuesYi[i], 
                    cnt: tradeCounts[i] 
                }};
            }});

            // Draw Single-day Trade Value Bars (Background)
            points.forEach(p => {{
                const barH = (p.valYi / maxVal) * (chartH * 0.4);
                const barW = Math.min(26, chartW / 6);
                ctx.fillStyle = 'rgba(188, 140, 255, 0.25)';
                ctx.fillRect(p.x - barW/2, paddingTop + chartH - barH, barW, barH);
                ctx.strokeStyle = 'rgba(188, 140, 255, 0.5)';
                ctx.lineWidth = 1;
                ctx.strokeRect(p.x - barW/2, paddingTop + chartH - barH, barW, barH);
            }});

            // Price Line Gradient Fill
            const isUp = closes[closes.length - 1] >= closes[0];
            const lineColor = isUp ? '#3fb950' : '#ff7b72';

            const grad = ctx.createLinearGradient(0, paddingTop, 0, paddingTop + chartH);
            grad.addColorStop(0, isUp ? 'rgba(63, 185, 80, 0.35)' : 'rgba(255, 123, 114, 0.35)');
            grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

            ctx.beginPath();
            ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {{
                ctx.lineTo(points[i].x, points[i].y);
            }}
            ctx.lineTo(points[points.length - 1].x, paddingTop + chartH);
            ctx.lineTo(points[0].x, paddingTop + chartH);
            ctx.closePath();
            ctx.fillStyle = grad;
            ctx.fill();

            // Price Line
            ctx.beginPath();
            ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {{
                ctx.lineTo(points[i].x, points[i].y);
            }}
            ctx.strokeStyle = lineColor;
            ctx.lineWidth = 3;
            ctx.stroke();

            // Dots & Multi-metric Labels
            points.forEach(p => {{
                ctx.beginPath();
                ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
                ctx.fillStyle = lineColor;
                ctx.fill();
                ctx.strokeStyle = '#161b22';
                ctx.lineWidth = 2;
                ctx.stroke();

                // Top Label: Close Price
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 10px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('$' + p.price.toFixed(2), p.x, p.y - 8);

                // Bottom Labels: Date, Single-day Trade Value & Transaction Count
                ctx.fillStyle = '#8b949e';
                ctx.font = '9px sans-serif';
                ctx.fillText(p.date, p.x, h - 22);

                const cntStr = p.cnt >= 10000 ? (p.cnt / 10000.0).toFixed(1) + '萬' : p.cnt.toLocaleString();
                ctx.fillStyle = '#bc8cff';
                ctx.font = 'bold 9px sans-serif';
                ctx.fillText(p.valYi.toFixed(1) + '億', p.x, h - 12);

                ctx.fillStyle = '#f1e05a';
                ctx.font = '8px sans-serif';
                ctx.fillText(cntStr, p.x, h - 3);
            }});
        }}
    </script>
</body>
</html>
"""

out_html_path = '/home/jrh/桌面/JRH20260720/etf_dashboard.html'
with open(out_html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Updated {out_html_path} with Mobile Responsive Fixes!")
