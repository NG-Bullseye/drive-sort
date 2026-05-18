# drive-sort — System-Brief

**Produkt:** Cortex (by System_One). Peripherie-/Tool-Repo.
**Selbstbild + Regeln:** `~/cortex/CLAUDE.md` (kanonisch).

## Zweck
Regelbasiertes, reversibles Aufräumen von Leos Google Drive (`gdrive:` via
rclone). Baut/erhält die Top-Level-Taxonomie, sortiert Müll in Quarantäne.

## Sicherheit (nicht verhandelbar)
- Dry-Run = Default. Echte Moves nur `--apply <manifest>` nach Leo-Gegenlesung.
- Nie hart löschen — Müll → `99_Review/<datum>/`.
- `protected:` (System/DR/Secrets, bisync-Set) wird NIE angefasst.
- Jeder Move → Ledger → `--undo` macht ihn rückgängig.

## Dateien
- `sort-rules.yaml` — Taxonomie, protected-Liste, Datei-/Ordner-/Dedupe-Regeln.
- `drive_sort.py` — Engine (dry-run / --apply / --undo).
- `manifests/`, `ledger/` — Laufzeit, gitignored.

## Kopplung
`folder_moves: Bürokratie → 10_Buerokratie` zieht den News-Poll-Pfad mit:
bei Apply MUSS `NEWS_BUERO_REMOTE` in `~/cortex/main.py` nachgezogen werden.

## Status
2026-05-18: Struktur (8 Buckets) live. Manifest A–E **angewendet, 76/76 ok**,
Ledger `ledger/ledger_2026-05-18_*.jsonl` (reversibel via --undo). Bürokratie
+ Personalien → `10_Buerokratie/`; News-Poll-Pfad in ~/cortex/main.py
nachgezogen, deployed, verifiziert (ctx buero=True). Root entmüllt.
Bisync-Dienst (WD-60) unabhängig (Müll war nicht im bisync-Set).
