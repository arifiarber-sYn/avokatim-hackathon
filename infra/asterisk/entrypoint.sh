#!/bin/sh
# Renders the pjsip template with the sipgate credentials from the
# environment (docker-compose <- backend/.env) and starts Asterisk in the
# foreground. Refuses to start without credentials so a misconfigured
# container cannot register half-empty against sipgate.
set -eu

if [ -z "${SIPGATE_SIP_USER:-}" ] || [ -z "${SIPGATE_SIP_PASSWORD:-}" ]; then
  echo "SIPGATE_SIP_USER / SIPGATE_SIP_PASSWORD not set — telephony disabled." >&2
  exit 1
fi

TEMPLATES=/etc/asterisk-templates
CONF=/etc/asterisk

sed -e "s|__SIPGATE_SIP_USER__|${SIPGATE_SIP_USER}|g" \
    -e "s|__SIPGATE_SIP_PASSWORD__|${SIPGATE_SIP_PASSWORD}|g" \
    -e "s|__SIPGATE_SIP_HOST__|${SIPGATE_SIP_HOST:-sipgate.de}|g" \
    "$TEMPLATES/pjsip.conf.template" > "$CONF/pjsip.conf"

cp "$TEMPLATES/extensions.conf" "$CONF/extensions.conf"
cp "$TEMPLATES/modules.conf" "$CONF/modules.conf"

exec asterisk -f -U asterisk
