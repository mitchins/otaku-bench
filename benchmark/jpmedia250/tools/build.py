#!/usr/bin/env python3
"""Build the curated JP-Media-250 corpus from its editable TSV source sections."""
from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = [
    ("01_ellipsis.tsv", "ellipsis_coreference"),
    ("02_keigo.tsv", "keigo_politeness"),
    ("03_idioms.tsv", "idiom_proverb"),
    ("04_implicature.tsv", "indirectness_pragmatics"),
    ("05_voices.tsv", "dialect_character_voice"),
    ("06_wordplay.tsv", "wordplay_irony"),
    ("07_mimetics.tsv", "mimetics_onomatopoeia"),
    ("08_culture.tsv", "culture_institutions"),
    ("09_subtext.tsv", "emotion_subtext"),
    ("10_genre.tsv", "genre_literary_structure"),
]
MEDIA = ["visual_novel", "light_novel", "game", "anime"]
ALTERNATES = {
    1: ["You go ahead."], 2: ["That's enough."], 3: ["You handle that side."],
    5: ["That belongs to me."], 7: ["Three minutes remaining."],
    8: ["Wrong way!"], 10: ["Everything was supposed to be okay."],
    13: ["Still there?"], 16: ["You think that's enough to make up for it?"],
    17: ["I used to love you. Maybe I still do."],
    26: ["Just a moment, please."], 29: ["Excuse me, I'm leaving for the day."],
    31: ["The teacher has arrived."], 33: ["Would you mind verifying this?"],
    36: ["The manager is back already."],
    41: ["With all due respect, I disagree with that decision."],
    48: ["If you were going to refuse, why accept this morning?"],
    51: ["I'm absolutely swamped today."], 53: ["She won't spill the beans."],
    56: ["Let's forgive and forget."], 58: ["I'll let it slide this once."],
    59: ["That's a hard truth to hear."], 61: ["Fixing this bridge overnight will be hard work."],
    62: ["Quit wasting time!"], 66: ["I feel too guilty to go back to that house."],
    69: ["If we dig any deeper, we may make things worse."],
    72: ["We can't afford to be picky. Let's ask the enemy for help."],
    76: ["Sorry, not today."], 79: ["Not bad, although..."],
    80: ["It's getting late. I should go."], 83: ["Some excuse."],
    88: ["Pretty good, considering it's you."],
    91: ["Let's begin without the people who haven't arrived."],
    95: ["Don't expect me to stop you. Just keep a way home open."],
    101: ["Really?"], 102: ["Damn, I won't make it!"],
    103: ["What the heck!"], 105: ["I never heard about that!"],
    109: ["I think it's over that way, but I'm not sure."],
    116: ["Then you'd better keep your word."],
    126: ["Did you really just say that dolphin pun?"],
    133: ["Don't leave your chopsticks on the bridge's edge."],
    142: ["Trying to make small talk just made it worse."],
    150: ["When you say 'fated partner,' did fate choose or force the choice?"],
    151: ["My heart is racing."], 153: ["He stared straight at me."],
    156: ["I barely made it."], 159: ["She quietly released my hand."],
    162: ["He turned it down flat."], 163: ["The poison is gradually taking effect."],
    165: ["My hands are all sticky and the sword keeps slipping."],
    168: ["I've got this vague unsettled feeling for no reason."],
    175: ["I didn't know whether it was the earth or my beliefs that had shaken."],
    176: ["Time to eat."], 177: ["Thank you for the food."],
    178: ["See you later!"], 179: ["I'm back."],
    181: ["I've spent all my New Year's money already."],
    188: ["Even seniors can't get away with everything."],
    195: ["Everyone endorsed it publicly, but no one was willing to act."],
    201: ["I'm not upset."], 205: ["See you in the morning."],
    207: ["It's not as if I was waiting for you!"],
    215: ["I thought I could smile when I saw you off."],
    220: ["I'm not forgiving you. I'm just too tired to keep blaming you."],
    226: ["Let's save the game first."], 227: ["A laugh came from beyond the door."],
    228: ["Not enough magic power."],
    234: ["I could have sworn the relationship meter went up."],
    236: ["The door opens only from this side."],
    241: ["We didn't get away. They let us go."],
    248: ["She might not have lied, but that doesn't mean she told us everything."],
}

COLUMNS = ["id", "split", "medium", "genre", "difficulty", "primary_challenge",
           "tags", "japanese", "english_reference", "alternate_references",
           "scene_context", "translation_note", "provenance", "review_status"]


