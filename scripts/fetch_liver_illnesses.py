# -*- coding: utf-8 -*-
"""Download egov illnesses and keep only liver-related ICD-10 rows."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

COOKIE_FILE = RAW / "_egov_cookies.txt"
OUT_JSON = PROCESSED / "illnesses_liver.json"
OUT_CSV = PROCESSED / "illnesses_liver.csv"
OUT_SUMMARY = PROCESSED / "illnesses_liver_summary.json"

PREFIXES = [
    "B15",
    "B16",
    "B17",
    "B18",
    "B19",
    "K70",
    "K71",
    "K72",
    "K73",
    "K74",
    "K75",
    "K76",
    "K77",
    "C22",
]
LIVER_RE = re.compile(r"^(B1[5-9]|K7[0-7]|C22)(\.|$)", re.I)
BASE = "https://data.egov.kz/datasets/getdata"


def load_cookies() -> str:
    raw = COOKIE_FILE.read_text(encoding="utf-8").strip()
    # Accept either full Cookie header or one cookie per line name=value
    if "\n" in raw and "Cookie:" not in raw:
        parts = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts.append(line.split(";", 1)[0].strip())
        return "; ".join(parts)
    return raw.replace("Cookie:", "").strip()


def is_liver(code: object) -> bool:
    if code is None:
        return False
    c = str(code).upper().replace(" ", "")
    return bool(LIVER_RE.match(c))


def fetch_page(cookie: str, text: str, page: int, count: int = 20) -> dict:
    qs = urllib.parse.urlencode(
        {
            "index": "illnesses",
            "version": "v1",
            "page": page,
            "count": count,
            "text": text,
            "column": "",
            "order": "",
        }
    )
    req = urllib.request.Request(
        f"{BASE}?{qs}",
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://data.egov.kz/datasets/view?index=illnesses",
            "Cookie": cookie,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    cookie = load_cookies()
    by_id: dict[str, dict] = {}
    stats: dict[str, dict] = {}

    for prefix in PREFIXES:
        page = 1
        total_pages = 1
        fetched = 0
        kept = 0
        while page <= total_pages:
            data = fetch_page(cookie, prefix, page)
            total_pages = int(data.get("totalPages") or 1)
            elements = data.get("elements") or []
            fetched += len(elements)
            for row in elements:
                if is_liver(row.get("icd10")):
                    by_id[str(row.get("id"))] = row
                    kept += 1
            print(f"{prefix}: page {page}/{total_pages} fetched={fetched} kept_so_far={len(by_id)}", flush=True)
            page += 1
            time.sleep(0.05)
            if page > 800:
                break
        stats[prefix] = {"fetched": fetched, "kept": kept, "totalPages": total_pages}

    rows = list(by_id.values())
    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSV without pandas dependency for robustness
    cols = ["id", "icd10", "icd_name", "cat", "code", "subcode", "patients_c", "region", "sdu_load_i"]
    lines = [",".join(cols)]
    for r in rows:
        vals = []
        for c in cols:
            v = "" if r.get(c) is None else str(r.get(c))
            if any(ch in v for ch in [",", '"', "\n"]):
                v = '"' + v.replace('"', '""') + '"'
            vals.append(v)
        lines.append(",".join(vals))
    OUT_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    # quick aggregates
    by_code: dict[str, int] = {}
    by_region: dict[str, int] = {}
    patients_total = 0
    for r in rows:
        code = str(r.get("icd10") or "")
        stem = code.split(".")[0]
        by_code[stem] = by_code.get(stem, 0) + 1
        region = str(r.get("region") or "")
        by_region[region] = by_region.get(region, 0) + 1
        try:
            patients_total += int(float(str(r.get("patients_c") or "0").replace(" ", "")))
        except ValueError:
            pass

    summary = {
        "source": "https://data.egov.kz/datasets/view?index=illnesses",
        "filter": "ICD-10 B15-B19, K70-K77, C22",
        "rows": len(rows),
        "patients_c_sum": patients_total,
        "by_icd_stem": dict(sorted(by_code.items())),
        "regions": len(by_region),
        "stats_by_prefix_search": stats,
        "outputs": {"csv": str(OUT_CSV), "json": str(OUT_JSON)},
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "patients_c_sum": patients_total, "by_icd_stem": summary["by_icd_stem"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
