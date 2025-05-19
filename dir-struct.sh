#!/usr/bin/env bash
#
# Usage: 
#   chmod +x print_structure.sh
#   ./print_structure.sh [DEPTH]
#
# Prints a tree of your project up to DEPTH (default 3)

DEPTH="${1:-3}"

echo "Project structure (max depth = $DEPTH):"
if command -v tree &> /dev/null; then
  # if you have `tree` installed
  tree -L "$DEPTH"
else
  # fallback to find + indent
  find . -maxdepth "$DEPTH" | sed -e 's/[^-][^\/]*\//   |__/g' -e 's/\.\///g'
fi
