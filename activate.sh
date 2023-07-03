#!/usr/bin/env bash

# Indicate to the application it's running outside of a container
export APPLICATION_CONTEXT=host

# Load environment variables similar to how docker-compose does it
export $(cat .env | xargs)

# Activate virtual environment
if command -v conda >/dev/null 2>&1 && { conda env list | grep 'harvester'; } >/dev/null 2>&1; then
    conda activate harvester
else
    source venv/bin/activate;
fi
