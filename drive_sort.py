#!/usr/bin/env python3
"""drive-sort — regelbasiertes, reversibles Aufräumen von Leos Google Drive.

Sicherheits-Design (Pflicht):
  - Dry-Run ist Default. Echte Moves nur mit --apply <manifest>.
  - Nie hart löschen. Müll → quarantine-Bucket (99_Review/<datum>/).
  - protected-Ordner (System/DR/Secrets) werden NIE angefasst.
  - Jeder echte Move ins Ledger (ledger/<ts>.jsonl) → --undo macht ihn rückgängig.

  python drive_sort.py                      # Dry-Run, schreibt manifests/<ts>.tsv
  python drive_sort.py --apply manifests/X  # führt geprüftes Manifest aus
  python drive_sort.py --undo ledger/Y      # macht einen Apply rückgängig
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
RULES = yaml.safe_load((ROOT / "sort-rules.yaml").read_text(encoding="utf-8"))
REMOTE = RULES["remote"]
PROTECTED = set(RULES["protected"]) | set(RULES["buckets"])
TODAY = dt.date.today().isoformat()


def rclone(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["rclone", *args], capture_output=True, text=True,
                          check=check)


def lsjson(path: str, depth: int = 1) -> list[dict]:
    r = rclone("lsjson", f"{REMOTE}{path}", "--max-depth", str(depth),
               check=False)
    if r.returncode != 0:
        print(f"  ! lsjson {path!r} rc={r.returncode}: {r.stderr[:160]}",
              file=sys.stderr)
        return []
    return json.loads(r.stdout or "[]")


def classify(name: str, size: int) -> tuple[str, str]:
    """Loses Root-File → (ziel-bucket, regelname). Erste Regel gewinnt."""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    for rule in RULES["file_rules"]:
        if rule.get("any"):
            return rule["target"], rule["name"]
        if rule.get("empty_gdoc") and size != -1:
            continue
        if "ext" in rule and ext not in rule["ext"]:
            continue
        if "name_re" in rule and not re.search(rule["name_re"], name):
            continue
        if rule.get("empty_gdoc") or "ext" in rule or "name_re" in rule:
            return rule["target"], rule["name"]
    return "00_Inbox", "fallback"


def build_manifest() -> list[tuple[str, str, str, str]]:
    """→ Zeilen (action, src, dst, reason). action: file|dir|dedupe."""
    rows: list[tuple[str, str, str, str]] = []

    # 1) Lose Root-Dateien klassifizieren
    for e in lsjson("", 1):
        if e["IsDir"] or e["Name"] in PROTECTED:
            continue
        tgt, why = classify(e["Name"], e.get("Size", 0))
        dst = (f"{tgt}/{TODAY}/{e['Name']}" if tgt == RULES["quarantine"]
               else f"{tgt}/{e['Name']}")
        rows.append(("file", e["Name"], dst, why))

    # 2) Ganze Root-Ordner konsolidieren (folder_moves)
    existing = {e["Name"] for e in lsjson("", 1) if e["IsDir"]}
    for src, bucket in RULES.get("folder_moves", {}).items():
        if src in PROTECTED or src not in existing:
            continue
        rows.append(("dir", src, f"{bucket}/{src}", "folder_moves"))

    # 3) Dedupe: " 2.<ext>"-Doubletten in dedupe_dirs → Quarantäne
    dq = re.compile(r"^(.*) 2(\.[A-Za-z0-9]+)?$")
    for d in RULES.get("dedupe_dirs", []):
        if d in PROTECTED:
            continue
        for e in lsjson(d, 1):
            if e["IsDir"]:
                continue
            if dq.match(e["Name"].rsplit(".", 1)[0] if "." in e["Name"]
                        else e["Name"]) or dq.match(e["Name"]):
                rows.append(("dedupe", f"{d}/{e['Name']}",
                             f"{RULES['quarantine']}/{TODAY}/{d}__{e['Name']}",
                             "dup-suffix ' 2'"))
    return rows


def write_manifest(rows) -> Path:
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    p = ROOT / "manifests" / f"manifest_{ts}.tsv"
    p.parent.mkdir(exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        f.write("action\tsrc\tdst\treason\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    return p


def summarize(rows) -> None:
    from collections import Counter
    by_dst = Counter(r[2].split("/")[0] for r in rows)
    by_act = Counter(r[0] for r in rows)
    print(f"\n  {len(rows)} geplante Operationen "
          f"(file={by_act['file']} dir={by_act['dir']} "
          f"dedupe={by_act['dedupe']})")
    print("  Ziel-Buckets:")
    for k, v in sorted(by_dst.items()):
        print(f"    {v:4d}  {k}")
    print("\n  Beispiele:")
    for r in rows[:18]:
        print(f"    [{r[0]:6}] {r[1][:46]:46} → {r[2][:46]}  ({r[3]})")
    if len(rows) > 18:
        print(f"    … +{len(rows)-18} weitere (siehe Manifest-Datei)")


def do_apply(manifest: Path) -> None:
    rows = [l.rstrip("\n").split("\t")
            for l in manifest.read_text(encoding="utf-8").splitlines()[1:]]
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ledger = ROOT / "ledger" / f"ledger_{ts}.jsonl"
    ledger.parent.mkdir(exist_ok=True)
    ok = fail = 0
    with ledger.open("w", encoding="utf-8") as lg:
        for action, src, dst, reason in rows:
            top = src.split("/")[0]
            if top in set(RULES["protected"]):
                print(f"  SKIP protected: {src}")
                continue
            cmd = (["move", f"{REMOTE}{src}", f"{REMOTE}{dst}",
                    "--delete-empty-src-dirs"]
                   if action == "dir"
                   else ["moveto", f"{REMOTE}{src}", f"{REMOTE}{dst}"])
            r = rclone(*cmd, check=False)
            if r.returncode == 0:
                lg.write(json.dumps({"src": src, "dst": dst,
                                     "action": action}) + "\n")
                ok += 1
            else:
                print(f"  FAIL {src}: {r.stderr[:160]}")
                fail += 1
    print(f"\n  Apply fertig: {ok} ok, {fail} fail. Ledger: {ledger}")


def do_undo(ledger: Path) -> None:
    moves = [json.loads(l) for l in
             ledger.read_text(encoding="utf-8").splitlines() if l.strip()]
    ok = fail = 0
    for m in reversed(moves):
        cmd = (["move", f"{REMOTE}{m['dst']}", f"{REMOTE}{m['src']}"]
               if m["action"] == "dir"
               else ["moveto", f"{REMOTE}{m['dst']}", f"{REMOTE}{m['src']}"])
        r = rclone(*cmd, check=False)
        ok += r.returncode == 0
        fail += r.returncode != 0
    print(f"  Undo fertig: {ok} ok, {fail} fail.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", metavar="MANIFEST")
    ap.add_argument("--undo", metavar="LEDGER")
    a = ap.parse_args()
    if a.undo:
        do_undo(Path(a.undo))
    elif a.apply:
        do_apply(Path(a.apply))
    else:
        rows = build_manifest()
        p = write_manifest(rows)
        summarize(rows)
        print(f"\n  DRY-RUN. Kein Move ausgeführt. Manifest: {p}")
        print(f"  Freigabe → python {Path(__file__).name} --apply {p}")


if __name__ == "__main__":
    main()
