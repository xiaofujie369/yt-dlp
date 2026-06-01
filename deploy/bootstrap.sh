#!/usr/bin/env sh
set -eu

cp -n .env.example .env
mkdir -p data/downloads data/postgres logs
docker compose pull
docker compose up -d --build
docker compose logs -f backend worker frontend
