"""Compare the top 30% and bottom 20% of reels and write work/stats.md.

Usage (from the repo root): python3 reels_analysis/scripts/analyze.py

Main set: on-topic reels (relevant=1), split by virality = views / followers.
Checks: the same split by outlier_x (views / the account's own median, which
does not reward small accounts) and the whole 1,280-reel pet sample.
"""

import csv
import statistics as st
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "work" / "stats.md"


def load():
    rows = list(csv.DictReader(open(ROOT / "data.csv", encoding="utf-8")))
    for r in rows:
        r["virality"] = float(r["virality"]) if r["virality"] else None
        r["outlier_x"] = float(r["outlier_x"])
        r["followers"] = int(r["followers"])
        r["views"] = int(r["views"])
        r["duration_s"] = float(r["duration_s"]) if r["duration_s"] else None
        r["difficulty"] = int(r["difficulty"])
    return rows


def split(rows, key):
    vals = sorted(r[key] for r in rows if r[key] is not None)
    k = lambda p: vals[int((len(vals) - 1) * p)]
    top_cut, bottom_cut = k(0.70), k(0.20)
    top = [r for r in rows if r[key] is not None and r[key] >= top_cut]
    bottom = [r for r in rows if r[key] is not None and r[key] <= bottom_cut]
    return top, bottom


def features(r):
    f = {}
    for name in filter(None, r["formats"].split("; ")):
        f[f"формат: {name}"] = 1
    if not r["formats"]:
        f["формат: не определён"] = 1
    for name in filter(None, r["who_in_frame"].split("; ")):
        f[f"в кадре: {name}"] = 1
    f["текст в хуке (0–3 с)"] = int(r["has_text_hook"])
    f["текст на экране в ролике"] = int(r["has_text_overlay"])
    if r["text_overlays"]:
        f[f"тип текста: {r['text_overlays']}"] = 1
    if r["audio_kind"]:
        f[f"звук: {r['audio_kind']}"] = 1
    f["трендовый/узнаваемый звук"] = int(r["trend_audio"])
    f["звуковые эффекты (SFX)"] = int(r["sfx_present"] == "true")
    f["закольцован (loop)"] = int(r["is_looped"] == "true")
    if r["cuts_level"]:
        f[f"смены кадра: {r['cuts_level']}"] = 1
    pace = r["pacing"].split(" (")[0]
    if pace:
        f[f"темп: {pace}"] = 1
    f[f"сложность {r['difficulty']}"] = 1
    if r["duration_bucket"]:
        f[f"длина: {r['duration_bucket']} с"] = 1
    f["призыв в подписи"] = int(r["cta_in_caption"])
    f[f"язык: {r['lang']}"] = 1
    value = r["intended_value"].split(" ")[0].strip(",/|")
    if value:
        f[f"цель: {value}"] = 1
    return f


def compare(top, bottom, min_n=8):
    ct, cb = Counter(), Counter()
    for r in top:
        ct.update(k for k, v in features(r).items() if v)
    for r in bottom:
        cb.update(k for k, v in features(r).items() if v)
    lines = []
    for k in sorted(set(ct) | set(cb)):
        if ct[k] + cb[k] < min_n:
            continue
        pt, pb = 100 * ct[k] / len(top), 100 * cb[k] / len(bottom)
        lift = pt / pb if pb else float("inf")
        lines.append((lift, k, pt, pb, ct[k], cb[k]))
    lines.sort(key=lambda x: -x[0])
    return lines


def table(lines):
    out = ["| Признак | Топ-30% | Низ-20% | Во сколько раз чаще в топе |", "|---|---|---|---|"]
    for lift, k, pt, pb, nt, nb in lines:
        l = "∞" if lift == float("inf") else f"{lift:.2f}"
        out.append(f"| {k} | {pt:.0f}% ({nt}) | {pb:.0f}% ({nb}) | {l} |")
    return "\n".join(out)


def med(vals):
    vals = [v for v in vals if v is not None]
    return st.median(vals) if vals else None


def by_group(rows, key_fn, label, min_n=5):
    groups = {}
    for r in rows:
        for g in key_fn(r):
            groups.setdefault(g, []).append(r)
    out = [f"| {label} | Роликов | Медиана просмотры/подписчики | Медиана «x от медианы аккаунта» |", "|---|---|---|---|"]
    for g, rs in sorted(groups.items(), key=lambda kv: -(med([r["virality"] for r in kv[1]]) or 0)):
        if len(rs) < min_n:
            continue
        out.append(f"| {g} | {len(rs)} | {med([r['virality'] for r in rs]):.1f} | {med([r['outlier_x'] for r in rs]):.1f} |")
    return "\n".join(out)


