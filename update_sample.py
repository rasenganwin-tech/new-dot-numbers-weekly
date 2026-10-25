#!/usr/bin/env python3
"""Regenerate sample/new-usdot-carriers-sample.csv from the newest weekly zip.

    python3 update_sample.py [folder-with-weekly-zips]

Takes 100 rows (all columns) from the newest "New USDOT carriers <start> to <end>.zip", spread evenly across the
week, business-entity names only. Personal fields are partly masked in this free sample (officer -> initials,
email -> domain, house numbers and the last 4 cell digits hidden); the paid file has them in full.
Also rewrites the date line between the SAMPLE markers in README.md. Stdlib only.
"""
import csv
import io
import os
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SRC = HERE.parents[1] / "ventures" / "15" / "products" / "new-usdot-registrations-weekly"
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NEWDOT_ZIP_DIR", DEFAULT_SRC))
OUT = HERE / "sample" / "new-usdot-carriers-sample.csv"
N = 100
ENTITY = re.compile(r"\b(LLC|L\.?L\.?C|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PLLC)\.?,?\s*$", re.I)


def initials(name):
    return " ".join(p[0].upper() + "." for p in re.findall(r"[A-Za-z]+", name or ""))


def mask_email(e):
    return "***@" + e.split("@", 1)[1] if "@" in (e or "") else ""


def mask_street(s):
    return re.sub(r"\d+", "***", s or "")


def mask_cell(c):
    d = re.sub(r"\D", "", c or "")
    return f"{d[:3]}-{d[3:6]}-****" if len(d) == 10 else ""


def newest_zip():
    pat = re.compile(r"New USDOT carriers (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})\.zip$")
    zips = sorted((m.group(2), m.group(1), p) for p in SRC.glob("New USDOT carriers * to *.zip") if (m := pat.search(p.name)))
    if not zips:
        sys.exit(f"no weekly zip found in {SRC}")
    end, start, path = zips[-1]
    return path, start, end


def main():
    path, start, end = newest_zip()
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        reader = csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8-sig"))
        cols, rows = reader.fieldnames, list(reader)
    pool = [r for r in rows if ENTITY.search(r.get("Legal Name", "")) and r.get("Phone") and "@" in r.get("Email", "")] or rows
    step = max(len(pool) / N, 1)
    picked = [pool[int(i * step)] for i in range(min(N, len(pool)))]
    picked.sort(key=lambda r: int(r["USDOT Number"]) if r["USDOT Number"].isdigit() else 0)
    for r in picked:
        r["Company Officer"] = initials(r.get("Company Officer"))
        r["Email"] = mask_email(r.get("Email"))
        r["Street Address"] = mask_street(r.get("Street Address"))
        r["Cell Phone"] = mask_cell(r.get("Cell Phone"))
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(picked)
    readme = HERE / "README.md"
    if readme.exists():
        line = f"<!--SAMPLE-->Current sample: {len(picked)} of the {len(rows):,} carriers registered {start} to {end}.<!--/SAMPLE-->"
        readme.write_text(re.sub(r"<!--SAMPLE-->.*?<!--/SAMPLE-->", line, readme.read_text(), flags=re.S))
    print(f"wrote {len(picked)} rows from {path.name} ({start} to {end}, {len(rows)} carriers) to {OUT.relative_to(HERE)}")


if __name__ == "__main__":
    main()
