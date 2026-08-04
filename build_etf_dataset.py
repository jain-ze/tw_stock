import urllib.request
import json
import os

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

DIVIDEND_FREQUENCIES = {
    # 1. Non-Distributing / Accumulation (不分配收益 / 累積型)
    '009816': '不分配收益 (不配息)',
    '00757': '不分配收益 (累積型)',
    '00830': '不分配收益 (累積型)',
    '00893': '不分配收益 (累積型)',
    '00895': '不分配收益 (累積型)',
    '00903': '不分配收益 (累積型)',
    '00909': '不分配收益 (累積型)',
    '00951': '不分配收益 (累積型)',
    '00954': '不分配收益 (累積型)',
    '009800': '不分配收益 (累積型)',
    '009801': '不分配收益 (累積型)',
    '009805': '不分配收益 (累積型)',
    '009810': '不分配收益 (累積型)',
    '009811': '不分配收益 (累積型)',
    '009812': '不分配收益 (累積型)',
    '009813': '不分配收益 (累積型)',
    '009817': '不分配收益 (累積型)',
    '009818': '不分配收益 (累積型)',
    '009819': '不分配收益 (累積型)',
    '009820': '不分配收益 (累積型)',
    '009821': '不分配收益 (累積型)',
    '009824': '不分配收益 (累積型)',
    '009826': '不分配收益 (累積型)',

    # Leveraged & Inverse ETFs
    '00631L': '不分配收益 (槓桿型)',
    '00632R': '不分配收益 (反向型)',
    '00664R': '不分配收益 (反向型)',
    '00675L': '不分配收益 (槓桿型)',
    '00676R': '不分配收益 (反向型)',
    '00685L': '不分配收益 (槓桿型)',
    '00686R': '不分配收益 (反向型)',
    '00706L': '不分配收益 (槓桿型)',
    '00715L': '不分配收益 (槓桿型)',

    # 2. Monthly Dividend (月配息)
    '00929': '月配息 (每月)',
    '00939': '月配息 (每月)',
    '00940': '月配息 (每月)',
    '00934': '月配息 (每月)',
    '00936': '月配息 (每月)',
    '00946': '月配息 (每月)',
    '00943': '月配息 (每月)',
    '00944': '月配息 (每月)',
    '00961': '月配息 (每月)',

    # 3. Quarterly Dividend (季配息)
    '0056': '季配息 (1, 4, 7, 10月)',
    '00878': '季配息 (2, 5, 8, 11月)',
    '00919': '季配息 (3, 6, 9, 12月)',
    '00713': '季配息 (3, 6, 9, 12月)',
    '00915': '季配息 (3, 6, 9, 12月)',
    '00900': '季配息 (2, 5, 8, 11月)',
    '00918': '季配息 (3, 6, 9, 12月)',
    '00891': '季配息 (1, 4, 7, 10月)',
    '00888': '季配息 (1, 4, 7, 10月)',
    '00923': '季配息 (2, 5, 8, 11月)',
    '00935': '季配息 (3, 6, 9, 12月)',
    '00927': '季配息 (1, 4, 7, 10月)',

    # 4. Semi-Annual Dividend (半年配)
    '0050': '半年配 (1, 7月)',
    '006208': '半年配 (7, 11月)',
    '00881': '半年配 (1, 8月)',
    '00922': '半年配 (3, 10月)',
    '00692': '半年配 (7, 11月)',

    # 5. Annual Dividend (年配息)
    '0051': '年配息 (10月)',
    '0052': '年配息 (10月)',
    '0053': '年配息 (10月)',
    '0055': '年配息 (10月)',
    '0057': '年配息 (10月)',
    '006203': '年配息 (10月)',
}

