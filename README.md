# drive-sort

Regelbasiertes, reversibles Google-Drive-Aufraeum-Tool. Dry-Run als Default, Manifest-basierte Applys, vollstaendig reversibel via Ledger.

## Design

- **Dry-Run als Default** — `python drive_sort.py` zeigt nur, was passieren wuerde
- **Manifest-basiert** — `--apply <manifest>` fuehrt die im Manifest (`manifests/manifest_<ts>.tsv`) protokollierten Moves aus
- **Komplett reversibel** — `--undo ledger/ledger_<ts>.jsonl` macht jeden Move eines Applys rueckgaengig
- **Protected Buckets** — konfigurierbare Ordner, die nie angefasst werden
- **Quarantaene statt Loeschen** — keine Datei wird je geloescht

## Setup

```bash
cd drive-sort
./bootstrap.sh                                # pyyaml + sort-rules.yaml aus Vorlage
python3 drive_sort.py                         # dry-run, schreibt manifests/manifest_<ts>.tsv
python3 drive_sort.py --apply manifests/manifest_<ts>.tsv   # ausfuehren
```

Voraussetzung: `rclone` muss konfiguriert sein (`rclone config`).

## sort-rules.yaml

```yaml
remote: "gdrive:"           # rclone remote name
protected: [Backup, secrets]  # nie anfassen
buckets: ["00_Inbox", "01_Work", "02_Personal"]
quarantine: "99_Review"     # Muell → 99_Review/<datum>/, nie loeschen
file_rules:                 # erste passende Regel gewinnt; Felder: name, target, ext | name_re | empty_gdoc | any
  - {name: rest, any: true, target: "00_Inbox"}
# optional: folder_moves, dedupe_dirs
```

## License

MIT — see `LICENSE`.
