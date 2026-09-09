# 體重趨勢圖 → 自動從 Notion 更新 → 嵌入「年度檢視」頁面

這個資料夾放的是一個**會自己更新**的體重折線圖：GitHub Actions 每天固定時間去 Notion
抓「🏋️ 習慣追蹤」資料庫裡的「紀錄日期」「紀錄體重」，寫成 `data.json`，`index.html`
讀這個檔案畫圖。設定好之後不用手動做任何事，Notion 裡多打一筆體重，隔天圖表就會自動更新。

檔案說明：

- `index.html` — 圖表本體，會 `fetch('data.json')` 來畫圖。
- `data.json` — 目前已經包含 2025-05-28 ~ 2026-09-08 共 270 筆體重紀錄（先幫你把歷史資料
  抓好，之後由 Action 自動覆蓋更新）。
- `fetch_weight.py` — 真正去呼叫 Notion API 抓資料、寫 `data.json` 的程式。
- `.github/workflows/update-weight.yml` — 排程設定，每天 UTC 14:00（台北時間 22:00）
  自動跑一次 `fetch_weight.py`，如果資料有變就自動 commit + push。

## 第一次設定

### 1. 建立 Notion Integration，拿到 Token

1. 到 [notion.so/my-integrations](https://www.notion.so/my-integrations) → **New integration**。
2. 名稱隨意（例如「體重圖表」），Associated workspace 選你的工作區。
3. Capabilities 只需要打勾 **Read content**（不需要 Insert/Update）。
4. 建立後，複製 **Internal Integration Secret**（長得像 `ntn_...` 或 `secret_...`）。
   **這組 token 只能貼進 GitHub Secrets，絕對不要貼在程式碼、Notion 頁面、或任何公開的地方**——
   拿到這組 token 的人可以讀取你分享給這個 integration 的所有資料。

### 2. 把「習慣追蹤」資料庫分享給這個 Integration

1. 打開你的「🏋️ 習慣追蹤」資料庫（在「年度檢視」頁面裡面那個內嵌的資料庫）。
2. 右上角 `···` → **Connections**（連結）→ 搜尋剛剛建立的 Integration 名稱 → 加入。
3. 如果沒有這個步驟，API 呼叫會回傳「找不到資料」的錯誤，即使 token 是對的。

### 3. 建立 GitHub Repository，上傳這個資料夾

1. 到 [github.com/new](https://github.com/new) 建一個新 repo（例如 `weight-chart`），
   選 **Public**（GitHub Pages 免費方案需要 public repo）。
2. 把這個資料夾的所有檔案（包含 `.github/workflows/update-weight.yml`）上傳/push 上去，
   注意資料夾結構要維持原樣（`.github/workflows/` 這層路徑不能變，GitHub 才認得出排程設定）。

### 4. 把 Notion Token 存成 GitHub Secret

1. 到 repo 的 **Settings → Secrets and variables → Actions → New repository secret**。
2. Name 填 `NOTION_TOKEN`，Value 貼上第 1 步拿到的 token，Add secret。
3. 這組 token 只有 GitHub Actions 執行時看得到，不會出現在程式碼或 log 裡。

### 5. 開啟 GitHub Pages

1. repo 的 **Settings → Pages**：Source 選 **Deploy from a branch**，Branch 選 `main`
   （或你的預設分支），資料夾選 `/ (root)`。
2. 存檔後等 1–2 分鐘，會出現網址，長得像：
   `https://<你的帳號>.github.io/weight-chart/`
3. 打開確認圖表有正常顯示（這時候看到的是先幫你放好的 270 筆歷史資料）。

### 6. 手動跑一次 Action，確認自動更新有效

1. repo 的 **Actions** 分頁 → 選 **Update weight data** → **Run workflow** → **Run workflow**。
2. 等它跑完（通常幾十秒），檢查有沒有出現新的 commit（如果體重資料跟現有的一樣就不會有新
   commit，這是正常的——workflow 只在資料真的變動時才 commit）。
3. 如果失敗，點進去看 log：最常見的原因是第 2 步忘記把資料庫分享給 Integration，
   或者 Secret 名稱打錯字。

### 7. 貼進 Notion「年度檢視」頁面，取代原本的體重折線圖

1. 找到「年度檢視」頁面裡目前那個 Notion 內建的體重折線圖 view，把它刪掉
   （或先移到旁邊，確認新圖表沒問題後再刪）。
2. 在同樣的位置輸入 `/embed`，選擇 **Embed**，貼上第 5 步的 GitHub Pages 網址，Embed link。
3. 拖曳調整嵌入框的高度/寬度（或用 `Create embed` 讓它全寬）。

之後每天 Notion 裡的體重一有新紀錄，隔天這個嵌入的圖表打開就會自動是最新的，不用手動做任何事。

## 圖表在畫什麼

- 折線只畫「有記錄體重的日子」，橫軸是實際日期（不是硬把每一筆拉齊），所以密集量測的時候
  線會比較擠、量得少的時候會比較疏。
- 兩次記錄間隔超過 10 天時，那一段線會改成虛線，提醒你那是「間隔內插」不是每天都量——
  你的資料裡有幾段這樣的空窗（例如 2026-02 中到 2026-03 初、2026-04 底到 2026-05 中、
  2026-05 底到 2026-06 底），虛線就是在標這些地方。
- Y 軸範圍是根據資料自動算的（不是寫死 70 那種固定值），資料變動範圍改變時軸線也會跟著調整。
- 右上角「切換成表格檢視」可以看到全部原始數字；滑鼠移到線上（或手機點選）可以看到那天的
  確切日期和體重。
- 圖表本身沒有圖例（legend）——因為只有一條線，標題已經說明了在畫什麼。

## 之後想调整排程時間或抓取範圍

- 排程時間：改 `.github/workflows/update-weight.yml` 裡的 `cron: "0 14 * * *"`
  （這是 UTC 時間，14:00 UTC = 台北時間 22:00）。
- 想抓的欄位/資料庫：改 `fetch_weight.py` 最上面的 `DATA_SOURCE_ID` / `DATE_PROP` /
  `WEIGHT_PROP` 常數。`DATA_SOURCE_ID` 目前指向你的「🏋️ 習慣追蹤」資料來源，如果之後在
  Notion 裡整個重建了這個資料庫，要重新去該資料庫的分享連結或用 Notion API 查一次新的
  data source id。

## 安全性提醒

- `NOTION_TOKEN` 只存在 GitHub Secret 裡，只有 Actions 執行當下讀得到，不會被寫進
  `data.json`、`index.html`，也不會出現在 commit 紀錄或公開的 Pages 網站裡。
- `data.json` 本身只包含日期和體重數字，沒有其他隱私資訊，可以放心讓它是 public repo
  的一部分（GitHub Pages 本身就要求檔案是公開的）。如果之後想抓其他更敏感的欄位，
  要重新評估要不要用 public repo。
