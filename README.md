# drive-sort

Regelbasiertes, reversibles Google-Drive-Aufraeum-Tool. Dry-Run als Default, Manifest-basierte Applys, vollstaendig reversibel via Ledger.

## Design

- **Dry-Run als Default** — `python drive_sort.py` zeigt nur, was passieren wuerde
- **Manifest-basiert** — `--apply <manifest>` fuehrt die im Manifest protokollierten Moves aus
- **Komplett reversibel** — `--undo ledger/ledger_<ts>.jsonl` macht jeden Move eines Applys rueckgaengig
- **Protected Buckets** — konfigurierbare Ordner, die nie angefasst werden
- **Quarantaene statt Loeschen** — keine Datei wird je geloescht

## Setup

```bash
cd drive-sort
cp sort-rules.yaml.example sort-rules.yaml   # anpassen: remote, buckets, protected
python3 drive_sort.py                         # dry-run
python3 drive_sort.py --apply manifests/YYYY-MM-DD-manifest.json   # ausfuehren
```

Voraussetzung: `rclone` muss konfiguriert sein (`rclone config`).

## sort-rules.yaml

```yaml
remote: "gdrive:"           # rclone remote name
protected:                  # nie anfassen
  - Backup
  - secrets
buckets:                    # Ziel-Buckets (erste passende Regel gewinnt)
  - "00_Inbox"
  - "01_Work"
  - "02_Personal"
rules: []                   # Regeln: {pattern, bucket}
```

## License

MIT — see `LICENSE`.
