#! /bin/bash -e

service openvswitch-switch start

if [ ! -S /var/run/docker.sock ]; then
    echo 'Error: the Docker socket file "/var/run/docker.sock" was not found. It should be mounted as a volume.'
    exit 1
fi

if [[ $# -eq 0 ]]; then
    cd /son-emu/src/emuvim/examples
    exec /usr/bin/python simple_heat_restapi_single_dc.py
else
    $*
fi
