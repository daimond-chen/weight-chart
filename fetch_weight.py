#!/usr/bin/env python3
"""
從 Notion「習慣追蹤」資料來源抓取 紀錄日期 / 紀錄體重，寫成 data.json。
給 GitHub Actions 排程執行用；也可以在本機手動跑一次測試。

需要的環境變數：
  NOTION_TOKEN  Notion Integration 的 Internal Integration Token（存成 GitHub Secret，
                千萬不要寫進程式碼或 commit 進 repo）

資料來源 ID（data_source_id）不是密鑰，直接寫在下面常數裡。
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

DATA_SOURCE_ID = "1fe3a003-b4fa-805c-a52c-000b8a8b98ba"
NOTION_VERSION = "2025-09-03"
API_URL = f"https://api.notion.com/v1/data_sources/{DATA_SOURCE_ID}/query"

DATE_PROP = "紀錄日期"
WEIGHT_PROP = "紀錄體重"

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def notion_query(token, start_cursor=None):
    body = {
        "page_size": 100,
        "sorts": [{"property": DATE_PROP, "direction": "ascending"}],
    }
    if start_cursor:
        body["start_cursor"] = start_cursor

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Notion API 回傳錯誤 {e.code}：{detail}")


def extract_point(page):
    props = page.get("properties", {})
    date_prop = props.get(DATE_PROP, {})
    weight_prop = props.get(WEIGHT_PROP, {})

    date_val = date_prop.get("date")
    if not date_val or not date_val.get("start"):
        return None
    date_str = date_val["start"][:10]  # 只取日期部分，不管有沒有帶時間

    weight = weight_prop.get("number")
    if weight is None:
        return None

    return date_str, weight


def main():
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("錯誤：找不到環境變數 NOTION_TOKEN", file=sys.stderr)
        sys.exit(1)

    by_date = {}
    cursor = None
    pages_fetched = 0

    while True:
        result = notion_query(token, cursor)
        for page in result.get("results", []):
            extracted = extract_point(page)
            if extracted:
                date_str, weight = extracted
                by_date[date_str] = weight
        pages_fetched += len(result.get("results", []))

        if result.get("has_more"):
            cursor = result.get("next_cursor")
        else:
            break

    if not by_date:
        print("警告：沒有抓到任何有體重數值的紀錄，保留現有 data.json 不覆蓋。", file=sys.stderr)
        sys.exit(1)

    dates = sorted(by_date.keys())
    points = [{"date": d, "weight": by_date[d]} for d in dates]

    out = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "points": points,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print(f"完成：共 {pages_fetched} 筆紀錄，{len(points)} 筆有體重數值，"
          f"範圍 {dates[0]} ~ {dates[-1]}，寫入 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
