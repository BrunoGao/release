#!/bin/bash
cd "$(dirname "$0")/.."
./gitea-data-protection.sh backup auto-$(date +%Y%m%d-%H%M%S)
