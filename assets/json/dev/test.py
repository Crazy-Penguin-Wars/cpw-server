import json
import sys
from pathlib import Path
import os

NL_FILE = "tuxwars_config_nl.json"        # complete Dutch file
EN_FILE = "LAST_BEFORE_NEW_ASSETS_tuxwars_config_en.json"        # partial English file
OUT_FILE = "en_merged.json"

p = Path(__file__).parent

def load(path):
    with open(os.path.join(p, path), "r", encoding="utf-8-sig") as f:
        return json.load(f)


def fmt_entry(entry):
    """Format one entry on a single line, like the originals: { "ID":"X", "en":"Y" }"""
    parts = [
        f'{json.dumps(k, ensure_ascii=False)}:{json.dumps(v, ensure_ascii=False)}'
        for k, v in entry.items()
    ]
    return "{ " + ", ".join(parts) + " }"


def main():
    nl = load(NL_FILE)
    en = load(EN_FILE)

    nl_tid = nl["TID"]
    en_tid = en["TID"]

    out_tid = {}
    replaced = placeholder = 0

    for key, nl_entry in nl_tid.items():
        # Keep the type-definition row from the English file
        if key == "$DATA_TYPE":
            out_tid[key] = en_tid.get(key, nl_entry)
            continue

        en_entry = en_tid.get(key)
        if en_entry and "en" in en_entry:
            # English version exists -> use it
            new_entry = dict(en_entry)
            replaced += 1
        else:
            # No English version -> keep Dutch text, but relabel nl -> en
            new_entry = {}
            for k, v in nl_entry.items():
                new_entry["en" if k == "nl" else k] = v
            placeholder += 1

        out_tid[key] = new_entry

    # Write in the same one-entry-per-line style as the source files
    lines = []
    if "ConfigVersion" in en:
        lines.append(f'  "ConfigVersion":{json.dumps(en["ConfigVersion"])},')
    lines.append('  "TID": {')

    items = list(out_tid.items())
    for i, (key, entry) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        lines.append(f'    {json.dumps(key, ensure_ascii=False)}: {fmt_entry(entry)}{comma}')

    lines.append("  }")
    text = "{\n" + "\n".join(lines) + "\n}\n"

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Done. {replaced} taken from English, {placeholder} Dutch placeholders.")
    print(f"Written to {OUT_FILE}")


if __name__ == "__main__":
    sys.exit(main())