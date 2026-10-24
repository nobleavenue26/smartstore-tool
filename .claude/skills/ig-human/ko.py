#!/usr/bin/env python3
"""
ko.py - Korean support shared by caption.py, hookscore.py, beats.py,
detect.py and humanize.py.

Every pattern in the English tools is written for Latin text: \\b word
boundaries, capitalised proper nouns, apostrophe contractions, "comment WORD".
Korean has none of those. Particles glue onto words (패딩을, 38만원에), names
are not capitalised, and a syllable is a better unit of speech than a word.
This module carries the Korean equivalents. The data lives in ko.json so it
can be edited like slop.json.

Nothing here changes what happens to text with no Hangul in it.
"""

import json
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "ko.json")

HANGUL_RE = re.compile(r"[가-힣ㄱ-ㅎㅏ-ㅣ]")
SYLLABLE_RE = re.compile(r"[가-힣]")
TOKEN_RE = re.compile(r"[A-Za-z0-9$%'’\-가-힣]+")
LATIN_NAME_RE = re.compile(r"\b[A-Z][A-Za-z]{2,}\b")

with open(DATA_PATH, encoding="utf-8") as _fh:
    DATA = json.load(_fh)

NUMBER_RE = re.compile(r"(?<![\d.,])\d[\d,]*(?:\.\d+)?\s?(?:" + DATA["number_units"] + r")?")
FORMAL_END_RE = re.compile(DATA["formal_endings"])
ASKS = [(re.compile(a["regex"], re.IGNORECASE), a["name"]) for a in DATA["asks"]]
DEALBREAKERS = [(re.compile(d["regex"], re.MULTILINE), d["msg"]) for d in DATA["dealbreakers"]]
FILLER_TAGS = set(DATA["filler_tags"])
_PARTICLES = sorted(DATA["particles"], key=len, reverse=True)


def has_hangul(text):
    return bool(HANGUL_RE.search(text))


def syllables(text):
    return len(SYLLABLE_RE.findall(text))


def tokens(text):
    return TOKEN_RE.findall(re.sub(r"(?<=\d),(?=\d)", "", text))


def spoken_units(text):
    """Speech length in English-word equivalents.

    Latin tokens count one each. Hangul counts by syllable, at
    syllables_per_word syllables to a word (2.0 by default: about 5.5
    syllables a second against 2.75 English words a second).
    """
    latin = [t for t in tokens(text) if not HANGUL_RE.search(t)]
    return len(latin) + syllables(text) / DATA["syllables_per_word"]


def display_width(text):
    """Columns a string takes on screen. Hangul and other wide glyphs are 2."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in text)


def cut_width(text, width):
    """The longest prefix that fits in `width` columns."""
    used = 0
    for i, c in enumerate(text):
        used += display_width(c)
        if used > width:
            return text[:i]
    return text


def wrap_width(line, width):
    """textwrap.wrap, but measured in columns so Hangul lines fit the box."""
    out, cur = [], ""
    for word in line.split(" "):
        cand = word if not cur else cur + " " + word
        if display_width(cand) <= width:
            cur = cand
            continue
        if cur:
            out.append(cur)
        while display_width(word) > width:
            head = cut_width(word, width)
            out.append(head)
            word = word[len(head):]
        cur = word
    if cur:
        out.append(cur)
    return out or [""]


def pad(text, width):
    return text + " " * max(0, width - display_width(text))


def strip_particle(token):
    """패딩을 -> 패딩, 38만원에 -> 38만원. Leaves at least one syllable."""
    for p in _PARTICLES:
        if token.endswith(p) and len(token) > len(p):
            return token[: -len(p)]
    return token


def _squash(text):
    return re.sub(r"\s+", "", text).lower()


def brands(text):
    """Brand names found in the text, spaces ignored (골든 구스 = 골든구스)."""
    flat = _squash(text)
    found = []
    for b in DATA["brands"]:
        key = _squash(b)
        if HANGUL_RE.search(b):
            hit = key in flat
        else:
            hit = re.search(r"(?<![A-Za-z])" + re.escape(key) + r"(?![A-Za-z])", flat) is not None
        if hit:
            found.append(b)
    return found


def numbers(text):
    return [n.strip() for n in NUMBER_RE.findall(text) if n.strip()]


def concrete(text):
    """Numbers, brand names, Latin model names and spoken quantities."""
    hits = numbers(text) + brands(text)
    brand_low = {b.lower() for b in brands(text)}
    hits += [w for w in set(LATIN_NAME_RE.findall(text)) if w.lower() not in brand_low]
    hits += [w for w in DATA["spoken_numbers"] + DATA["money_words"] if w in text]
    return hits


def stakes(text):
    padded = text + " "
    return sorted({s.strip() for s in DATA["stakes"] if s in padded})


def is_payload(token):
    return (bool(NUMBER_RE.match(token)) or bool(brands(token))
            or any(s.strip() and s.strip() in token for s in DATA["stakes"])
            or any(w in token for w in DATA["money_words"] + DATA["spoken_numbers"]))


def weak_opener(text):
    t = tokens(text)
    if not t:
        return None
    first = strip_particle(t[0])
    for w in DATA["weak_openers"]:
        if t[0] == w or first == w:
            return w
    return None


def address(text):
    """(score, detail) on the same scale as hookscore.check_address."""
    padded = " " + text + " "
    if any(w in padded for w in DATA["address"]):
        return 100.0, "speaks to the viewer (당신/여러분/님)"
    if any(e in text for e in DATA["imperative_endings"]):
        return 90.0, "imperative (~세요/~하지 마)"
    if any(w in padded for w in DATA["first_person"]):
        return 70.0, "first person (저/제가/우리), no viewer named"
    return 35.0, "third person, nobody in the room"


def lexicon_pattern(find, deleting=False):
    """Lexicon entries: \\b for English, a no-Hangul-before guard for Korean.

    Korean words take particles on the end, so there is no trailing boundary.
    When the entry is being deleted (결론적으로, -> nothing), its comma goes
    with it so no orphaned ", " is left mid-sentence.
    """
    body = re.escape(find).replace(r"\ ", r"\s+")
    if HANGUL_RE.search(find):
        return re.compile(r"(?<![가-힣])" + body + (r"(?:\s*,)?" if deleting else ""))
    return re.compile(r"\b" + body + r"\b", re.IGNORECASE)
