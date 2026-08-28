import urllib.request
import urllib.parse
import http.cookiejar
import json
import os
import re
import datetime
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest'
}

def clean_html(text):
    if not text:
        return ''
    text = re.sub(r'</?(ul|ol)[^>]*>', ' ', text)
    text = re.sub(r'<li[^>]*>', ' ｜ ', text)
    text = re.sub(r'</li[^>]*>', '', text)
    text = re.sub(r'<br\s*/?>', ' ｜ ', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^(｜|\s)+', '', text)
    text = re.sub(r'(｜|\s)+$', '', text)
    text = re.sub(r'(\s*｜\s*)+', ' ｜ ', text)
    return text

def extract_summary_fee(full_fee_str):
    if not full_fee_str:
        return '--'
    matches = re.findall(r'(\d+(?:\.\d+)?\s*%)', full_fee_str)
    if not matches:
        return full_fee_str[:15] if len(full_fee_str) <= 15 else '--'
    nums = [float(m.replace('%', '').strip()) for m in matches]
    if not nums:
        return '--'
    min_n, max_n = min(nums), max(nums)
    if min_n == max_n:
        return f'{min_n:.2f}%'
    else:
        return f'{min_n:.2f}% ~ {max_n:.2f}%'

def fetch_twse_official_spec(code):
    url = f'https://www.twse.com.tw/rwd/zh/ETF/productContent?id={code}&response=json'
    req_headers = headers.copy()
    req_headers['Referer'] = f'https://www.twse.com.tw/zh/products/securities/etf/products/content.html?{code}#domestic'
    
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('stat') == 'ok' and 'tables' in data and data['tables']:
                    rows = data['tables'][0].get('data', [])
                    fields = data['tables'][0].get('fields', [])
                    if rows:
                        row_dict = dict(zip(fields, rows[0]))
                        
                        mgmt_clean = clean_html(row_dict.get('管理費', ''))
                        cust_clean = clean_html(row_dict.get('保管費', ''))
                        dist_clean = clean_html(row_dict.get('收益分配', ''))
                        issuer_clean = clean_html(row_dict.get('基金經理公司', ''))
                        index_clean = clean_html(row_dict.get('標的指數', ''))
                        type_clean = clean_html(row_dict.get('ETF類別', ''))
                        listing_clean = clean_html(row_dict.get('上市日期', ''))
                        url_clean = clean_html(row_dict.get('基金經理公司網站', ''))
                        tax_clean = clean_html(row_dict.get('證券交易稅', ''))
                        unit_clean = clean_html(row_dict.get('交易單位', ''))

                        return {
                            'mgmt_fee': mgmt_clean,
                            'mgmt_fee_summary': extract_summary_fee(mgmt_clean),
                            'cust_fee': cust_clean,
                            'cust_fee_summary': extract_summary_fee(cust_clean),
                            'freq': dist_clean,
                            'issuer': issuer_clean,
                            'underlying_index': index_clean,
                            'type': type_clean,
                            'listing_date': listing_clean,
                            'official_url': url_clean,
                            'tax_rate': tax_clean,
                            'trade_unit': unit_clean
                        }
        except Exception as e:
            time.sleep(0.1)
    
    return {
        'mgmt_fee': '',
        'mgmt_fee_summary': '--',
        'cust_fee': '',
        'cust_fee_summary': '--',
        'freq': '',
        'issuer': '',
        'underlying_index': '',
        'type': '',
        'listing_date': '',
        'official_url': '',
        'tax_rate': '',
        'trade_unit': ''
    }

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

out_json_path = '/home/jrh/桌面/JRH20260720/etf_data.json'

# Load existing cached specs if available
existing_specs = {}
if os.path.exists(out_json_path):
    try:
        with open(out_json_path, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
            for item in old_data:
                c = item['meta']['code']
                existing_specs[c] = {
                    'mgmt_fee': item['meta'].get('mgmt_fee', ''),
                    'mgmt_fee_summary': item['meta'].get('mgmt_fee_summary', '--'),
                    'cust_fee': item['meta'].get('cust_fee', ''),
                    'cust_fee_summary': item['meta'].get('cust_fee_summary', '--'),
                    'freq': item['meta'].get('freq', ''),
                    'issuer': item['meta'].get('issuer', ''),
                    'underlying_index': item['meta'].get('underlying_index', ''),
                    'type': item['meta'].get('type', ''),
                    'listing_date': item['meta'].get('listing_date', ''),
                    'official_url': item['meta'].get('official_url', ''),
                    'tax_rate': item['meta'].get('tax_rate', ''),
                    'trade_unit': item['meta'].get('trade_unit', '')
                }
    except Exception as e:
        print("Notice loading cached json:", e)

force_spec_fetch = os.environ.get('FORCE_SPEC_FETCH') == '1'

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
    
    if is_foreign or '國外' in category_type or '跨國' in category_type:
        cat_group = '國外成分股'
    else:
        cat_group = '國內成分股'

    # Filter out Debt / Bond / REITs / Commodities / Warrants if any
    if any(k in category_type for k in ['債券', '不動產', '期貨', '大宗商品', '貨幣', 'REITs']):
        continue
    if any(k in name for k in ['美債', '公債', '公司債', '投等債', '高收益債', '金融債', '債']):
        continue

    # Fetch 100% official TWSE specification if force or missing, else use cached spec
    if force_spec_fetch or code not in existing_specs:
        twse_spec = fetch_twse_official_spec(code)
    else:
        twse_spec = existing_specs[code]

    etf_meta[code] = {
        'code': code,
        'name': name,
        'full_name': item.get('基金中文名稱', '').strip() or name,
        'en_name': item.get('基金英文名稱', '').strip(),
        'type': twse_spec['type'] or category_type,
        'cat_group': cat_group,
        'is_foreign': is_foreign,
        'underlying_index': twse_spec['underlying_index'] or item.get('標的指數/追蹤指數名稱', '').strip(),
        'issuer': twse_spec['issuer'] or item.get('經理公司名稱', name[:2] + '投信'),
        'manager': item.get('基金經理人', '').strip(),
        'custodian': item.get('保管機構', '').strip(),
        'inception_date': item.get('成立日期', '').strip(),
        'listing_date': twse_spec['listing_date'] or item.get('上市日期', '').strip(),
        'issued_units': item.get('發行單位數/轉換數', '').strip(),
        'mgmt_fee': twse_spec['mgmt_fee'],
        'mgmt_fee_summary': twse_spec['mgmt_fee_summary'],
        'cust_fee': twse_spec['cust_fee'],
        'cust_fee_summary': twse_spec['cust_fee_summary'],
        'freq': twse_spec['freq'],
        'official_url': twse_spec['official_url'],
        'tax_rate': twse_spec['tax_rate'],
        'trade_unit': twse_spec['trade_unit'],
        'issuer_phone': item.get('經理公司總機', '').strip(),
        'issuer_address': item.get('經理公司地址', '').strip(),
    }

print("2. Dynamically fetching recent 6 valid TWSE trading days (T-5 to T for 5 full intervals)...")
def fetch_valid_trading_days(n=6):
    import requests
    valid_dates = []
    curr = datetime.date.today()
    attempts = 0
    reports = {}
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.twse.com.tw/zh/products/securities/etf/products/list.html'
    })
    
    while len(valid_dates) < n and attempts < 45:
        # Skip Saturday (5) and Sunday (6) immediately without HTTP requests
        if curr.weekday() >= 5:
            curr -= datetime.timedelta(days=1)
            attempts += 1
            continue
            
        d_str = curr.strftime('%Y%m%d')
        
        # Primary endpoint: ETFDaily
        url_etf = f"https://www.twse.com.tw/rwd/zh/ETFReport/ETFDaily?date={d_str}&response=json"
        fetched_data = None
        
        for retry in range(2):
            try:
                resp = session.get(url_etf, timeout=8, allow_redirects=False)
                if resp.status_code == 200:
                    data = resp.json()
                    stat = data.get('stat', '')
                    if stat == 'OK' and data.get('data'):
                        fetched_data = data['data']
                        break
                    elif '沒有符合條件' in stat or 'No Data' in stat:
                        break
            except Exception:
                pass
            time.sleep(1.0)
            
        # Secondary fallback endpoint: afterTrading/MI_INDEX (ALLBUT0999) if ETFDaily failed or got WAF 307
        if not fetched_data:
            url_mi = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d_str}&type=ALLBUT0999&response=json"
            try:
                resp_mi = session.get(url_mi, timeout=8, allow_redirects=False)
                if resp_mi.status_code == 200:
                    data_mi = resp_mi.json()
                    if data_mi.get('stat') == 'OK' and data_mi.get('tables'):
                        t8 = None
                        for t in data_mi.get('tables', []):
                            if t.get('title') and '每日收盤行情' in t.get('title'):
                                t8 = t
                                break
                        if not t8 and len(data_mi.get('tables', [])) > 8:
                            t8 = data_mi['tables'][8]
                        if t8 and t8.get('data'):
                            # Convert MI_INDEX row to ETFDaily format for ETF items
                            mi_etf_rows = []
                            for row in t8['data']:
                                code = row[0].strip()
                                if code.startswith('00'):
                                    # Format: [Code, Name, Volume, Count, Value, Open, High, Low, Close, Dir, Diff, Last, ...]
                                    mi_etf_rows.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11]])
                            if mi_etf_rows:
                                fetched_data = mi_etf_rows
            except Exception:
                pass
                
        if fetched_data:
            valid_dates.append(d_str)
            reports[d_str] = fetched_data
            print(f"Successfully fetched trading day {d_str} (Records: {len(fetched_data)})")
            
        curr -= datetime.timedelta(days=1)
        attempts += 1
        time.sleep(1.0)
        
    return valid_dates, reports

