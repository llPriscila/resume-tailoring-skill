#!/usr/bin/env bash
# Convert all CV markdown files in output/ to PDF using Pandoc.
#
# Requirements (install once on Mac):
#   brew install pandoc
#   brew install --cask wkhtmltopdf
#
# Usage:
#   ./convert_to_pdf.sh              # convert all CVs
#   ./convert_to_pdf.sh Wise         # convert only files matching "Wise"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/output"
CSS="$OUTPUT_DIR/resume.css"

if ! command -v pandoc &>/dev/null; then
  echo "Error: pandoc not found. Install with: brew install pandoc"
  exit 1
fi

FILTER="${1:-}"
CONVERTED=0
SKIPPED=0

for md in "$OUTPUT_DIR"/*_Resume.md; do
  filename="$(basename "$md")"

  # Skip report files
  [[ "$filename" == *_Report* ]] && continue

  # Apply optional name filter
  if [[ -n "$FILTER" && "$filename" != *"$FILTER"* ]]; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  pdf="${md%.md}.pdf"

  echo "Converting: $filename"
  pandoc "$md" \
    --pdf-engine=wkhtmltopdf \
    --css "$CSS" \
    -V margin-top=1.4cm \
    -V margin-bottom=1.4cm \
    -V margin-left=1.8cm \
    -V margin-right=1.8cm \
    -V papersize=A4 \
    -o "$pdf"

  echo "  → $(basename "$pdf")"
  CONVERTED=$((CONVERTED + 1))
done

echo ""
echo "Done: $CONVERTED PDF(s) generated, $SKIPPED skipped."
