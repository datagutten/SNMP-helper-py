#!/usr/bin/env bash
set -e
docker compose build --build-arg SNMP_LIBRARY=$1
docker compose run --rm tests python3 -m unittest tests.compat.test_compat