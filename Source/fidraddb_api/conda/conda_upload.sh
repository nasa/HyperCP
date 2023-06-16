# Only need to change these two variables
export PKG_NAME=ocdb-client
export USER=ocdb

mkdir ~/conda-bld
conda config --set anaconda_upload no

CONDA_PACKAGE=$(conda build -c conda-forge recipe --output)

echo anaconda -t "${CONDA_UPLOAD_TOKEN}" upload  -u ${USER} "${CONDA_PACKAGE}" --force

anaconda -t "${CONDA_UPLOAD_TOKEN}" upload  -u ${USER} "${CONDA_PACKAGE}" --force
