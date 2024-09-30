#!/usr/bin/env bash

# Function to validate the project argument
validate_project() {
    local valid_projects=("edusources" "publinova" "mbodata")
    for project in "${valid_projects[@]}"; do
        if [[ "$1" == "$project" ]]; then
            return 0
        fi
    done
    return 1
}

# Get the project argument or use default
PROJECT=${1:-}

# Indicate to the application it's running outside of a container
export APPLICATION_CONTEXT=host

# Load environment variables similar to how docker compose does it
set -a
source .env
set +a

# Set APPLICATION_PROJECT based on argument if it's valid otherwise use .env value.
if [[ -n "$PROJECT" ]]; then
    if validate_project "$PROJECT"; then
        export APPLICATION_PROJECT="$PROJECT"
    else
        echo "Warning: Invalid project name. Using the value from .env file if available."
    fi
fi

# Activate virtual environment
if command -v conda >/dev/null 2>&1 && { conda env list | grep 'harvester'; } >/dev/null 2>&1; then
    conda activate harvester
else
    source venv/bin/activate
fi

# Print the current APPLICATION_PROJECT for verification
echo "Current APPLICATION_CONTEXT: $APPLICATION_CONTEXT"
echo "Current APPLICATION_PROJECT: $APPLICATION_PROJECT"
echo "Current APPLICATION_MODE: $APPLICATION_MODE"
