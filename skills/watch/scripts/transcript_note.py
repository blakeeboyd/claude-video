#!/usr/bin/env python3
"""Turn a watch report's transcript into clean ~30 s paragraphs (markdown).

YouTube rolling captions repeat each line inside the next one; this strips
the overlap so every word appears once. Usage: transcript_note.py REPORT.md
"""
import re
import sys

LINE = re.compile(r"^\[(\d+:\d{2}(?::\d{2})?)\]\s*(.*)$")


def seconds(ts):
    s = 0
    for part in ts.split(":"):
        s = s * 60 + int(part)
    return s


def new_part(prev, cur):
    """The part of cur not already said at the end of prev."""
    if cur in prev:
        return ""
    for k in range(min(len(prev), len(cur)), 0, -1):
        if prev.endswith(cur[:k]) and (k == len(cur) or cur[k] == " "):
            return cur[k:].strip()
    return cur


def clean(lines, block=30):
    paras, prev, start, words = [], "", None, []
    for ts, text in lines:
        add = new_part(prev, text)
        prev = text
        if not add:
            continue
        if start is None:
            start = ts
        cut = None
        if seconds(ts) - seconds(start) >= block:
            ends = [m.end() for m in re.finditer(r'[.?!]"?(?=\s|$)', add)]
            cut = ends[0] if ends else None
            # Unpunctuated auto-captions never end a sentence: break anyway at 2x block.
            if cut is None and seconds(ts) - seconds(start) >= 2 * block:
                cut = len(add)
        if cut is None:
            words.append(add)
            continue
        words.append(add[:cut])
        paras.append(f"**[{start}]** " + " ".join(words))
        rest = add[cut:].strip()
        start, words = (ts, [rest]) if rest else (None, [])
    if words:
        paras.append(f"**[{start}]** " + " ".join(words))
    return "\n\n".join(paras)


def main():
    lines = [m.groups() for m in map(LINE.match, open(sys.argv[1], encoding="utf-8")) if m]
    print(clean(lines))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo = [("0:00", "a b"), ("0:01", "a b c d"), ("0:02", "c d"), ("0:31", "c d e. g"), ("0:32", "f")]
        out = clean(demo)
        assert out == "**[0:00]** a b c d e.\n\n**[0:31]** g f", out
        assert new_part("x y", "z") == "z"
        flat = clean([("0:00", "a"), ("0:40", "b"), ("1:00", "c"), ("1:10", "d")])
        assert flat == "**[0:00]** a b c\n\n**[1:10]** d", flat
        print("ok")
    else:
        main()
