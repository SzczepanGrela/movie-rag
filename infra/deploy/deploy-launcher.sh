#!/bin/bash
set -e

DEPLOY_SCRIPT_PATH=/home/movie-rag/deploy.sh
DEPLOY_SCRIPT_URL=https://raw.githubusercontent.com/SzczepanGrela/movie-rag/main/infra/deploy/deploy.sh

curl -fsSL "$DEPLOY_SCRIPT_URL" -o "$DEPLOY_SCRIPT_PATH"
chmod 755 "$DEPLOY_SCRIPT_PATH"
exec bash "$DEPLOY_SCRIPT_PATH"
