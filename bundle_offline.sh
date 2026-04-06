#!/usr/bin/env bash
# bundle_offline.sh - Create a complete air-gap transfer bundle for TechniqueMaker
#
# Produces: techniquemaker_offline_v1.tar.gz
#   Contains: Full source tree + pre-built Sidekiq-SNG (x86_64)
#   Excludes: .git, build artifacts, Docker image (already separate), .env
#
# Transfer via USB to air-gapped x86_64 Ubuntu 22.04 target machine.
#
# On the target:
#   tar xzf techniquemaker_offline_v1.tar.gz
#   cd technique-generator
#   ./install.sh                    # Build GNU Radio OOT module
#   cd sidekiq-sng && ./build_on_target.sh  # Build Sidekiq streaming engine

echo "============================================"
echo "  TechniqueMaker Air-Gap Bundle v2.0"
echo "  x86_64 / Ubuntu 22.04"
echo "============================================"

BUNDLE_NAME="techniquemaker_offline_v1.tar.gz"
cd "$(dirname "$0")"

# Clean up old bundles
rm -f "$BUNDLE_NAME"
rm -f sidekiq_sng_v1.zip

# --- Optional: also create the Sidekiq-only zip (backwards compat) ---
echo "[1/4] Bundling Sidekiq-SNG standalone zip (backwards compat)..."
if command -v zip &> /dev/null; then
    chmod +x sidekiq-sng/build_on_target.sh
    zip -q -r sidekiq_sng_v1.zip sidekiq-sng/
    echo "  -> sidekiq_sng_v1.zip created"
else
    echo "  -> 'zip' not found, skipping Sidekiq zip (not required for main bundle)"
fi

# --- Create the main source tarball ---
echo "[2/4] Creating full source bundle..."
echo "  Excluding: .git, build artifacts, Docker image, .env, logs, caches"

# Files to include (explicit whitelist for safety)
INCLUDE_PATHS=(
    "apps/"
    "config/"
    "docs/"
    "gr-techniquemaker/"
    "local_drivers/"
    "predator-cpp/CMakeLists.txt"
    "predator-cpp/src/"
    "sidekiq-sng/"
    "tests/"
    "TechniqueMaker.py"
    "CHANGELOG.md"
    "Dockerfile"
    ".dockerignore"
    ".gitignore"
    "install.sh"
    "lcc"
    "LLM_HANDOVER_DOCUMENT.md"
    "PROJECT_ARCHITECT_PROMPT.md"
    "pyproject.toml"
    "README.md"
    "run_docker.sh"
    "run_standalone.sh"
    "bundle_offline.sh"
    "check_hardware.sh"
)

# Create the tarball, excluding large/binary artifacts
EXCLUDES=(
    --exclude='.git'
    --exclude='__pycache__'
    --exclude='*.pyc'
    --exclude='*.tar.gz'
    --exclude='*.zip'
    --exclude='sidekiq_sng_v1/'
    --exclude='everything-claude-code/'
    --exclude='predator-cpp/build/'
    --exclude='sidekiq_ai_bundle/'
    --exclude='.env'
    --exclude='techniquemaker.log'
    --exclude='venv/'
    --exclude='.claude/'
    --exclude='*.grc'
)

tar czf "$BUNDLE_NAME" "${EXCLUDES[@]}" "${INCLUDE_PATHS[@]}" 2>/dev/null

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$BUNDLE_NAME" | cut -f1)
    echo "  -> $BUNDLE_NAME ($SIZE)"
else
    echo "  WARNING: tar failed, trying full-tree approach..."
    tar czf "$BUNDLE_NAME" "${EXCLUDES[@]}" --transform="s|^|technique-generator/|" . 2>/dev/null
    SIZE=$(du -h "$BUNDLE_NAME" | cut -f1)
    echo "  -> $BUNDLE_NAME ($SIZE)"
fi

echo "[3/4] Verifying archive contents..."
echo "  Archive size: $(du -h "$BUNDLE_NAME" | cut -f1)"
echo "  File count: $(tar tzf "$BUNDLE_NAME" | wc -l)"

echo "[4/4] Bundle complete."
echo ""
echo "============================================"
echo "  Transfer Instructions"
echo "============================================"
echo ""
echo "  1. Copy these files to the air-gapped target via USB:"
echo "       - $BUNDLE_NAME"
echo "       - predator_image.tar.gz  (Docker image for x86_64)"
echo ""
echo "  2. On the target machine:"
echo "       a. Extract:     tar xzf $BUNDLE_NAME"
echo "       b. Enter:       cd technique-generator/"
echo "       c. Check HW:    ./check_hardware.sh"
echo "       d. Install:     ./install.sh"
echo "       e. Build SNG:   cd sidekiq-sng && ./build_on_target.sh && cd .."
echo "       f. Load Docker: gunzip -c predator_image.tar.gz | docker load"
echo "       g. Launch:      python3 TechniqueMaker.py predator"
echo ""
echo "============================================"
