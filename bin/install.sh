#!/bin/sh

if [ -n "$1" ]; then
    LIB_NAME=$(basename "$1")
    printf "%s" "$LIB_NAME: "

    case "$LIB_NAME" in
        *wx*) echo "Protected lib, skipping"; return 0 ;;
        *python*) echo "Protected lib, skipping"; return 0 ;;
        *) ;;
    esac

    LOCATE_OUT="$(/sbin/ldconfig -p | grep "$LIB_NAME" | tr ' ' '\n' | grep / | head -n 1)"

    if [ -e "$LOCATE_OUT" ]; then
        echo "Found on the system: $LOCATE_OUT. Removing $1"
        rm -f "$1"
    else
        echo "$LIB_NAME not found, keeping the bundled one"
    fi

    return 0
fi

find . -maxdepth 1 -type f -name 'lib*' -exec "$0" '{}' \;
exit 0
