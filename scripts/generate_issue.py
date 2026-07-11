#!/usr/bin/env python3
"""
Weekly Korean stock market magazine generator.

Calls the Claude API (with the built-in web_search tool) to research the
past week's KOSPI/KOSDAQ action, renders it into the magazine's HTML
template, saves it under issues/, and updates manifest.json so it shows
up in the archive on index.html.

Requires env var ANTHROPIC_API_KEY. Run weekly via GitHub Actions
(see .github/workflows/weekly-magazine.yml).
"""
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ISSUES_DIR = ROOT / "issues"
MANIFEST_PATH = ISSUES_DIR / "manifest.json"

# NOTE: update this if Anthropic's model naming changes.
MODEL = "claude-sonnet-5"
API_URL = "https://api.anthropic.com/v1/messages"

SCHEMA_INSTRUCTIONS = """
당신은 한국 주식시장을 다루는 위클리 매거진의 애널리스트입니다.
web_search 도구를 사용해 지난 7일간의 코스피/코스닥 동향, 주요 뉴스,
그리고 저점을 다지고 반등하는 종목들을 조사한 뒤, 아래 JSON 스키마에
맞춰 "오직 JSON만" 출력하세요. 마크다운 코드블록(```)이나 설명 문구를
절대 포함하지 마세요.

스키마:
{
  "date_range": "YYYY년 M월 D일 – M월 D일 형식의 이번 조사 대상 주간",
  "title": "매거진 표지에 들어갈 한자 성어/은유적 한 줄 헤드라인 (8자 내외)",
  "ticker": [
    {"text": "KOSPI 0,000.00", "cls": "up|down|"},
    ... 5~6개, 지수/대형주/환율 등
  ],
  "overview_headline": "이번 주 시황을 압축한 헤드라인 문장",
  "overview_paragraphs": ["문단1", "문단2"],
  "news": [
    {"tag": "카테고리(예: 반도체, 바이오, 거시 등)", "title": "뉴스 제목", "body": "2~3문장 요약"},
    ... 정확히 6개
  ],
  "stock_watch_intro": "바닥권 반등 종목 섹션 도입부 1~2문장",
  "stocks": [
    {"name": "종목명", "sector": "섹터", "change": "+00.0%", "dir": "up|down", "reason": "반등/주목 이유 1문장"},
    ... 6~8개
  ],
  "callout_label": "유의사항 등 짧은 라벨",
  "callout_text": "반등이 추세전환인지 낙폭과대 되돌림인지 등에 대한 전문가 코멘트/유의사항",
  "quote": "이번 주를 요약하는 통찰력 있는 한 문장 (인용구 스타일)",
  "insights": ["문장1", "문장2", "문장3", "문장4"],
  "risks": ["리스크1", "리스크2", "리스크3", "리스크4"],
  "sources_note": "참고한 언론사/자료 목록과 날짜를 짧게 요약"
}

중요:
- 반드시 실제 검색 결과에 기반한 사실만 작성하고, 수치를 지어내지 마세요.
- 투자 권유가 아닌 정보 정리라는 점을 항상 유지하세요.
- 어조는 위클리 경제 매거진 톤(간결하고 분석적)으로 작성하세요.
"""


def call_claude(week_label: str) -> dict:
    api_key = os.environ["ANTHROPIC_API_KEY"]
    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 4096,
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 12}],
            "messages": [
                {
                    "role": "user",
                    "content": f"{SCHEMA_INSTRUCTIONS}\n\n이번 조사 대상 주간: {week_label}",
                }
            ],
        },
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()

    text = "".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    )
    cleaned = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def render_ticker(items):
    out = []
    for it in items:
        cls = f' <span class="{it["cls"]}">{it.get("delta","")}</span>' if it.get("cls") else ""
        out.append(f'    <span>{it["text"]}</span>')
    return "\n".join(out)


def render_news(news_items):
    left, right = [], []
    for i, n in enumerate(news_items):
        block = f'''        <div class="news-item">
          <span class="tag">{n["tag"]}</span>
          <h3>{n["title"]}</h3>
          <p>{n["body"]}</p>
        </div>'''
        (left if i % 2 == 0 else right).append(block)
    return "\n".join(left), "\n".join(right)


