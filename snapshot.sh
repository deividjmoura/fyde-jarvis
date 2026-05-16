#!/bin/bash

OUTPUT="fyde_jarvis_backend_snapshot.txt"

echo "=========================================" > "$OUTPUT"
echo "FYDE-JARVIS BACKEND SNAPSHOT" >> "$OUTPUT"
echo "=========================================" >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "### PROJECT TREE ###" >> "$OUTPUT"
echo "" >> "$OUTPUT"

find . \
  -path './.git' -prune -o \
  -path './venv' -prune -o \
  -path './node_modules' -prune -o \
  -path './__pycache__' -prune -o \
  -type f | sort >> "$OUTPUT"

echo "" >> "$OUTPUT"

echo "=========================================" >> "$OUTPUT"
echo "### FILE CONTENTS ###" >> "$OUTPUT"
echo "=========================================" >> "$OUTPUT"

FILES=$(find . \
  -path './.git' -prune -o \
  -path './venv' -prune -o \
  -path './node_modules' -prune -o \
  -path './__pycache__' -prune -o \
  -type f \( \
    -name "*.py" -o \
    -name "*.env" -o \
    -name "*.txt" -o \
    -name "*.md" -o \
    -name "requirements.txt" -o \
    -name "pyproject.toml" -o \
    -name "*.yml" -o \
    -name "*.yaml" \
  \))

for file in $FILES
do
  echo "" >> "$OUTPUT"
  echo "=========================================" >> "$OUTPUT"
  echo "FILE: $file" >> "$OUTPUT"
  echo "=========================================" >> "$OUTPUT"

  sed -n '1,260p' "$file" >> "$OUTPUT" 2>/dev/null
done

echo ""
echo "========================================="
echo "Snapshot gerado com sucesso:"
echo "$OUTPUT"
echo "========================================="
