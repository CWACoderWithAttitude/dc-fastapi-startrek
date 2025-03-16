#!/bin/sh
# file: run_server.sh

uvicorn main:app --reload --host 0.0.0.0 --port 8000