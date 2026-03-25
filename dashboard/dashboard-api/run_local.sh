#!/usr/bin/env bash

set -a
source ../.env.example
set +a

uvicorn app.main:app --host 0.0.0.0 --port 8100