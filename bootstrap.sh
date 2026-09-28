#!/usr/bin/env bash
# bootstrap.sh — idempotentes Aufsetzen von drive-sort. Startet nichts, fuehrt keinen Move aus.
set -euo pipefail
cd "$(dirname "$0")"
command -v rclone >/dev/null || { echo "rclone fehlt → installieren und 'rclone config' ausfuehren" >&2; exit 1; }
python3 -c "import yaml" 2>/dev/null || python3 -m pip install --user pyyaml
[ -f sort-rules.yaml ] || { cp sort-rules.yaml.example sort-rules.yaml; echo "sort-rules.yaml aus Vorlage angelegt — anpassen"; }
mkdir -p manifests ledger
echo "ok — Dry-Run: python3 drive_sort.py"
