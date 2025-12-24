#!/usr/bin/env python3
"""
get_all_words_from_json.py

Load a JSON file that contains an array of objects with at least a "word" key
(e.g., your bot db.json), and print the list of words (one per line) to stdout.
All other fields are ignored.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, List


def extract_words(data: Any) -> List[str]:
    if not isinstance(data, list):
        raise ValueError("Expected the JSON top-level structure to be a list.")
    words: List[str] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        w = item.get("word")
        if isinstance(w, str) and w.strip():
            words.append(w.strip())
    return words


def main() -> None:
    json_path = Path(__file__).parent.parent / "database" / "db.json"

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    words = extract_words(data)
    print(f'found {len(words)} words in {json_path}:')
    print('\n\n[')
    for w in words:
        print(f"'{w}',")
    print(']')



if __name__ == "__main__":
    main()
