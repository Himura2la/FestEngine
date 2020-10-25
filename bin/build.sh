#!/bin/sh
cd "$(dirname "$0")"
docker-compose up --build
docker cp fest-engine:/app/bin/fest_engine.tar.gz ./fest_engine-linux-x64-minimal.tar.gz
docker-compose down