def main():
    rows = load()
    rel = [r for r in rows if r["relevant"] == "1"]
    parts = [f"# Статистика (сгенерировано analyze.py)\n\nВсего роликов Instagram: {len(rows)}; по теме: {len(rel)}.\n"]

    top, bottom = split(rel, "virality")
    parts.append(f"## Основное сравнение: по теме, вирусность = просмотры / подписчики\n\nТоп-30%: {len(top)}, низ-20%: {len(bottom)}.")
    parts.append(
        f"Медиана подписчиков: топ {med([r['followers'] for r in top]):,.0f}, низ {med([r['followers'] for r in bottom]):,.0f}. "
        f"Медиана просмотров: топ {med([r['views'] for r in top]):,.0f}, низ {med([r['views'] for r in bottom]):,.0f}. "
        f"Медиана длины (точная): топ {med([r['duration_s'] for r in top])} с, низ {med([r['duration_s'] for r in bottom])} с.\n"
    )
    parts.append(table(compare(top, bottom)))

    t2, b2 = split(rel, "outlier_x")
    parts.append(f"\n## Проверка: по теме, сплит по «x от медианы аккаунта»\n\nТоп-30%: {len(t2)}, низ-20%: {len(b2)}.\n")
    parts.append(table(compare(t2, b2)))

    t3, b3 = split(rows, "virality")
    parts.append(f"\n## Проверка: все {len(rows)} роликов о животных, вирусность\n\nТоп-30%: {len(t3)}, низ-20%: {len(b3)}.\n")
    parts.append(table(compare(t3, b3, min_n=15)))

    parts.append("\n## По сложности съёмки (по теме)\n")
    parts.append(by_group(rel, lambda r: [f"сложность {r['difficulty']}"], "Сложность"))
    parts.append("\n## Форматы при сложности 1–2 (по теме)\n")
    easy = [r for r in rel if r["difficulty"] <= 2]
    parts.append(by_group(easy, lambda r: [f for f in r["formats"].split("; ") if f] or ["не определён"], "Формат"))
    parts.append("\n## Форматы при любой сложности (по теме)\n")
    parts.append(by_group(rel, lambda r: [f for f in r["formats"].split("; ") if f] or ["не определён"], "Формат"))
    parts.append("\n## Кто в кадре (по теме)\n")
    parts.append(by_group(rel, lambda r: [f for f in r["who_in_frame"].split("; ") if f] or ["не определено"], "В кадре"))
    parts.append("\n## Длина: Instagram, только ролики с известной длиной\n")
    parts.append("Длина известна, только когда поиск задавал минимальную длину, поэтому роликов короче 10 с почти нет.\n")
    parts.append("По теме:\n")
    parts.append(by_group(rel, lambda r: [r["duration_bucket"] or "длина неизвестна"], "Длина, с", min_n=3))
    parts.append("\nВсе ролики о животных:\n")
    parts.append(by_group(rows, lambda r: [r["duration_bucket"] or "длина неизвестна"], "Длина, с"))
    parts.append("\nОдин и тот же запрос с разными фильтрами длины (все результаты запроса):\n")
    by_query = {}
    for r in rows:
        for q in r["queries"].split():
            by_query.setdefault(q, []).append(r)
    groups = {"RU зоомагазин": ("q03", "q04", "q05"), "EN pet store": ("q07", "q08", "q09"),
              "груминг": ("q11", "q12", "q13"), "корма и товары": ("q15", "q16", "q17")}
    lines = ["| Запрос | 10–20 с | 20–40 с | 40+ с |", "|---|---|---|---|"]
    for name, qs in groups.items():
        cells = [f"x{med([r['outlier_x'] for r in by_query[q]]):.0f} · {med([r['virality'] for r in by_query[q]]):.0f}" for q in qs]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    parts.append("\n".join(lines))
    parts.append("\n(в ячейке: медиана «x от медианы аккаунта» · медиана просмотры/подписчики)\n")

    tiktok = list(csv.DictReader(open(ROOT / "work" / "tiktok.csv", encoding="utf-8")))
    for r in tiktok:
        r["virality"] = float(r["virality"]) if r["virality"] else None
        r["outlier_x"] = float(r["outlier_x"])
        r["duration_s"] = float(r["duration_s"]) if r["duration_s"] else None
    known = [r for r in tiktok if r["duration_s"] is not None]
    parts.append(f"\n## Длина: TikTok из тех же запросов, для справки (длина известна у {len(known)} из {len(tiktok)})\n")
    tb = lambda r: ["до 7 с" if r["duration_s"] <= 7 else "7–15 с" if r["duration_s"] <= 15 else "15–30 с" if r["duration_s"] <= 30 else "30–60 с" if r["duration_s"] <= 60 else "60+ с"]
    parts.append("Все:\n")
    parts.append(by_group(known, tb, "Длина"))
    parts.append("\nПо теме:\n")
    parts.append(by_group([r for r in known if r["relevant"] == "1"], tb, "Длина"))
    parts.append("\n## Звук (по теме)\n")
    parts.append(by_group(rel, lambda r: [r["audio_kind"] or "нет данных"], "Звук"))
    parts.append("\n## Текст (по теме)\n")
    parts.append(by_group(rel, lambda r: [("текст в хуке" if r["has_text_hook"] == "1" else "без текста в хуке")], "Текст"))
    parts.append(by_group(rel, lambda r: [r["text_overlays"] or "без текста на экране"], "Тип текста"))
    parts.append("\n## Смены кадра и темп (по теме)\n")
    parts.append(by_group(rel, lambda r: [r["cuts_level"] or "нет данных"], "Смены кадра"))
    parts.append(by_group(rel, lambda r: [r["pacing"].split(" (")[0] or "нет данных"], "Темп"))

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
