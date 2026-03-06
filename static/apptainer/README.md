# Apptainer images
The script in this directory, `build_images.sh` builds Apptainer images that can be used to run DIA-NN instances. It assumes that the .zip archives for DIA-NN are in the same directory. Assuming that you meet DIA-NN's licensing terms (see each version's LICENSE.txt as per [the repo](https://github.com/vdemichev/DiaNN/blob/master/LICENSE.md)), you can obtain the [releases here](https://github.com/vdemichev/DiaNN/releases). The `build_images.sh` script will use those and create images for each available version. Once created, you can use the `start_diann_instances.sh` script at the top level of the directory to start Apptainer instances that will be executable via the MCP server.


There are three files in this directory:
**diann.def**
The definition file for the images containing DIA-NN - the default version is 2.3.1 but it can be updated using the build argument "DIANN_VERSION"

**build_images.sh**
Script for building DIA-NN containers for multiple versions. Checks for DIA-NN-{{version}}-*Linux*.zip files to determine available versions.

**diann_sha256.txt**
Hashes for the DIA-NN released binaries.
