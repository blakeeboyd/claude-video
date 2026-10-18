#!/usr/bin/env python3
"""Check a watch note against its transcript before trusting it.

Flags quotes that are not in the transcript, timestamps past the end of the
video, and [[wikilinks]] with no matching file under a vault root.
Usage: check_note.py NOTE.md TRANSCRIPT.md [VAULT_ROOT]
"""
import re
import sys
from pathlib import Path


def norm(s):
    s = s.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"\*\*\[[\d:]+\]\*\*|\[music\]|\[laughter\]|>>", " ", s)
    return re.sub(r"[^a-z0-9']+", " ", s).strip()


def seconds(ts):
    s = 0
    for part in ts.split(":"):
        s = s * 60 + int(part)
    return s


def check(note, transcript, vault=None):
    problems = []
    text = norm(transcript)
    own = note.split("### Related sources")[0]  # quotes from other sources live below this
    for q in re.findall(r'"(\S[^"\n]{10,}\S)"', own):
        if norm(q) not in text:
            problems.append(f"quote not in transcript: \"{q}\"")
    stamps = [seconds(t) for t in re.findall(r"\*\*\[([\d:]+)\]\*\*", transcript)]
    end = max(stamps) if stamps else 0
    for t in set(re.findall(r"(?<![\d$])(\d{1,2}:\d{2}(?::\d{2})?)(?![\d])", note)):
        if seconds(t) > end + 60:
            problems.append(f"timestamp past end of video: {t}")
    if vault:
        names = {p.stem for p in Path(vault).rglob("*.md")}
        for link in set(re.findall(r"\[\[([^\]|#]+)", note)):
            if link.strip() not in names:
                problems.append(f"wikilink has no file: [[{link}]]")
    return problems


if __name__ == "__main__":
    if len(sys.argv) == 1:
        tr = '**[0:00]** She said "hello there friend" today.\n\n**[1:30]** End.'
        assert check('"hello there friend" at 0:00', tr) == []
        assert check('"goodbye there friend" at 9:00', tr) == [
            'quote not in transcript: "goodbye there friend"',
            "timestamp past end of video: 9:00",
        ]
        print("ok")
    else:
        vault = sys.argv[3] if len(sys.argv) > 3 else None
        found = check(Path(sys.argv[1]).read_text(), Path(sys.argv[2]).read_text(), vault)
        print("\n".join(found) if found else "no problems found")
        sys.exit(1 if found else 0)