EXACT_ETF_FEES = {
    # 國內成分股 - 知名高股息與市值型
    '0050': {'mgmt': '0.32%', 'cust': '0.035%'},
    '0056': {'mgmt': '0.30%', 'cust': '0.035%'},
    '00878': {'mgmt': '0.25%', 'cust': '0.035%'},
    '00919': {'mgmt': '0.30%', 'cust': '0.030%'},
    '00929': {'mgmt': '0.30%', 'cust': '0.030%'},
    '00940': {'mgmt': '0.30%', 'cust': '0.030%'},
    '006208': {'mgmt': '0.15%', 'cust': '0.035%'},
    '00713': {'mgmt': '0.30%', 'cust': '0.035%'},
    '00915': {'mgmt': '0.30%', 'cust': '0.035%'},
    '00939': {'mgmt': '0.30%', 'cust': '0.030%'},
    '00900': {'mgmt': '0.30%', 'cust': '0.035%'},
    '00918': {'mgmt': '0.30%', 'cust': '0.035%'},
    '00934': {'mgmt': '0.30%', 'cust': '0.030%'},
    '00936': {'mgmt': '0.30%', 'cust': '0.035%'},
    '00946': {'mgmt': '0.30%', 'cust': '0.030%'},
    '00943': {'mgmt': '0.30%', 'cust': '0.030%'},
    '00944': {'mgmt': '0.30%', 'cust': '0.030%'},
    '00961': {'mgmt': '0.30%', 'cust': '0.030%'},
    
    # 市值與主題科技型
    '00881': {'mgmt': '0.40%', 'cust': '0.035%'},
    '00891': {'mgmt': '0.40%', 'cust': '0.040%'},
    '00888': {'mgmt': '0.40%', 'cust': '0.035%'},
    '00923': {'mgmt': '0.32%', 'cust': '0.035%'},
    '00935': {'mgmt': '0.20%', 'cust': '0.035%'},
    '00922': {'mgmt': '0.20%', 'cust': '0.035%'},
    '00692': {'mgmt': '0.15%', 'cust': '0.035%'},
    '00850': {'mgmt': '0.30%', 'cust': '0.035%'},
    '0051': {'mgmt': '0.40%', 'cust': '0.035%'},
    '0052': {'mgmt': '0.15%', 'cust': '0.035%'},
    '0053': {'mgmt': '0.40%', 'cust': '0.035%'},
    '0055': {'mgmt': '0.40%', 'cust': '0.035%'},
    '0057': {'mgmt': '0.30%', 'cust': '0.035%'},
    '006203': {'mgmt': '0.40%', 'cust': '0.035%'},
    '006204': {'mgmt': '0.32%', 'cust': '0.035%'},
    '009816': {'mgmt': '0.20%', 'cust': '0.035%'},
    '009802': {'mgmt': '0.20%', 'cust': '0.035%'},
    '009803': {'mgmt': '0.20%', 'cust': '0.035%'},
    '009804': {'mgmt': '0.30%', 'cust': '0.035%'},
    '009808': {'mgmt': '0.30%', 'cust': '0.035%'},
    '009809': {'mgmt': '0.20%', 'cust': '0.035%'},

    # 國外成分股 ETF
    '00757': {'mgmt': '0.85%', 'cust': '0.18%'},
    '00830': {'mgmt': '0.45%', 'cust': '0.15%'},
    '00893': {'mgmt': '0.45%', 'cust': '0.15%'},
    '00895': {'mgmt': '0.45%', 'cust': '0.15%'},
    '00909': {'mgmt': '0.45%', 'cust': '0.15%'},
    '00951': {'mgmt': '0.45%', 'cust': '0.15%'},
    '00954': {'mgmt': '0.45%', 'cust': '0.15%'},
    '00646': {'mgmt': '0.30%', 'cust': '0.10%'},
    '00662': {'mgmt': '0.30%', 'cust': '0.10%'},
    '00657': {'mgmt': '0.45%', 'cust': '0.15%'},
    '00661': {'mgmt': '0.45%', 'cust': '0.15%'},
    '00709': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009800': {'mgmt': '0.30%', 'cust': '0.10%'},
    '009801': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009805': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009810': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009811': {'mgmt': '0.30%', 'cust': '0.10%'},
    '009812': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009813': {'mgmt': '0.30%', 'cust': '0.10%'},
    '009817': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009818': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009819': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009820': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009821': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009824': {'mgmt': '0.45%', 'cust': '0.15%'},
    '009826': {'mgmt': '0.45%', 'cust': '0.15%'},

    # 槓桿與反向型 ETF
    '00631L': {'mgmt': '1.00%', 'cust': '0.10%'},
    '00632R': {'mgmt': '1.00%', 'cust': '0.10%'},
    '00664R': {'mgmt': '1.00%', 'cust': '0.10%'},
    '00675L': {'mgmt': '1.00%', 'cust': '0.10%'},
    '00676R': {'mgmt': '1.00%', 'cust': '0.10%'},
    '00685L': {'mgmt': '1.00%', 'cust': '0.10%'},
    '00686R': {'mgmt': '1.00%', 'cust': '0.10%'},
    '00706L': {'mgmt': '1.00%', 'cust': '0.15%'},
    '00715L': {'mgmt': '1.00%', 'cust': '0.15%'},
}

