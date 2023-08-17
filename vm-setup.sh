#!/bin/bash

# install necessary packages
echo "Checking packages"
sudo apt install python3-pip
sudo apt install python3-venv
sudo apt install podman
sudo apt install locust
mkdir -p /srv/objects

# create and activate virtual environment
echo "Set virtual env"
FILE=cc1-env
if [ -f "$FILE" ]; then
    echo "venv already exists"
else
    python3 -m venv cc1-env
fi
source cc1-env/bin/activate

# download python packages in venv
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Checking packages in venv..."
    pip3 install flask_limiter
    pip3 install flask_restful
    pip3 install podman
    pip3 install locust
    pip3 install pandas
fi

echo "Activate venv with 'source cc1-env/bin/activate'"
