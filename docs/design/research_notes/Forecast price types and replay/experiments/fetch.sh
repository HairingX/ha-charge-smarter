#!/usr/bin/env bash
# Download the public data the experiments read into an empty folder: fetch.sh <folder> [end date]
# elpriser.org forecast archive (every run, DK1 and DK2) and Energi Data Service DayAheadPrices.
set -euo pipefail
out=$1; end=${2:-$(date -u -d tomorrow +%F)}
mkdir -p "$out"
for a in DK1 DK2; do
  curl -sS -o "$out/list_$a.json" "https://elpriser.org/api/forecast/archive?area=$a"
  for d in $(python3 -I -c "import json,sys;print(' '.join(json.load(open(sys.argv[1]))['issued']))" "$out/list_$a.json"); do
    curl -sS -o "$out/arch_${a}_$d.json" "https://elpriser.org/api/forecast/archive?area=$a&issued=$d"
  done
done
curl -sS -o "$out/dap.json" "https://api.energidataservice.dk/dataset/DayAheadPrices?start=2026-09-01&end=$end&filter=%7B%22PriceArea%22:%5B%22DK1%22,%22DK2%22%5D%7D&limit=0"
