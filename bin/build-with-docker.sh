#! /bin/bash

# File from https://github.com/TheAssassin/redeclipse-appimage
# Copyright 2017 TheAssassin. Licensed under the terms of the MIT license.
# See https://github.com/TheAssassin/redeclipse-appimage/blob/master/LICENSE
# for details on the licensing.

set -e

log() {
    (echo -e "\e[91m\e[1m$*\e[0m")
}

cleanup() {
    if [ "$containerid" == "" ]; then
        return 0
    fi

     if [ "$1" == "error" ]; then
        log "error occurred, cleaning up..."
    elif [ "$1" != "" ]; then
        log "$1 received, please wait a few seconds for cleaning up..."
    else
        log "cleaning up..."
    fi

    docker ps -a | grep -q $containerid && docker rm -f $containerid
}

trap "cleanup SIGINT" SIGINT
trap "cleanup SIGTERM" SIGTERM
trap "cleanup error" 0
trap "cleanup" EXIT

log  "Building in a container..."

randstr=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 8 | head -n 1)
containerid=festengine-$randstr
imageid="festengine"

thisdir=$(dirname -- $(readlink -f -- "$0"))

log "Building Docker container"
(set -xe; docker build -t $imageid "$thisdir")

log "Creating container $containerid"

outdir=$(readlink -f -- "$thisdir/../out")
srcdir=$(readlink -f -- "$thisdir/../src")

log "Out dir: $outdir"
log "Source dir: $srcdir"

mkdir -p "$outdir"
chmod o+rwx,u+s "$outdir"
set -xe
docker run -it \
    --name $containerid \
    -v "$outdir:/out" \
    -v "$srcdir:/src" \
    $imageid
