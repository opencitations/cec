#!/bin/sh
set -e

CONFIG=/opt/grobid/grobid-home/config/grobid.yaml

if [ -n "$CROSSREF_MAILTO" ]; then
    sed -i "s|^\([[:space:]]*\)mailto:[[:space:]].*|\1mailto: \"${CROSSREF_MAILTO}\"|" "$CONFIG"
fi

if [ -n "$GROBID_CONCURRENCY" ]; then
    sed -i "s|^\([[:space:]]*\)concurrency:[[:space:]].*|\1concurrency: ${GROBID_CONCURRENCY}|" "$CONFIG"
fi

exec ./grobid-service/bin/grobid-service "$@"
