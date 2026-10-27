#!/bin/sh

if [ -z "${HOST_IP:-}" ]; then
    HOST_IP="$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')"
    HOST_IP="${HOST_IP:-10.160.4.43}"
fi

INGRESS_HTTP_PORT="${INGRESS_HTTP_PORT:-80}"
INGRESS_HTTPS_PORT="${INGRESS_HTTPS_PORT:-443}"

INGRESS_CLASS="${INGRESS_CLASS:-nginx}"

HTTP_BASE_URL="http://${HOST_IP}:${INGRESS_HTTP_PORT}"
HTTPS_BASE_URL="https://${HOST_IP}:${INGRESS_HTTPS_PORT}"

export HOST_IP
export INGRESS_HTTP_PORT
export INGRESS_HTTPS_PORT
export INGRESS_CLASS
export HTTP_BASE_URL
export HTTPS_BASE_URL
