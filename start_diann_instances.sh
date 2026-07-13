#!/bin/sh
# Starts the Apptainer instances for all available versions. Assumes that the relevant directories are in /data/; modify the mounting paths as appropriate.

SCRIPT_DIR=$(dirname "$0")
echo "Script dir: ${SCRIPT_DIR}"
apptainer_path=${SCRIPT_DIR}/static/apptainer/

for i in `ls ${apptainer_path}/*.sif`; do
	echo "Starting ${i}..."
	im_name=`basename ${i}`;
	im_name="${im_name%.*}";
	apptainer instance start -B /data/articles/:/data/articles/:ro -B /data/datasets/:/data/datasets/:ro -B /data/supporting/:/data/supporting/:ro -B /data/quantified/:/data/quantified/ ${i} ${im_name}
done

