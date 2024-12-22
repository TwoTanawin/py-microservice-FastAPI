#!/bin/bash

# Start login service
uvicorn login_service.main:app --host 0.0.0.0 --port 8001 &

# Start movie service
uvicorn movie_service.main:app --host 0.0.0.0 --port 8002 &

# Start gateway service
uvicorn gateway.main:app --host 0.0.0.0 --port 8000