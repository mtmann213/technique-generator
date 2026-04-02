#!/usr/bin/env bash
# Bundles the Sidekiq-Native Generator for air-gapped transfer

echo "--- Packaging Sidekiq-SNG ---"
ZIP_NAME="sidekiq_sng_v1.zip"

# Ensure we are in the root
cd "$(dirname "$0")"

# Remove old bundle if exists
rm -f "$ZIP_NAME"

# Create zip
zip -r "$ZIP_NAME" sidekiq-sng/

echo "-----------------------------------"
echo "Bundle Created: $ZIP_NAME"
echo "Move this file to your air-gapped machine via USB."
echo "-----------------------------------"
