#!/usr/bin/env bash
# Builds Apptainer images for each DIA-NN version found in the script's directory.
# Versions are detected from DIA-NN-{{version}}-*Linux.zip files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEF_FILE="${SCRIPT_DIR}/diann.def"

if [[ ! -f "$DEF_FILE" ]]; then
    echo "Error: Definition file not found: ${DEF_FILE}" >&2
    exit 1
fi

# Collect unique versions from zip filenames
declare -A versions
for zip in "${SCRIPT_DIR}"/DIA-NN-*-Linux*.zip; do
    [[ -f "$zip" ]] || continue
    basename="$(basename "$zip")"
    # Extract the leading numeric version from the filename
    version="${basename#DIA-NN-}"
    version="$(echo "$version" | grep -oP '^\d+(\.\d+)*')"
    versions["$version"]=1
done

if [[ ${#versions[@]} -eq 0 ]]; then
    echo "Error: No DIA-NN zip files found in ${SCRIPT_DIR}" >&2
    exit 1
fi

echo "Found versions: ${!versions[*]}"

for version in "${!versions[@]}"; do
    output="${SCRIPT_DIR}/diann_v${version}.sif"
    zip="$(ls "${SCRIPT_DIR}"/DIA-NN-${version}-*Linux*.zip 2>/dev/null | head -1)"
    echo "Zip: $zip"
    if [[ -f "$output" ]]; then
        echo "Skipping ${version}: ${output} already exists"
        continue
    fi
    
    if [[ -z "$zip" ]]; then
        echo "Error: No zip file found for version ${version}" >&2
        continue
    fi
    echo "Building image for DIA-NN ${version} using $(basename "$zip")..."
    if apptainer build \
        --build-arg "DIANN_VERSION=${version}" \
        --build-arg "DIANN_ZIP=$(basename "$zip")" \
        "$output" \
        "$DEF_FILE" > /dev/null; then
        echo "Built: ${output}"
    else
        echo "Error: Build failed for DIA-NN ${version}" >&2
    fi
done

echo "Done."