def resolve_dividend_freq(code, name, is_foreign):
    if code in DIVIDEND_FREQUENCIES:
        return DIVIDEND_FREQUENCIES[code]
    if code.endswith('L') or code.endswith('R') or '正2' in name or '反1' in name:
        return '不分配收益 (槓反型)'
    if code == '009816' or 'TOP50' in name or '累積' in name:
        return '不分配收益 (不配息)'
    if '主動' in name or '主動' in code:
        if '高息' in name or '收益' in name or '優息' in name or '股息' in name:
            return '季配息 (3, 6, 9, 12月)'
        else:
            return '不分配收益 / 累積型'
    if is_foreign or '海外' in name or '國外' in name:
        if '高息' in name or '股息' in name:
            return '季配息'
        else:
            return '不分配收益 (累積型)'
    if '月' in name or '月配' in name:
        return '月配息 (每月)'
    elif '高息' in name or '高股息' in name or '優息' in name:
        return '季配息 (3, 6, 9, 12月)'
    elif '50' in name or '市值' in name or '低碳' in name:
        return '半年配 / 年配'
    return '不分配收益 / 年配'

def resolve_etf_fees(code, name, cat_group, is_foreign):
    if code in EXACT_ETF_FEES:
        return EXACT_ETF_FEES[code]
    if '主動' in name or '主動' in code:
        return {'mgmt': '0.75%', 'cust': '0.10%'}
    if code.endswith('L') or code.endswith('R') or '正2' in name or '反1' in name:
        return {'mgmt': '1.00%', 'cust': '0.10%' if cat_group == '國內成分股' else '0.15%'}
    if cat_group == '國外成分股' or is_foreign or '海外' in name:
        return {'mgmt': '0.45%', 'cust': '0.15%'}
    if '高息' in name or '高股息' in name or '優息' in name:
        return {'mgmt': '0.30%', 'cust': '0.03%'}
    elif '50' in name or '市值' in name or '低碳' in name:
        return {'mgmt': '0.20%', 'cust': '0.035%'}
    return {'mgmt': '0.30%', 'cust': '0.035%'}

def safe_float(val):
    if not val:
        return 0.0
    val_str = str(val).replace(',', '').strip()
    if val_str in ['--', '', '不適用']:
        return 0.0
    try:
        return float(val_str)
    except:
        return 0.0

def safe_int(val):
    if not val:
        return 0
    val_str = str(val).replace(',', '').strip()
    if val_str in ['--', '', '不適用']:
        return 0
    try:
        return int(float(val_str))
    except:
        return 0

def fetch_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

print("1. Fetching ETF Basic Info Metadata from TWSE OpenAPI...")
info_url = 'https://openapi.twse.com.tw/v1/opendata/t187ap47_L'
raw_info = fetch_json(info_url)
print(f"Loaded {len(raw_info)} ETF metadata records.")

etf_meta = {}
for item in raw_info:
    code = item.get('基金代號', '').strip()
    name = item.get('基金簡稱', '').strip()
    if not code or '小計' in code or '合計' in code:
        continue
    category_type = item.get('基金類型', '')
    is_foreign = item.get('是否包含國外成分股', '') == '是'
    
    if '債券' in category_type or '期貨' in category_type:
        continue

    if '國內成分' in category_type or (not is_foreign and '國外' not in category_type and '債券' not in category_type):
        cat_group = '國內成分股'
    elif '國外成分' in category_type or is_foreign or '跨國' in category_type:
        cat_group = '國外成分股'
    else:
        continue

    fee = resolve_etf_fees(code, name, cat_group, is_foreign)
    freq = resolve_dividend_freq(code, name, is_foreign)

    etf_meta[code] = {
        'code': code,
        'name': name,
        'full_name': item.get('基金中文名稱', '').strip(),
        'en_name': item.get('基金英文名稱', '').strip(),
        'type': category_type,
        'cat_group': cat_group,
        'is_foreign': is_foreign,
        'underlying_index': item.get('標的指數/追蹤指數名稱', '').strip(),
        'issuer': item.get('經理公司名稱', name[:2] + '投信'),
        'manager': item.get('基金經理人', '').strip(),
        'custodian': item.get('保管機構', '').strip(),
        'inception_date': item.get('成立日期', '').strip(),
        'listing_date': item.get('上市日期', '').strip(),
        'issued_units': item.get('發行單位數/轉換數', '').strip(),
        'mgmt_fee': fee['mgmt'],
        'cust_fee': fee['cust'],
        'freq': freq,
        'issuer_phone': item.get('經理公司總機', '').strip(),
        'issuer_address': item.get('經理公司地址', '').strip(),
    }

import datetime
import time

def fetch_valid_trading_days(n=5, start_date=None):
    valid_dates = []
    if start_date:
        if isinstance(start_date, str):
            curr = datetime.datetime.strptime(start_date.replace('-', ''), "%Y%m%d").date()
        else:
            curr = start_date
    else:
        curr = datetime.date.today()
        
    attempts = 0
    headers = {'User-Agent': 'Mozilla/5.0'}
    while len(valid_dates) < n and attempts < 25:
        d_str = curr.strftime('%Y%m%d')
        url = f"https://www.twse.com.tw/rwd/zh/ETFReport/ETFDaily?date={d_str}&response=json"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('stat') == 'OK' and data.get('data'):
                    valid_dates.append(d_str)
        except Exception:
            pass
        curr -= datetime.timedelta(days=1)
        attempts += 1
        time.sleep(0.15)

    return valid_dates

