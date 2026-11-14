#!/usr/bin/env python3
"""monitor/reported.md から Obsidian 用の日次まとめノートを生成する。

出力先: obsidian/PLC市場ウォッチ/YYYY-MM-DD.md と 索引.md
何度実行しても同じ結果になる(全日付を作り直す)。標準ライブラリのみ。
"""
import re
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "monitor" / "reported.md"
OUT = ROOT / "obsidian" / "PLC市場ウォッチ"

NO_NEWS = "今週は報告すべき新しい動きなし"
UNUSED = ("SNSテーマ未使用", "初回調査")
URL_RE = re.compile(r"(?<![\w/\[(])((?:https?://)?(?:[\w-]+\.)+[a-z]{2,}/[^\s、。〕)」]+)")


def linkify(text):
    """裸のドメイン付きパスをクリックできるリンクにする。"""
    def repl(m):
        raw = m.group(1)
        url = raw if raw.startswith("http") else "https://" + raw
        return f"[{raw}]({url})"
    return URL_RE.sub(repl, text)


def parse_rows():
    rows = []
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\s*20\d\d-\d\d-\d\d", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        # 「動き」の中に | が入っていた場合は中央にまとめる
        label, source, level, theme = cells[0], cells[-3], cells[-2], cells[-1]
        move = " | ".join(cells[1:-3])
        rows.append({
            "date": label[:10], "label": label, "move": move,
            "source": source, "level": level, "theme": theme,
        })
    return rows


def clean_theme(theme):
    return theme.replace("(ニュースに基づかない例)", "").strip()


def build_note(date, rows):
    news = [r for r in rows if not r["move"].startswith(NO_NEWS)]
    quiet = [r for r in rows if r["move"].startswith(NO_NEWS)]
    out = [
        "---",
        f"date: {date}",
        "tags: [PLC, 市場ウォッチ]",
        f"新しい動き: {len(news)}",
        f"実行回数: {len(rows)}",
        "---",
        f"# PLC市場ウォッチ {date}",
        "",
        f"- 新しい動き:{len(news)}件",
        f"- チェック実行:{len(rows)}回(うち新しい動きなし {len(quiet)}回)",
        "",
        "## 新しい動き",
        "",
    ]
    if not news:
        out += ["この日は報告すべき新しい動きなし。", ""]
    for i, r in enumerate(news, 1):
        out += [
            f"### {i}. {r['move'][:40]}{'…' if len(r['move']) > 40 else ''}",
            "",
            r["move"],
            "",
            f"- 一次情報:{linkify(r['source']) if r['source'] not in ('-', '') else '記載なし'}",
            f"- 確認度:{r['level'] if r['level'] not in ('-', '') else '記載なし'}",
        ]
        if r["theme"] and not any(u in r["theme"] for u in UNUSED):
            out.append(f"- SNSテーマ:{r['theme']}")
        out.append("")
    themes = [clean_theme(r["theme"]) for r in quiet
              if r["theme"] and r["theme"] != "-" and not any(u in r["theme"] for u in UNUSED)]
    if themes:
        out += ["## ニュースに基づかないSNSテーマ案", ""]
        out += [f"- {t}" for t in themes]
        out.append("")
    out += [
        "---",
        "自動生成:`monitor/reported.md` から作成。確認度が「検索要約」の項目は原文未読。",
        "",
    ]
    return "\n".join(out), len(news)


def main():
    rows = parse_rows()
    if not rows:
        sys.exit("reported.md に表の行が見つかりません")
    by_date = OrderedDict()
    for r in rows:
        by_date.setdefault(r["date"], []).append(r)
    OUT.mkdir(parents=True, exist_ok=True)
    index = ["# PLC市場ウォッチ 索引", "", "| 日付 | 新しい動き | 実行回数 |", "|---|---|---|"]
    for date in sorted(by_date, reverse=True):
        text, n = build_note(date, by_date[date])
        (OUT / f"{date}.md").write_text(text, encoding="utf-8")
        index.append(f"| [[{date}]] | {n} | {len(by_date[date])} |")
    (OUT / "索引.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"{len(by_date)}日分のノートを {OUT.relative_to(ROOT)} に出力しました")


if __name__ == "__main__":
    main()
