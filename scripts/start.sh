#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Start the application
if [ "$APP_ENV" = "production" ]; then
    echo "Starting in production mode..."
    gunicorn app.main:app \
        --workers ${APP_WORKERS:-4} \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind ${APP_HOST:-0.0.0.0}:${APP_PORT:-8000} \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log
else
    echo "Starting in development mode..."
    uvicorn app.main:app \
        --host ${APP_HOST:-0.0.0.0} \
        --port ${APP_PORT:-8000} \
        --reload
fi
