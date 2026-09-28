# ARCHITECTURE — drive-sort

## Deep Modules — Dry-Run → Manifest → Apply → Ledger → Undo

Flow: `drive_sort.py` liest `sort-rules.yaml`, listet das Drive per `rclone lsjson`, klassifiziert, schreibt ein Manifest; erst `--apply` bewegt, jeder Move geht ins Ledger. Die Sequenz lebt in `drive_sort.py::main`. Jede Innenleben-Zelle ist datei:zeile und muss per grep -n treffen.

## Flow

**Sequenz**

| # | Modul | Eingang | Ausgang | Bedingung | Stellschraube | Innenleben |
|---|---|---|---|---|---|---|
| 1 | Regeln | `sort-rules.yaml` | `RULES`, `PROTECTED` | Datei existiert | `remote`, `protected`, `buckets` | drive_sort.py:28 `RULES` |
| 2 | Listing | rclone remote | Datei-Einträge (JSON) | — | `depth` | drive_sort.py:39 `def lsjson` |
| 3 | Klassifikation | Name, Größe | (bucket, regel) | erste Regel gewinnt | `file_rules` | drive_sort.py:49 `def classify` |
| 4 | Manifest | Moves | `manifests/manifest_<ts>.tsv` | Default (Dry-Run) | — | drive_sort.py:102 `def write_manifest` |
| 5 | Apply | Manifest | Moves + `ledger/ledger_<ts>.jsonl` | `--apply` | `protected` | drive_sort.py:130 `def do_apply` |
| 6 | Undo | Ledger | Rück-Moves | `--undo` | — | drive_sort.py:158 `def do_undo` |

**Parallel**

| Modul | Eingang | Ausgang | Bedingung | Stellschraube | Innenleben |
|---|---|---|---|---|---|
| Dedupe | `dedupe_dirs` | Doubletten → Quarantäne | Key gesetzt | `quarantine` | drive_sort.py:88 `dedupe_dirs` |

## Schnittstellen

- rclone CLI als einziger Egress (drive_sort.py:34 `def rclone`).
- Manifest (TSV) und Ledger (JSONL) sind Nutzdaten, gitignored.

## Standard: Deep Modules + Flow

Standard R1–R5 steht in `~/repos/speech-engine/ARCHITECTURE.md`.
