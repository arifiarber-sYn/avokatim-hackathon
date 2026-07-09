#!/bin/bash
# BoraLaw encrypted backup: Postgres dump + documents + config (.env).
#
# Output: ~/BoraLawBackups/boralaw-YYYYmmdd-HHMMSS.tar.gz.enc
# Key:    ~/.config/boralaw/backup.key (generated on first run — BACK IT UP
#         SEPARATELY, e.g. on a USB stick; without it backups are unreadable)
# Retention: last 30 backups are kept (matches the SLA).
#
# RESTORE (example):
#   openssl enc -d -aes-256-cbc -pbkdf2 -pass file:$HOME/.config/boralaw/backup.key \
#     -in boralaw-XXXX.tar.gz.enc | tar xz -C /tmp/restore
#   # then: psql < db.sql, copy documents/ into data/, copy env into backend/.env

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/BoraLawBackups"
KEY_FILE="$HOME/.config/boralaw/backup.key"
STAMP="$(date +%Y%m%d-%H%M%S)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

mkdir -p "$BACKUP_DIR"

# Encryption key: create once, never overwrite
if [ ! -f "$KEY_FILE" ]; then
    mkdir -p "$(dirname "$KEY_FILE")"
    openssl rand -hex 32 > "$KEY_FILE"
    chmod 600 "$KEY_FILE"
    echo "U krijua çelësi i backup-it: $KEY_FILE — RUAJE edhe diku tjetër (USB)!"
fi

# 1. Postgres dump (via the running container)
docker exec boralaw-db pg_dump -U boralaw boralaw > "$WORK_DIR/db.sql"

# 2. Documents (already encrypted at rest) + corpus data
if [ -d "$PROJECT_DIR/data/documents" ]; then
    cp -a "$PROJECT_DIR/data/documents" "$WORK_DIR/documents"
fi

# 3. Config with secrets (needed to decrypt documents after restore)
cp "$PROJECT_DIR/backend/.env" "$WORK_DIR/env"

# 4. Encrypted archive
OUT="$BACKUP_DIR/boralaw-$STAMP.tar.gz.enc"
tar czf - -C "$WORK_DIR" . | openssl enc -aes-256-cbc -pbkdf2 -salt \
    -pass "file:$KEY_FILE" -out "$OUT"

# 5. Retention: keep the newest 30 (aligned with the SLA's 30-day promise)
ls -1t "$BACKUP_DIR"/boralaw-*.tar.gz.enc 2>/dev/null | tail -n +31 | xargs -r rm -f

echo "Backup OK: $OUT ($(du -h "$OUT" | cut -f1))"
