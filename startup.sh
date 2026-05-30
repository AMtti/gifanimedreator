#!/usr/bin/env bash
set -e

PORT_VALUE=${PORT:-8000}

exec streamlit run main.py \
  --server.address 0.0.0.0 \
  --server.port $PORT_VALUE \
  --server.headless true