def build() -> list[dict]:
    records = []
    for section_index, (filename, category) in enumerate(SECTIONS):
        p = ROOT / "data" / "sections" / filename
        lines = p.read_text(encoding="utf-8").splitlines()
        if len(lines) != 25:
            raise ValueError(f"{filename} expected 25 records; got {len(lines)}")
        for position, line in enumerate(lines):
            cells = line.split("|")
            if len(cells) != 6:
                raise ValueError(f"{filename}:{position+1} expected six fields, got {len(cells)}")
            japanese, english, scene, note, tags, genre = [c.strip() for c in cells]
            if not all([japanese, english, scene, note, tags, genre]):
                raise ValueError(f"empty field {filename}:{position+1}")
            number = len(records) + 1
            records.append({
                "id": f"JMB-{number:03d}",
                # one held-out calibration example per challenge x difficulty cell
                "split": "dev" if position % 5 == 0 else "eval",
                "medium": MEDIA[(number - 1) % 4],
                "genre": genre,
                "difficulty": position // 5 + 1,
                "primary_challenge": category,
                "tags": tags.split(","),
                "japanese": japanese,
                "english_reference": english,
                "alternate_references": ALTERNATES.get(number, []),
                "scene_context": scene,
                "translation_note": note,
                "provenance": "independently_authored_original",
                "review_status": "editorial_draft_not_independently_native_reviewed",
            })
    validate(records)
    return records


def validate(records: list[dict]) -> None:
    assert len(records) == 250
    assert len({r["japanese"] for r in records}) == 250, "duplicate Japanese source"
    assert len({r["id"] for r in records}) == 250
    assert Counter(r["difficulty"] for r in records) == {n: 50 for n in range(1, 6)}
    assert Counter(r["primary_challenge"] for r in records) == {name: 25 for _, name in SECTIONS}
    assert Counter(r["medium"] for r in records) == {
        "visual_novel": 63, "light_novel": 63, "game": 62, "anime": 62}
    assert Counter(r["split"] for r in records) == {"dev": 50, "eval": 200}
    assert all(len(r["tags"]) >= 2 for r in records)
    assert all(1 <= r["difficulty"] <= 5 for r in records)
    assert all(r["provenance"] == "independently_authored_original" for r in records)
    assert len({(r["primary_challenge"],r["difficulty"]) for r in records if r["split"] == "dev"}) == 50


def dump_csv(path: Path, records: list[dict]):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=COLUMNS)
        wr.writeheader()
        for r in records:
            o = r.copy()
            o["tags"] = ";".join(r["tags"])
            o["alternate_references"] = " || ".join(r["alternate_references"])
            wr.writerow(o)


def dump_jsonl(path: Path, records: list[dict]):
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def main():
    records = build()
    out = ROOT / "data" / "build"
    out.mkdir(parents=True, exist_ok=True)
    dump_csv(out / "jpmedia250_gold.csv", records)
    dump_jsonl(out / "jpmedia250_gold.jsonl", records)
    dump_jsonl(out / "jpmedia250_blind_japanese_only.jsonl", [{
        "id": r["id"], "split": r["split"], "medium": r["medium"],
        "genre": r["genre"], "difficulty": r["difficulty"],
        "primary_challenge": r["primary_challenge"], "japanese": r["japanese"],
    } for r in records])
    dump_jsonl(out / "jpmedia250_blind_with_context.jsonl", [{
        "id": r["id"], "split": r["split"], "medium": r["medium"],
        "genre": r["genre"], "difficulty": r["difficulty"],
        "primary_challenge": r["primary_challenge"], "japanese": r["japanese"],
        "scene_context": r["scene_context"],
    } for r in records])
    md = {
        "dataset": "JP-Media-250", "version": "1.0.0-draft", "count": len(records),
        "provenance": "250 original Japanese sentences independently authored for this benchmark; none claimed sourced from published media",
        "review_status": "draft, not independently verified by native Japanese reviewers",
        "construction": "10 categories x 25 entries, sorted in each section by 5 heuristic difficulty bins x 5 items, medium assigned round-robin",
        "splits": dict(Counter(r["split"] for r in records)),
        "media": dict(Counter(r["medium"] for r in records)),
        "difficulty": {str(k): v for k,v in sorted(Counter(r["difficulty"] for r in records).items())},
        "categories": dict(Counter(r["primary_challenge"] for r in records)),
        "genres": dict(Counter(r["genre"] for r in records)),
        "tags": dict(Counter(tag for r in records for tag in r["tags"])),
        "primary_sha256": hashlib.sha256((out / "jpmedia250_gold.jsonl").read_bytes()).hexdigest(),
    }
    (out / "manifest.json").write_text(json.dumps(md, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:md[k] for k in ("count","splits","media","difficulty","categories","primary_sha256")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
