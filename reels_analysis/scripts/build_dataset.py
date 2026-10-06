"""Parse raw vidIQ outlier-search outputs into data.csv.

Usage (from the repo root): python3 reels_analysis/scripts/build_dataset.py

Reads reels_analysis/raw/q*.txt, keeps one row per Instagram reel (merging the
searches it appeared in), adds derived labels and writes:
  reels_analysis/data.csv           Instagram reels, one row each
  reels_analysis/work/tiktok.csv    TikTok rows from the same searches (side data)

Labels (format, who is on screen, difficulty, CTA, relevance) are keyword rules
over vidIQ's AI description of each video plus the caption. Videos were not
downloaded; every row says so in analysis_basis.
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
WORK = ROOT / "work"

HEADER_RE = re.compile(r"^\*\*@(?P<handle>[^*]+)\*\* — \"(?P<rest>.*)$")
METRIC_RE = re.compile(
    r"^\s+(?P<views>[\d.,]+[KMB]?) views \((?P<x>[\d.,]+)x their median of (?P<median>[\d.,]+[KMB]?)\)"
    r" · (?P<followers>[\d.,]+[KMB]?) followers(?: · (?P<dur>[\d.]+)s)?\s*$"
)
TOP_KEY_RE = re.compile(r"^ {3}\*\*(?P<key>[a-z_0-9]+)\*\*:\s?(?P<val>.*)$")
SUB_KEY_RE = re.compile(r"^ {5}(?P<key>[a-z_0-9]+):\s?(?P<val>.*)$")
FILE_RE = re.compile(r"^(?P<qid>q\d+)_(?P<topic>[a-z-]+)_(?P<bucket>d[\d-]+|all)\.txt$")

# A durationMax-only search (d00-10) also returns Instagram reels whose length
# vidIQ does not know, so it says nothing about length. Searches with durationMin
# return only reels with a known length, and print it.
BUCKETS = {"d00-10": "", "d10-20": "10-20", "d20-40": "20-40", "d40-": "40+", "all": ""}


def num(s):
    s = s.replace(",", "")
    mult = {"K": 1e3, "M": 1e6, "B": 1e9}.get(s[-1], 1)
    return float(s[:-1] if mult != 1 else s) * mult


def parse_file(path):
    m = FILE_RE.match(path.name)
    meta = {"qid": m["qid"], "topic": m["topic"], "bucket": BUCKETS[m["bucket"]]}
    platform, rec, section, caption_lines, in_caption = None, None, None, [], False
    out = []

    def close():
        if rec is not None:
            out.append(rec)

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            close()
            rec, platform = None, line[3:].strip()
            continue
        h = HEADER_RE.match(line)
        if h:
            close()
            rec = {"platform": platform, "handle": h["handle"].strip(), **meta}
            caption_lines, in_caption, section = [h["rest"]], True, None
            continue
        if rec is None:
            continue
        mm = METRIC_RE.match(line)
        if in_caption and mm:
            cap = "\n".join(caption_lines).strip()
            rec["caption"] = cap[:-1] if cap.endswith('"') else cap
            rec["views"] = num(mm["views"])
            rec["outlier_x"] = float(mm["x"].replace(",", ""))
            rec["median_views"] = num(mm["median"])
            rec["followers"] = num(mm["followers"])
            rec["duration_s"] = float(mm["dur"]) if mm["dur"] else None
            in_caption = False
            continue
        if in_caption:
            caption_lines.append(line)
            continue
        s = line.strip()
        if s.startswith("reel:"):
            rec["id"] = s[5:]
            rec["url"] = f"https://www.instagram.com/reel/{s[5:]}/"
            continue
        if s.startswith("https://"):
            rec["id"] = rec["url"] = s
            continue
        t = TOP_KEY_RE.match(line)
        if t:
            key, val = t["key"], t["val"].strip()
            if val:
                rec[key.replace("tiktok_concept", "concept").replace("reel_concept", "concept")] = val
                section = None
            else:
                section = key
            continue
        sub = SUB_KEY_RE.match(line)
        if sub and section:
            rec[f"{section}.{sub['key']}"] = sub["val"].strip()
    close()
    return out


def rx(pattern):
    return re.compile(pattern, re.I)


# On topic by itself: pet retail, grooming, aquariums, pet food.
PET_TRADE = rx(
    r"pet ?(store|shop|supply|supplies|boutique)|petco|petsmart|chewy|зоомагаз|зоотовар|зоосалон"
    r"|groom(ing|er)|груминг|грумер|aquarium|aquascap|fish tank|аквариум|pet food|dog food|cat food|kibble|корм"
)
# Pet goods: on topic when the reel is about buying, testing or reviewing them.
PET_GOODS = rx(
    r"(dog|cat|pet) (bed|toy|product|treat|costume|clothes|sweater|hoodie|carrier|bowl|harness|collar|leash)s?"
    r"|for (dogs|cats|pets)|лежанк|переноск|ошейник|поводок|шлейк|когтеточ|наполнител|лакомств|миск|игрушк\w* для"
    r"|костюм\w* для (собак|кош|питом)|одежд\w* для (собак|кош|питом)|для (собак|кошек|животных|питомц)"
    r"|\btoys?\b|carrier|costume|harness|collar|leash|litter|scratch(ing)? post|terrarium|террариум|supplement|shampoo|шампун"
)
# Generic retail words: on topic only together with pet goods and an animal.
COMMERCE = rx(
    r"\b(store|shop|boutique|retail|warehouse)\b|магазин|бутик|customer|shopper|cashier|checkout|employee|staff|shopkeeper"
    r"|clerk|salesperson|seller|consultant|покупател|продав|кассир|консультант|сотрудни|стрижк|salon|салон"
    r"|unbox|haul|распаков|restock|поставк|inventory|shel(f|ves)|aisle|полк|ассортимент|new arrivals|новинк"
    r"|product|товар|brand|бренд|price|цена|ценник|скидк|акци|\bbuy(ing)?\b|bought|purchas|покупк|купил|купить"
)
PET = rx(
    r"\bdogs?\b|\bcats?\b|pupp|kitten|\bpets?\b|animal|\bfish(es)?\b|bird|parrot|hamster|rabbit|bunny|guinea pig|reptile|turtle"
    r"|собак|\bкош(?!ел)|\bкот(?!ор)|щен|питом|животн|\bрыб(?!ал)|попуг|хомя|кролик"
)
# Public zoos and oceanariums mention aquariums and animals but are not pet trade.
ZOO = rx(r"zookeeper|\bzoo\b|oceanarium|public aquarium|океанариум|зоопарк")

FORMATS = {
    "POV": rx(r"\bpov\b|first-person|first person|от первого лица"),
    "до/после": rx(r"before (and|&) after|before/after|transformation|до и после|до/после|преображ"),
    "угадай цену/вес": rx(r"guess(ing)? (the )?(price|cost|weight|how much)|угада|сколько стоит|price reveal|ценник"),
    "распаковка/покупки": rx(r"unbox|haul|распаков|shopping spree|what i bought|new arrivals|новинк|restock|поставк"),
    "животное-«сотрудник»": rx(
        r"(shop|store|salon) (cat|dog|pet|mascot)|(cat|dog|pet) (works|working|employee|staff|manager|security|cashier|boss|helper)"
        r"|employee of the month|магазинн\w* (кот|пёс|пес|собак)|кот[- ](продав|сотрудн|охран|работ)|собака[- ](продав|сотрудн|работ)"
    ),
    "тренд-звук/мем": rx(r"trend|meme|lip[- ]?sync|viral (sound|audio|song)|popular (song|audio|sound)|тренд|мем\b|мемн|липсинк"),
    "ответ на комментарий": rx(r"(reply|replying|respond\w*) to (a |the )?comment|answer\w* (a )?comment|ответ на коммент|отвечаю на"),
    "ASMR": rx(r"asmr|satisfying|crunch|хруст|асмр|relaxing sound|soothing"),
    "юмор/сценка": rx(r"humor|humour|funny|comed|skit|joke|prank|parody|absurd|ironic|юмор|смешн|шутк|сценк|пранк|пароди"),
    "обучение/советы": rx(
        r"\btips?\b|how to|guide|explain|educat|tutorial|mistake|lesson|advice|совет|как (выбрать|правильно)|ошибк|лайфхак|life ?hack|обуч"
    ),
    "закулисье": rx(
        r"behind the scenes|day in the life|a day at|working day|\bshift\b|routine|закулис|будни|один день|рабочий день|opening (the|a) (store|shop)|closing"
    ),
    "обзор/рейтинг": rx(r"\breview|ranking|rating|tier list|\btop \d|compar|\bvs\.?\b|обзор|рейтинг|топ[- ]?\d|сравн"),
    "тур по магазину": rx(r"(store|shop|salon) tour|tour of|walk\w* (through|around) (the|a) (store|shop)|экскурси|прогулк\w* по магаз"),
    "диалог продавец–покупатель": rx(
        r"customer (asks|says|comes|wants|walks)|shopkeeper|seller (and|&) customer|clerk|покупатель (спраш|проси|прише)|когда покупатель|когда клиент"
    ),
    "милота/реакция животного": rx(r"\bcute|adorabl|reaction|reacts?\b|милот|реакци"),
}

WHO = {
    "продавец/сотрудник": rx(
        r"employee|staff|worker|shopkeeper|(store|shop|salon|business) owner|owner of the (store|shop)|seller|clerk|cashier|consultant"
        r"|groomer|veterinar|\bvet\b|продав|сотрудн|консультант|грумер|кассир|ветеринар"
    ),
    "покупатель": rx(r"customer|shopper|buyer|\bclient|покупател|клиент"),
    "животное": rx(
        r"\bdogs?\b|\bcats?\b|pupp|kitten|\bfish|bird|parrot|hamster|rabbit|bunny|guinea|reptile|snake|lizard|turtle|frog|animal|\bpets?\b"
        r"|собак|кош|\bкот|щен|рыб|попуг|хомя|кролик|животн|питом"
    ),
    "только товар": rx(r"product|\bbags?\b|\btoys?\b|kibble|treats?\b|collar|leash|package|\bitems?\b|shel(f|ves)|товар|корм|мешок|игрушк|лакомств|упаковк|полк"),
}

PEOPLE_BARRIER = rx(r"two people|second person|another person|multiple people|several people|actors?|\bteam\b|helper|assistant|camera ?(man|operator|person)|two creators|group of")
SKILL_BARRIER = rx(r"trained|training|special (effect|equipment)|professional|studio|vfx|animation|green ?screen|drone|costume|editing skills|multiple cameras|lighting setup")
CTA = rx(
    r"comment|коммент|пиши|напиши|link in bio|ссылк|\bbio\b|follow|подпис|\bsave\b|сохран|\bshare\b|отмет|tag (a|your|someone)|\bdm\b|direct|директ"
    r"|\border\b|заказ|shop now|\bbuy\b|купи|visit|приход|ждём|ждем|запис|\bbook\b"
)
TREND_AUDIO = rx(r"trend|viral|popular|meme|remix|well-known|famous|тренд|популярн")


def difficulty(r):
    time = r.get("effort.time", "").lower()
    d = {"within an hour": 1, "within a day": 3, "within a week": 4, "more than a week": 5}.get(time, 2)
    barrier = r.get("effort.barrier", "")
    if PEOPLE_BARRIER.search(barrier):
        d += 1
    if SKILL_BARRIER.search(barrier):
        d += 1
    pace = (r.get("execution.pacing", "") + " " + r.get("execution.visual_changes", "")).lower()
    if "heavy edits" in pace or "many cuts" in pace:
        d += 1
    return max(1, min(5, d))


def audio_kind(mix):
    m = mix.lower()
    voice, music = "voice" in m, "music" in m
    if voice and music:
        return "голос + музыка"
    if voice:
        return "голос"
    if music:
        return "музыка"
    if "raw" in m or "ambient" in m or "noise" in m:
        return "живой звук"
    return "другое" if m else ""


def level(v):
    v = v.lower()
    return "низкая" if v.startswith("low") else "высокая" if v.startswith("high") else "средняя" if v.startswith("moderate") else ""


def bucket_of(seconds):
    if seconds is None:
        return ""
    return "0-10" if seconds <= 10 else "10-20" if seconds <= 20 else "20-40" if seconds <= 40 else "40+"


def enrich(r):
    text = " ".join(
        r.get(k, "")
        for k in ("handle", "caption", "concept", "niche", "format.template", "format.style", "hook_0_3s.visual", "hook_0_3s.text", "effort.barrier")
    )
    trade = PET_TRADE.search(text) and not ZOO.search(text)
    goods = PET_GOODS.search(text) and PET.search(text) and COMMERCE.search(text)
    r["relevant"] = int(bool(trade or goods))
    fmt_text = " ".join(r.get(k, "") for k in ("caption", "concept", "format.template", "format.style", "hook_0_3s.visual", "hook_0_3s.text", "hook_0_3s.audio"))
    r["formats"] = "; ".join(name for name, pat in FORMATS.items() if pat.search(fmt_text))
    who_text = " ".join(r.get(k, "") for k in ("concept", "hook_0_3s.visual"))
    r["who_in_frame"] = "; ".join(name for name, pat in WHO.items() if pat.search(who_text))
    hook_text = r.get("hook_0_3s.text", "").strip()
    r["has_text_hook"] = int(bool(hook_text) and hook_text.lower() not in {"none", "n/a", "-"})
    r["has_text_overlay"] = int(bool(r.get("execution.text_overlays")))
    r["audio_kind"] = audio_kind(r.get("audio.audio_mix", ""))
    r["trend_audio"] = int(bool(TREND_AUDIO.search(r.get("hook_0_3s.audio", "") + " " + r.get("audio.music_track", ""))))
    r["cuts_level"] = level(r.get("execution.visual_changes", ""))
    r["difficulty"] = difficulty(r)
    r["cta_in_caption"] = int(bool(CTA.search(r.get("caption", ""))))
    r["hashtags"] = " ".join(dict.fromkeys(re.findall(r"#[\wЀ-ӿ]+", r.get("caption", ""))))
    r["lang"] = "ru" if re.search(r"[Ѐ-ӿ]", r.get("caption", "") + r.get("hook_0_3s.text", "")) else "en/other"
    r["virality"] = round(r["views"] / r["followers"], 3) if r.get("followers") else ""
    return r


COLUMNS = [
    # Requested columns (likes, comments, date are not returned by vidIQ search).
    "url", "account", "followers", "views", "likes", "comments", "duration_s", "date", "caption", "hashtags", "audio",
    # Metrics and segments.
    "virality", "outlier_x", "median_views", "segment", "relevant", "duration_bucket", "lang", "queries",
    # Labels derived from vidIQ's AI description.
    "formats", "who_in_frame", "has_text_hook", "hook_visual", "hook_text", "hook_audio", "trend_audio",
    "has_text_overlay", "text_overlays", "audio_kind", "audio_mix", "sfx_present", "pacing", "cuts_level",
    "difficulty", "effort_time", "effort_barrier", "cta_in_caption", "concept", "niche", "template", "format_style",
    "intended_value", "is_looped", "culture_region", "demographics", "analysis_basis",
]


def row(r):
    return {
        "url": r["url"], "account": "@" + r["handle"], "followers": int(r["followers"]), "views": int(r["views"]),
        "likes": "", "comments": "", "duration_s": r.get("duration_s") or "", "date": "",
        "caption": r.get("caption", ""), "hashtags": r["hashtags"],
        "audio": r.get("audio.music_track") or r.get("audio.audio_mix", ""),
        "virality": r["virality"], "outlier_x": r["outlier_x"], "median_views": int(r["median_views"]),
        "segment": r.get("segment", ""), "relevant": r["relevant"], "duration_bucket": r["duration_bucket"],
        "lang": r["lang"], "queries": r["queries"], "formats": r["formats"], "who_in_frame": r["who_in_frame"],
        "has_text_hook": r["has_text_hook"], "hook_visual": r.get("hook_0_3s.visual", ""),
        "hook_text": r.get("hook_0_3s.text", ""), "hook_audio": r.get("hook_0_3s.audio", ""),
        "trend_audio": r["trend_audio"], "has_text_overlay": r["has_text_overlay"],
        "text_overlays": r.get("execution.text_overlays", ""), "audio_kind": r["audio_kind"],
        "audio_mix": r.get("audio.audio_mix", ""), "sfx_present": r.get("audio.sfx_present", ""),
        "pacing": r.get("execution.pacing", ""), "cuts_level": r["cuts_level"], "difficulty": r["difficulty"],
        "effort_time": r.get("effort.time", ""), "effort_barrier": r.get("effort.barrier", ""),
        "cta_in_caption": r["cta_in_caption"], "concept": r.get("concept", ""), "niche": r.get("niche", ""),
        "template": r.get("format.template", ""), "format_style": r.get("format.style", ""),
        "intended_value": r.get("format.intended_value", ""), "is_looped": r.get("format.is_looped", ""),
        "culture_region": r.get("audience.culture_region", ""), "demographics": r.get("audience.demographics", ""),
        "analysis_basis": "vidIQ AI-описание видео + метаданные (видео не скачивалось)",
    }


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def main():
    records = [r for f in sorted(RAW.glob("q*.txt")) for r in parse_file(f)]
    ig, tiktok = {}, {}
    for r in records:
        target = ig if r["platform"] == "Instagram" else tiktok
        key = r["id"]
        if key not in target:
            r["queries"], r["buckets"] = [], set()
            target[key] = r
        kept = target[key]
        kept["queries"].append(r["qid"])
        if r["bucket"]:
            kept["buckets"].add(r["bucket"])
        if kept.get("duration_s") is None and r.get("duration_s") is not None:
            kept["duration_s"] = r["duration_s"]

    for r in list(ig.values()) + list(tiktok.values()):
        r["queries"] = " ".join(dict.fromkeys(r["queries"]))
        # Exact duration when vidIQ gives it, otherwise the search filter's range.
        r["duration_bucket"] = bucket_of(r.get("duration_s")) or "/".join(sorted(r["buckets"]))
        enrich(r)

    # Segments by virality among relevant reels: top 30% and bottom 20%.
    rel = sorted(r["virality"] for r in ig.values() if r["relevant"] and r["virality"] != "")
    top_cut, bottom_cut = percentile(rel, 0.70), percentile(rel, 0.20)
    for r in ig.values():
        if r["relevant"] and r["virality"] != "":
            r["segment"] = "top30" if r["virality"] >= top_cut else "bottom20" if r["virality"] <= bottom_cut else "middle"

    rows = sorted((row(r) for r in ig.values()), key=lambda x: (-x["relevant"], -(x["virality"] or 0)))
    with open(ROOT / "data.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    WORK.mkdir(exist_ok=True)
    trows = sorted((row(r) for r in tiktok.values()), key=lambda x: -(x["virality"] or 0))
    with open(WORK / "tiktok.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(trows)

    n_rel = sum(r["relevant"] for r in ig.values())
    print(f"parsed records: {len(records)}  instagram unique: {len(ig)}  tiktok unique: {len(tiktok)}")
    print(f"relevant instagram: {n_rel}  with exact duration: {sum(1 for r in ig.values() if r.get('duration_s') is not None)}")
    print(f"virality cut-offs among relevant: top30 >= {top_cut:.2f}  bottom20 <= {bottom_cut:.2f}")


if __name__ == "__main__":
    main()
