#!/usr/bin/env bash
set -euo pipefail

# Validates that all referenced files in SKILL.md exist
# Run from the skill directory: ./scripts/validate-references.sh

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_FILE="${SKILL_DIR}/SKILL.md"
ERRORS=0

echo "Validating references in ${SKILL_FILE}..."

# Extract referenced paths from SKILL.md (matches references/*.md and examples/*.md patterns)
while IFS= read -r ref; do
  ref_path="${SKILL_DIR}/${ref}"
  if [[ ! -f "${ref_path}" ]]; then
    echo "ERROR: Referenced file not found: ${ref}"
    ((ERRORS++))
  else
    echo "OK: ${ref}"
  fi
done < <(grep -oE '(references|examples)/[a-zA-Z0-9_-]+\.md' "${SKILL_FILE}" | sort -u)

if [[ ${ERRORS} -gt 0 ]]; then
  echo ""
  echo "FAILED: ${ERRORS} broken reference(s) found"
  exit 1
else
  echo ""
  echo "PASSED: All references valid"
  exit 0
fi
