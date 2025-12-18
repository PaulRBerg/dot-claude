#!/bin/bash
# Get macOS marketing name and version
name=$(awk -F 'macOS ' '/SOFTWARE LICENSE AGREEMENT FOR macOS/{gsub(/[0-9]+\.*/, "", $2); gsub(/\\.*/, "", $2); print $2; exit}' "/System/Library/CoreServices/Setup Assistant.app/Contents/Resources/en.lproj/OSXSoftwareLicense.rtf" | tr -d ' ')
version=$(sw_vers -productVersion)
echo "macOS ${name} ${version}"
