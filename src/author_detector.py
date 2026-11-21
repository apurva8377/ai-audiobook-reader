import re
from pathlib import Path
import pymupdf

FEMALE_NAMES = {
    "gail", "holly", "freida", "jane", "emily", "charlotte", "agatha", "jk", "joanne",
    "suzanne", "stephenie", "veronica", "sarah", "colleen", "taylor", "sally", "celeste",
    "madeline", "alice", "virginia", "maya", "toni", "harper", "louisa", "mary", "anne",
    "elizabeth", "margaret", "daphne", "gillian", "paula", "kristin", "liane", "ruth",
    "lucy", "claire", "hannah", "sophie", "chitra", "sudha", "arundhati", "kiran",
    "anita", "preeti", "nikita", "savi", "roshani", "kavita", "meera", "divya", "apurva",
    "eleanor", "rachel", "rebecca", "jennifer", "laura", "emma", "olivia", "ava", "mia",
    "amelia", "isabella", "charlotte", "grace", "chloe", "victoria", "nora", "lily", "zoe"
}

MALE_NAMES = {
    "chetan", "blake", "matt", "stephen", "george", "jrr", "john", "arthur", "charles",
    "ernest", "william", "leo", "fyodor", "scott", "khaled", "paulo", "dan",
    "james", "lee", "harlan", "michael", "neil", "terry", "brandon", "rick",
    "roald", "cs", "mark", "herman", "oscar", "bram", "hg", "jules", "alex", "andy",
    "amish", "devdutt", "ruskin", "rk", "vikram", "salman", "amitav", "aravind", "ravinder",
    "durjoy", "robert", "david", "richard", "thomas", "peter", "paul", "kevin", "brian"
}


def _classify_name(first_name: str) -> str:
    clean = re.sub(r"[^a-zA-Z]", "", first_name).lower()
    if not clean or len(clean) < 2:
        return "unknown"
    if clean in FEMALE_NAMES:
        return "female"
    if clean in MALE_NAMES:
        return "male"
    if clean.endswith(("a", "i", "ee", "ia", "na", "ta", "ka", "ra", "ya", "lyn", "elle", "ette")):
        return "female"
    return "unknown"


def detect_author_info(pdf_path: Path, fallback_title: str) -> dict:
    author = ""
    gender = "unknown"

    with pymupdf.open(pdf_path) as doc:
        meta = doc.metadata or {}
        raw_author = (meta.get("author") or "").strip()
        if raw_author and raw_author.lower() not in {"unknown", "admin", "user", "calibre", "none"}:
            author = raw_author
            gender = _classify_name(author.split()[0])

        # Scan first 8 pages for "by Author Name" (case-insensitive, supports ALL CAPS)
        front_text = ""
        for i in range(min(8, len(doc))):
            front_text += "\n" + doc[i].get_text("text")

        if gender == "unknown":
            match = re.search(
                r"(?:^|\n)\s*(?:by|BY|By)\s+([A-Za-z\.]+(?:\s+[A-Za-z\.]+){1,2})",
                front_text,
            )
            if match:
                candidate = match.group(1).strip()
                g = _classify_name(candidate.split()[0])
                if g != "unknown":
                    author = candidate.title()
                    gender = g

        # Scan standalone lines on title/copyright pages (first 6 pages) for known author names
        if gender == "unknown":
            for line in front_text.splitlines()[:120]:
                words = [w for w in re.split(r"[^a-zA-Z]+", line.strip()) if w]
                if 2 <= len(words) <= 3:
                    g = _classify_name(words[0])
                    if g != "unknown":
                        author = " ".join(words).title()
                        gender = g
                        break

    # Check filename as backup
    if gender == "unknown":
        for word in re.split(r"[^a-zA-Z]+", fallback_title):
            g = _classify_name(word)
            if g != "unknown":
                author = word.title()
                gender = g
                break

    recommended_voice = "en-GB-SoniaNeural" if gender == "female" else "en-GB-RyanNeural"
    return {
        "author": author or "Unknown Author",
        "gender": gender,
        "recommended_voice": recommended_voice,
    }