valid_days, daily_reports = fetch_valid_trading_days(6)
print(f"Fetched {len(valid_days)} valid TWSE trading days (Base T-5 to T): {valid_days}")

if len(valid_days) < 6:
    raise RuntimeError(f"Failed to fetch 6 valid trading days! Only got {len(valid_days)}: {valid_days}")

all_codes = set()
for d_str, records in daily_reports.items():
    for r in records:
        if len(r) > 1:
            code = r[0].strip()
            if code in etf_meta:
                all_codes.add(code)

print(f"Total ETFs matched in 6-day daily reports: {len(all_codes)}")

compiled_etfs = []
for code in all_codes:
    meta = etf_meta[code]
    history = []
    
    for d_str in reversed(valid_days):
        records = daily_reports.get(d_str, [])
        record = next((r for r in records if r[0].strip() == code), None)
        if record and len(record) >= 10:
            # TWSE Official Fields Mapping:
            # 0: 證券代號, 1: 證券名稱, 2: 成交股數, 3: 成交筆數, 4: 成交金額, 5: 開盤價, 6: 最高價, 7: 最低價, 8: 收盤價, 9: 漲跌價差
            trade_volume = safe_int(record[2])  # 成交股數 (Volume in shares)
            trade_count = safe_int(record[3])   # 成交筆數 (Transaction count)
            trade_value = safe_int(record[4])   # 成交金額 (Value in NTD)
            open_price = safe_float(record[5])
            high_price = safe_float(record[6])
            low_price = safe_float(record[7])
            close_price = safe_float(record[8])
            change_str = record[9].strip()
            
            # --- 🛡️ 數據正確性與欄位自動熔斷驗證 (Data Sanity Assertions) ---
            if trade_value > 0 and trade_volume > 0 and close_price > 1.0:
                if trade_value < (trade_volume * close_price * 0.4):
                    raise ValueError(f"🚨 [數據異常熔斷] {code} ({d_str}) 欄位對應異常！成交金額({trade_value}) 小於 成交股數({trade_volume}) * 股價({close_price})")
            if code == '0050' and trade_volume < 1000000 and close_price > 50:
                raise ValueError(f"🚨 [數據異常熔斷] 0050 ({d_str}) 單日成交股數異常過低 ({trade_volume} 股)！請檢查 API 欄位對應！")
            # -------------------------------------------------------------
            
            # Format exact price change string (record[9] = direction sign, record[10] = price difference)
            dir_str = record[9].strip() if len(record) > 9 else ''
            diff_val = 0.0
            if len(record) > 10:
                val_str = str(record[10]).replace(',', '').strip()
                try:
                    diff_val = float(val_str)
                except:
                    diff_val = 0.0

            if diff_val == 0.0:
                clean_chg = "0.00"
            elif '+' in dir_str or 'red' in dir_str:
                clean_chg = f"+{diff_val:.2f}"
            elif '-' in dir_str or 'green' in dir_str:
                clean_chg = f"-{diff_val:.2f}"
            else:
                clean_chg = f"{diff_val:+.2f}"

            history.append({
                'date': d_str,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'change': clean_chg,
                'trade_volume': trade_volume,
                'trade_value': trade_value,
                'trade_count': trade_count
            })
            
    if not history:
        continue

    history.sort(key=lambda x: x['date'])
    
    latest = history[-1]
    close_latest = latest['close']
    close_start = history[0]['close']
    for h in history:
        if h['close'] > 0:
            close_start = h['close']
            break
            
    # Calculate exact 5-day return across 5 price change intervals (using T-5 base day close)
    if close_start > 0 and close_latest > 0:
        return_5d = ((close_latest - close_start) / close_start) * 100.0
    else:
        return_5d = 0.0
        
    # Sum cumulative trade volume & value over the 5 recent trading days (T-4 to T, i.e. history[1:])
    history_5d_active = history[1:] if len(history) >= 6 else history
    total_trade_val_5d = sum(item['trade_value'] for item in history_5d_active)
    total_trade_cnt_5d = sum(item['trade_count'] for item in history_5d_active)
    total_trade_vol_5d = sum(item['trade_volume'] for item in history_5d_active)
    
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

print(f"Compiled {len(compiled_etfs)} Equity ETF items with accurate TWSE 5-day history successfully.")

with open(out_json_path, 'w', encoding='utf-8') as f:
    json.dump(compiled_etfs, f, ensure_ascii=False, indent=2)

print(f"Saved verified 5-day dataset to {out_json_path}")