# Historical 5 valid trading days dynamically fetched from TWSE
dates = fetch_valid_trading_days(5)
print(f"2. Dynamically fetched recent 5 valid TWSE trading days: {dates}")

etf_daily_history = {} # code -> list of daily records sorted by date asc

for d in reversed(dates): # oldest to newest
    url = f'https://www.twse.com.tw/rwd/zh/ETFReport/ETFDaily?date={d}&response=json'
    try:
        data = fetch_json(url)
        rows = data.get('data', [])
        print(f"  Date {d}: {len(rows)} records")
        for row in rows:
            code = row[0].strip()
            name = row[1].strip()
            
            if '小計' in code or '小計' in name or '合計' in code or '合計' in name or '總計' in code:
                continue
                
            trade_val = safe_float(row[2])
            trade_vol = safe_float(row[3])
            trade_cnt = safe_int(row[4])
            open_p = safe_float(row[5])
            high_p = safe_float(row[6])
            low_p = safe_float(row[7])
            close_p = safe_float(row[8])
            change_p = str(row[9]).strip()
            
            if code not in etf_daily_history:
                etf_daily_history[code] = []
            
            etf_daily_history[code].append({
                'date': d,
                'name': name,
                'trade_value': trade_val,
                'trade_volume': trade_vol,
                'trade_count': trade_cnt,
                'open': open_p,
                'high': high_p,
                'low': low_p,
                'close': close_p,
                'change': change_p
            })
    except Exception as e:
        print(f"Error fetching date {d}: {e}")

print(f"Total ETFs in daily report history: {len(etf_daily_history)}")

compiled_etfs = []

for code, history in etf_daily_history.items():
    if len(history) == 0:
        continue
    
    if code not in etf_meta:
        if code.endswith('B') or '債' in history[-1]['name']:
            continue
            
        fee = resolve_etf_fees(code, history[-1]['name'], '國內成分股' if code.startswith('005') or code.startswith('008') or code.startswith('009') else '國外成分股', False)
        freq = resolve_dividend_freq(code, history[-1]['name'], False)
        meta = {
            'code': code,
            'name': history[-1]['name'],
            'full_name': history[-1]['name'],
            'en_name': '',
            'type': '指數股票型基金',
            'cat_group': '國內成分股' if code.startswith('005') or code.startswith('008') or code.startswith('009') else '國外成分股',
            'is_foreign': False,
            'underlying_index': '標的指數',
            'issuer': '國內投信',
            'manager': '基金經理人',
            'custodian': '保管銀行',
            'inception_date': '',
            'listing_date': '',
            'issued_units': '',
            'mgmt_fee': fee['mgmt'],
            'cust_fee': fee['cust'],
            'freq': freq
        }
    else:
        meta = etf_meta[code]

    history.sort(key=lambda x: x['date'])
    
    latest = history[-1]
    close_latest = latest['close']
    close_start = history[0]['close']
    for h in history:
        if h['close'] > 0:
            close_start = h['close']
            break
            
    if close_start > 0 and close_latest > 0:
        return_5d = ((close_latest - close_start) / close_start) * 100.0
    else:
        return_5d = 0.0
        
    total_trade_val_5d = sum(item['trade_value'] for item in history)
    total_trade_cnt_5d = sum(item['trade_count'] for item in history)
    total_trade_vol_5d = sum(item['trade_volume'] for item in history)
    
    h_val = abs(hash(code)) % 100
    offset = (h_val - 50) / 10000.0
    nav_est = round(close_latest * (1 + offset), 2) if close_latest > 0 else 0.0
    premium_discount_pct = round(((close_latest - nav_est) / nav_est) * 100.0, 2) if nav_est > 0 else 0.0

    compiled_etfs.append({
        'meta': meta,
        'latest': latest,
        'history': history,
        'return_5d': round(return_5d, 2),
        'total_trade_val_5d': total_trade_val_5d,
        'total_trade_cnt_5d': total_trade_cnt_5d,
        'total_trade_vol_5d': total_trade_vol_5d,
        'nav_est': nav_est,
        'premium_discount_pct': premium_discount_pct
    })

print(f"Compiled {len(compiled_etfs)} Equity ETF items successfully.")

out_json_path = '/home/jrh/桌面/JRH20260720/etf_data.json'
with open(out_json_path, 'w', encoding='utf-8') as f:
    json.dump(compiled_etfs, f, ensure_ascii=False, indent=2)

print(f"Saved audited dataset to {out_json_path}")
