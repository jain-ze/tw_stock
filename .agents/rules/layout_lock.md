# 輸出版面固定與數據正確性穩定規範 (Strict Layout Lock & Data Integrity Policy)

> [!IMPORTANT]
> 1. **每日日報 HTML 版面結構固定**：
>    - 必須比照 `2026-08-21.html` 的極致暗黑版面與雙視圖切換系統 (`switchMainView`)。
>    - 必須包含「大盤指數與三大法人/融資籌碼統計表」、「TOP 20 成交金額獨立榜單 (含點擊彈出 5 日動態 Canvas 雙軸圖 Modal)」、「全方位大數據與籌碼解析 Grid」。
>    - 必須包含 6 大高解析 Base64 嵌入圖卡藝廊區 (`switchCard`)。
>
> 2. **ETF 5日大數據與前100名排行榜觀測站版面結構固定**：
>    - 必須永遠以 **「5日成交張數」** (取代 5 日成交筆數) 進行排序、欄位呈現與圖表標註。
>
> 3. **不可隨意變更版面原則**：
>    - 除非使用者發出明確修改指令，否則所有自動排程腳本 (`build_html_report.py`, `build_etf_dashboard.py`, `process_top20_trading_value.py` 等) 及 AI 助理回答，均**嚴禁隨意更動、簡化、閹割或微調現有之版面結構、顏色標籤與欄位配置**。
>
> 4. **🛡️ 數據正確性與程式碼穩定性三大法則 (Data Integrity & Code Stability)**：
>    - **(A) 欄位索引對應校驗**：解析官方 API（如 TWSE/TPEx `MI_INDEX`、`BFI82U`）時，必須精確對照官方 Schema，確保 `record[2]` 為成交股數/成交量、`record[3]` 為成交筆數、`record[4]` 為成交金額，嚴禁混淆與誤對。
>    - **(B) 自動化熔斷與斷言 (Sanity Circuit Breaker)**：腳本內部必須包含斷言邏輯（如 `成交金額 < 成交股數 * 股價 * 0.4` 時立即 throw Exception 中斷），防止異常數據寫入。針對指標股（如 0050、2330）必須實施單日張數門檻斷言驗證。
>    - **(C) 實測驗證才可發布**：修改任何 Python 腳本或 HTML 樣式後，宣稱完成前必須親自執行驗證指令，印出當日實測數字（如 0050 近5日成交張數與金額）確認 100% 正確後方可提交 Git 與發布。
>
> 5. **📜 歷史錯誤案例防復發檢討 (Historical Error Anti-Regression Rules)**：
>    - **[防範 1] API 欄位對調導致張數嚴重縮水**：`record[2]` = 股數, `record[3]` = 筆數, `record[4]` = 金額。絕不可將筆數混為張數。
>    - **[防範 2] 漲跌價差僅取符號而遺漏金額**：`record[9]` 為方向符號, `record[10]` 為金額。必須兩者結合為 `+0.90` 格式，嚴禁只顯示 `+` 或 `-`。
>    - **[防範 3] 大盤籌碼表未同步當日盤後最新數據**：`build_html_report.py` 必須動態讀取當日產出之 `TWSE_TPEX_Market_5Day_YYYYMMDD.csv`，且驗證第一列日期為當日日期。
>    - **[防範 4] 上櫃 (TPEx) 股票型/主動式 ETF 遺漏**：`build_etf_dataset.py` 必須同時向證交所 (TWSE) 與櫃買中心 (TPEx) OpenAPI 雙源擷取，確保 00411A (統一前沿科技)、00998A (復華金融股息) 等上櫃主動式/股票型 ETF 全數自動納入，且所有 API 來源資料必須轉置為統一標準 Schema。
