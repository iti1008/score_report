import csv
import html
import unicodedata
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path


CSV_PATH = Path(__file__).with_name("課題2.csv")
HTML_PATH = Path(__file__).with_name("score_report.html")

FORMATS = ("table", "list", "detail")
FORMAT_LABELS = {
    "table": "表形式",
    "list": "箇条書き",
    "detail": "詳細リスト",
}


def display_width(text):
    width = 0
    for char in str(text):
        width += 2 if unicodedata.east_asian_width(char) in ("F", "W") else 1
    return width


def pad(text, width, align="left"):
    text = str(text)
    fill = max(0, width - display_width(text))
    if align == "right":
        return " " * fill + text
    if align == "center":
        left = fill // 2
        return " " * left + text + " " * (fill - left)
    return text + " " * fill


def format_avg(value):
    return str(Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def load_records(csv_path):
    by_name = defaultdict(list)
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            by_name[row["名前"].strip()].append(
                {
                    "日付": row["日付"].strip(),
                    "科目": row["科目"].strip(),
                    "スコア": int(row["スコア"]),
                }
            )
    return by_name


def summarize(records):
    scores = [item["スコア"] for item in records]
    subjects = []
    seen = set()
    for item in records:
        if item["科目"] not in seen:
            seen.add(item["科目"])
            subjects.append(item["科目"])
    return {
        "平均": sum(scores) / len(scores),
        "最高点": max(scores),
        "最低点": min(scores),
        "科目": subjects,
        "明細": records,
    }


def build_rows(records_by_name):
    rows = []
    for name, records in records_by_name.items():
        stats = summarize(records)
        stats["名前"] = name
        rows.append(stats)
    return rows


def column_widths(rows):
    headers = ["No", "名前", "平均", "最高点", "最低点", "科目"]
    widths = {header: display_width(header) for header in headers}
    for index, row in enumerate(rows, start=1):
        values = {
            "No": str(index),
            "名前": row["名前"],
            "平均": format_avg(row['平均']),
            "最高点": str(row["最高点"]),
            "最低点": str(row["最低点"]),
            "科目": f"+ {len(row['科目'])}科目",
        }
        for key, value in values.items():
            widths[key] = max(widths[key], display_width(value))
    return widths


def print_table(rows, expanded, widths):
    headers = ["No", "名前", "平均", "最高点", "最低点", "科目"]
    aligns = {
        "No": "right",
        "名前": "left",
        "平均": "right",
        "最高点": "right",
        "最低点": "right",
        "科目": "left",
    }
    header_line = "  ".join(pad(h, widths[h], aligns[h]) for h in headers)
    print(header_line)
    print("-" * display_width(header_line))
    for index, row in enumerate(rows, start=1):
        marker = "-" if row["名前"] in expanded else "+"
        cells = [
            pad(index, widths["No"], "right"),
            pad(row["名前"], widths["名前"]),
            pad(format_avg(row['平均']), widths["平均"], "right"),
            pad(row["最高点"], widths["最高点"], "right"),
            pad(row["最低点"], widths["最低点"], "right"),
            pad(f"{marker} {len(row['科目'])}科目", widths["科目"]),
        ]
        print("  ".join(cells))
        if row["名前"] in expanded:
            print_subjects(row)


def print_list(rows, expanded):
    for index, row in enumerate(rows, start=1):
        marker = "-" if row["名前"] in expanded else "+"
        print(
            f"- [{index}] {row['名前']}: 平均 {format_avg(row['平均'])} / "
            f"最高 {row['最高点']} / 最低 {row['最低点']} "
            f"[{marker}科目]"
        )
        if row["名前"] in expanded:
            print_subjects(row, indent="    ")


def print_detail(rows, expanded):
    for index, row in enumerate(rows, start=1):
        marker = "閉じる" if row["名前"] in expanded else "開く"
        print(f"[{index}] {row['名前']}")
        print(f"    平均    : {format_avg(row['平均'])}")
        print(f"    最高点  : {row['最高点']}")
        print(f"    最低点  : {row['最低点']}")
        print(f"    科目    : {len(row['科目'])}科目 （番号入力で{marker}）")
        if row["名前"] in expanded:
            print_subjects(row, indent="    ")
        print()


def print_subjects(row, indent="          "):
    grouped = defaultdict(list)
    for item in row["明細"]:
        grouped[item["科目"]].append(f"{item['日付']} {item['スコア']}点")
    for subject in row["科目"]:
        print(f"{indent}- {subject}: {', '.join(grouped[subject])}")


def print_report(rows, view_format, expanded):
    print()
    print(f"表示形式: {FORMAT_LABELS[view_format]}")
    print("番号を入力すると、その人の科目欄を開閉します。")
    print("f: 表示形式を変更 / a: 全員開閉 / h: HTML出力 / q: 終了")
    print()
    if view_format == "table":
        print_table(rows, expanded, column_widths(rows))
    elif view_format == "list":
        print_list(rows, expanded)
    else:
        print_detail(rows, expanded)


def choose_format(current):
    print()
    print("表示形式を選んでください。")
    for index, key in enumerate(FORMATS, start=1):
        current_mark = " (現在)" if key == current else ""
        print(f"  {index}. {FORMAT_LABELS[key]}{current_mark}")
    choice = input("> ").strip()
    if choice in {"1", "2", "3"}:
        return FORMATS[int(choice) - 1]
    print("1 / 2 / 3 のいずれかを入力してください。形式は変更しません。")
    return current


STAT_KEYS = ("平均", "最高点", "最低点")


def stat_extremes(rows):
    return {
        key: (max(row[key] for row in rows), min(row[key] for row in rows))
        for key in STAT_KEYS
    }


def highlight_class(row, key, extremes):
    top, bottom = extremes[key]
    if top == bottom:
        return ""
    if row[key] == top:
        return " best"
    if row[key] == bottom:
        return " worst"
    return ""


def subject_list(row):
    grouped = defaultdict(list)
    for item in row["明細"]:
        grouped[item["科目"]].append(
            f"{html.escape(item['日付'])} {item['スコア']}点"
        )
    return "".join(
        f"<li><strong>{html.escape(subject)}</strong>: "
        f"{', '.join(grouped[subject])}</li>"
        for subject in row["科目"]
    )


def write_html(rows):
    extremes = stat_extremes(rows)

    def cls(row, key):
        return highlight_class(row, key, extremes)

    cards = []
    table_rows = []
    for index, row in enumerate(rows):
        name = html.escape(row["名前"])
        avg = format_avg(row["平均"])
        subjects = subject_list(row)
        count = len(row["科目"])
        sort_attrs = (
            f'data-index="{index}" data-name="{name}" data-avg="{row["平均"]}" '
            f'data-max="{row["最高点"]}" data-min="{row["最低点"]}"'
        )

        cards.append(
            f"""
<article class="card" {sort_attrs}>
  <h2>{name}</h2>
  <dl class="stats">
    <div class="stat-avg"><dt>平均</dt><dd class="val{cls(row, '平均')}">{avg}</dd></div>
    <div><dt>最高点</dt><dd class="val{cls(row, '最高点')}">{row['最高点']}</dd></div>
    <div><dt>最低点</dt><dd class="val{cls(row, '最低点')}">{row['最低点']}</dd></div>
  </dl>
  <details>
    <summary>受けた科目（{count}科目）</summary>
    <ul>{subjects}</ul>
  </details>
</article>
"""
        )

        table_rows.append(
            f"""
<tr {sort_attrs}>
  <td>{name}</td>
  <td class="num avg"><span class="val{cls(row, '平均')}">{avg}</span></td>
  <td class="num"><span class="val{cls(row, '最高点')}">{row['最高点']}</span></td>
  <td class="num"><span class="val{cls(row, '最低点')}">{row['最低点']}</span></td>
  <td>
    <details>
      <summary>{count}科目</summary>
      <ul>{subjects}</ul>
    </details>
  </td>
</tr>
"""
        )

    HTML_PATH.write_text(
        f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>参加者スコア集計</title>
  <style>
    :root {{
      --bg: #f6f7fb;
      --card: #fff;
      --line: #d9deea;
      --text: #1f2937;
      --muted: #5b6472;
      --accent: #2563eb;
      --stripe: #f8fafc;
      --hover: #eef2ff;
      --best: #15803d;
      --best-bg: #dcfce7;
      --worst: #b91c1c;
      --worst-bg: #fee2e2;
    }}
    body {{
      margin: 0;
      font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    main {{
      max-width: 960px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px 20px;
      align-items: center;
      margin: 20px 0;
    }}
    label {{ color: var(--muted); }}
    select {{
      padding: 6px 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px 14px;
      font-size: 13px;
      color: var(--muted);
    }}
    .legend .val {{ font-size: 12px; }}
    .sort-status {{ font-size: 13px; color: var(--muted); margin: -8px 0 12px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--card);
      border-radius: 12px;
      overflow: hidden;
    }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: middle;
    }}
    th {{ background: #eef2ff; }}
    th.sortable {{ padding: 0; }}
    th.sortable button {{
      all: inherit;
      display: flex;
      align-items: center;
      gap: 4px;
      width: 100%;
      box-sizing: border-box;
      padding: 12px 14px;
      cursor: pointer;
      font-weight: 700;
    }}
    th.num.sortable button {{ justify-content: flex-end; }}
    th.sortable button:hover {{ color: var(--accent); }}
    th.sortable button:focus-visible {{ outline: 2px solid var(--accent); outline-offset: -2px; }}
    .sort-icon {{ color: var(--muted); font-size: 11px; }}
    th[aria-sort] .sort-icon {{ color: var(--accent); }}
    tbody tr:nth-child(even) {{ background: var(--stripe); }}
    tbody tr:hover {{ background: var(--hover); }}
    td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .avg, .stat-avg dd {{ font-weight: 700; }}
    .val {{
      display: inline-block;
      padding: 1px 6px;
      border-radius: 6px;
      font-variant-numeric: tabular-nums;
    }}
    .val.best {{ color: var(--best); background: var(--best-bg); font-weight: 700; }}
    .val.worst {{ color: var(--worst); background: var(--worst-bg); font-weight: 700; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
    }}
    .card h2 {{ margin: 0 0 12px; font-size: 18px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px 12px;
      margin: 0 0 12px;
    }}
    .stats dt {{ color: var(--muted); font-size: 12px; }}
    .stats dd {{ margin: 0; }}
    .stat-avg dd {{ font-size: 20px; }}
    details {{ margin-top: 8px; }}
    summary {{
      cursor: pointer;
      color: var(--accent);
      font-weight: 600;
    }}
    ul {{ margin: 8px 0 0; padding-left: 18px; }}
    .hidden {{ display: none; }}
  </style>
</head>
<body>
  <main>
    <h1>参加者スコア集計</h1>
    <p>平均・最高点・最低点と、受けた科目（折りたたみ）を表示します。</p>
    <div class="toolbar">
      <div>
        <label for="view">リスト形式</label>
        <select id="view">
          <option value="table">表形式</option>
          <option value="detail">カード形式</option>
        </select>
      </div>
      <div class="legend">
        <span><span class="val best">緑</span> 各項目で最も高い値</span>
        <span><span class="val worst">赤</span> 各項目で最も低い値</span>
      </div>
    </div>
    <p class="sort-status" id="sort-status">並び順：元の順（表の見出しをクリックで並べ替え）</p>
    <section id="view-table">
      <table>
        <thead>
          <tr>
            <th>名前</th>
            <th class="num sortable" data-key="avg"><button type="button">平均<span class="sort-icon">⇅</span></button></th>
            <th class="num sortable" data-key="max"><button type="button">最高点<span class="sort-icon">⇅</span></button></th>
            <th class="num sortable" data-key="min"><button type="button">最低点<span class="sort-icon">⇅</span></button></th>
            <th>受けた科目</th>
          </tr>
        </thead>
        <tbody id="table-body">
          {''.join(table_rows)}
        </tbody>
      </table>
    </section>
    <section id="view-detail" class="cards hidden">
      {''.join(cards)}
    </section>
  </main>
  <script>
    const select = document.getElementById("view");
    const views = {{
      table: document.getElementById("view-table"),
      detail: document.getElementById("view-detail"),
    }};
    select.addEventListener("change", () => {{
      Object.entries(views).forEach(([key, el]) => {{
        el.classList.toggle("hidden", key !== select.value);
      }});
    }});

    const labels = {{ avg: "平均", max: "最高点", min: "最低点" }};
    const headers = document.querySelectorAll("th.sortable");
    const status = document.getElementById("sort-status");
    let sortKey = null;
    let sortDir = null;

    function compare(a, b) {{
      let result = Number(a.dataset[sortKey]) - Number(b.dataset[sortKey]);
      if (sortDir === "desc") result = -result;
      return result || Number(a.dataset.index) - Number(b.dataset.index);
    }}

    function applySort() {{
      [document.getElementById("table-body"), views.detail].forEach((container) => {{
        [...container.children].sort(compare).forEach((el) => container.appendChild(el));
      }});
      headers.forEach((th) => {{
        const icon = th.querySelector(".sort-icon");
        if (th.dataset.key === sortKey) {{
          th.setAttribute("aria-sort", sortDir === "asc" ? "ascending" : "descending");
          icon.textContent = sortDir === "asc" ? "▲" : "▼";
        }} else {{
          th.removeAttribute("aria-sort");
          icon.textContent = "⇅";
        }}
      }});
      const dirLabel = sortDir === "asc" ? "昇順" : "降順";
      status.textContent = `並び順：${{labels[sortKey]}}の${{dirLabel}}（もう一度クリックで切り替え）`;
    }}

    headers.forEach((th) => {{
      th.querySelector("button").addEventListener("click", () => {{
        const key = th.dataset.key;
        if (sortKey === key) {{
          sortDir = sortDir === "asc" ? "desc" : "asc";
        }} else {{
          sortKey = key;
          sortDir = "desc";
        }}
        applySort();
      }});
    }});
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )
    return HTML_PATH


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSVが見つかりません: {CSV_PATH}")

    rows = build_rows(load_records(CSV_PATH))
    view_format = "table"
    expanded = set()

    while True:
        print_report(rows, view_format, expanded)
        choice = input("\n操作 > ").strip().lower()
        if choice in {"q", "quit", "終了"}:
            print("終了します")
            return
        if choice in {"f", "format", "形式"}:
            view_format = choose_format(view_format)
            continue
        if choice in {"a", "all"}:
            names = {row["名前"] for row in rows}
            expanded = set() if expanded == names else names
            continue
        if choice in {"h", "html"}:
            path = write_html(rows)
            print(f"HTMLを出力しました: {path}")
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(rows):
            name = rows[int(choice) - 1]["名前"]
            if name in expanded:
                expanded.remove(name)
            else:
                expanded.add(name)
            continue
        print("番号 / f / a / h / q のいずれかを入力してください")


if __name__ == "__main__":
    main()