def render_stocks(stocks):
    rows = []
    for s in stocks:
        rows.append(f'''      <tr>
        <td class="name">{s["name"]}</td><td class="sector">{s["sector"]}</td>
        <td class="chg {s["dir"]}">{s["change"]}</td>
        <td>{s["reason"]}</td>
      </tr>''')
    return "\n".join(rows)


def render_list(items, style="num"):
    out = []
    if style == "num":
        for i, txt in enumerate(items, 1):
            out.append(f'      <li><span class="num">{i:02d}</span><span>{txt}</span></li>')
    else:
        labels = "ABCDEFGH"
        for i, txt in enumerate(items):
            out.append(f'      <li><span class="num">{labels[i]}</span><span>{txt}</span></li>')
    return "\n".join(out)


def build_html(issue_no: int, filename: str, d: dict) -> str:
    left_news, right_news = render_news(d["news"])
    ticker_html = "\n".join(f'    <span>{it["text"]}</span>' for it in d["ticker"])
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>위클리 마켓 리뷰 · {d["date_range"]}</title>
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>
<div class="sheet">

  <div class="masthead">
    <div class="kicker"><span>WEEKLY MARKET REVIEW</span><span>NO. {issue_no} · {date.today().year}</span></div>
    <h1>{d["title"]}</h1>
    <div class="sub">
      <span>{d["date_range"]}</span>
      <span><a href="../index.html">← 전체 호 보기</a></span>
    </div>
  </div>

  <div class="ticker">
{ticker_html}
  </div>

  <section>
    <div class="section-label"><span>이번 주 시장 리뷰</span><span>OVERVIEW</span></div>
    <h2 class="headline">{d["overview_headline"]}</h2>
    <p class="lede dropcap">{d["overview_paragraphs"][0]}</p>
    {"".join(f'<p class="lede" style="margin-top:14px;">{p}</p>' for p in d["overview_paragraphs"][1:])}
  </section>

  <section>
    <div class="section-label"><span>이번 주 헤드라인</span><span>NEWS</span></div>
    <div class="grid2">
      <div class="colrule">
{left_news}
      </div>
      <div>
{right_news}
      </div>
    </div>
  </section>

  <section>
    <div class="section-label"><span>바닥 다지고 올라오는 종목</span><span>TURNAROUND WATCH</span></div>
    <h2 class="headline">저점을 확인하고 방향을 튼 이름들</h2>
    <p class="lede" style="font-size:14.5px;">{d["stock_watch_intro"]}</p>
    <table class="ledger">
      <tr><th>종목</th><th>섹터</th><th>등락</th><th style="text-align:right;">반등 논리</th></tr>
{render_stocks(d["stocks"])}
    </table>
    <div class="callout">
      <span class="lbl">{d["callout_label"]}</span>
      {d["callout_text"]}
    </div>
  </section>

  <section>
    <div class="section-label"><span>인사이트</span><span>WHAT IT MEANS</span></div>
    <div class="quote-box">{d["quote"]}</div>
    <ul class="risk-list">
{render_list(d["insights"], "num")}
    </ul>
  </section>

  <section>
    <div class="section-label"><span>리스크 체크리스트</span><span>WATCHLIST</span></div>
    <ul class="risk-list">
{render_list(d["risks"], "alpha")}
    </ul>
  </section>

  <div class="colophon">
    {d["sources_note"]} · 본 매거진은 투자 참고용 정보 정리이며 투자 권유가 아닙니다 · 최종 투자 판단과 책임은 본인에게 있습니다.
  </div>

</div>
</body>
</html>
'''


def main():
    ISSUES_DIR.mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else []
    next_no = (max((m["issue_no"] for m in manifest), default=0)) + 1

    today = date.today()
    week_start = today - timedelta(days=6)
    week_label = f"{week_start.isoformat()} ~ {today.isoformat()}"
    filename = f"{today.isoformat()}.html"

    print(f"Generating issue No.{next_no} for {week_label} ...", file=sys.stderr)
    data = call_claude(week_label)

    html = build_html(next_no, filename, data)
    (ISSUES_DIR / filename).write_text(html, encoding="utf-8")

    manifest.append(
        {
            "issue_no": next_no,
            "file": filename,
            "date_range": data["date_range"],
            "title": data["title"],
            "published": today.isoformat(),
        }
    )
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote issues/{filename} and updated manifest.json", file=sys.stderr)


if __name__ == "__main__":
    main()
