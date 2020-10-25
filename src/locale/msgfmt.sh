#!/bin/sh
cd "$(dirname "$0")"
msgfmt -o ./ru/LC_MESSAGES/main.mo ./ru/LC_MESSAGES/main.po
