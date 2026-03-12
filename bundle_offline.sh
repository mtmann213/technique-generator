#!/bin/bash

IMAGE_NAME="techniquemaker"
BUNDLE_FILE="techniquemaker_offline_bundle.tar"

echo "--- Starting Offline Bundle Generation ---"
echo "Step 1: Building Docker Image (Requires Internet)..."
docker build -t $IMAGE_NAME .

echo "Step 2: Exporting Image to Tarball..."
docker save $IMAGE_NAME > $BUNDLE_FILE

echo "--- Bundle Complete! ---"
echo "File created: $BUNDLE_FILE"
echo ""
echo "TO DEPLOY ON NO-INTERNET DEVICE:"
echo "1. Copy $BUNDLE_FILE to the target machine via USB."
echo "2. Run: docker load < $BUNDLE_FILE"
echo "3. Run: ./run_docker.sh predator"
