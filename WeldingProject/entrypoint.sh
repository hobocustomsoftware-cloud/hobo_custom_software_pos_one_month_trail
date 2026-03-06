#!/bin/sh
# Ensure media dirs exist and are writable by appuser (fix Permission denied: /app/media/shop for logo upload)
set -e
mkdir -p /app/media/shop
chown -R appuser:appuser /app/media 2>/dev/null || true
exec gosu appuser "$@"
