#!/usr/bin/env bash


# Exit immediately on error
set -e


# Installs local search-client repo during development when available
if [ "$DET_DJANGO_DEBUG" == "1" ]  && [ -e "/usr/src/search_client/setup.py" ] && \
    [ $(pip show search_client | grep "Location:" | awk -F "/" '{print $NF}') == "site-packages" ]
then
    echo "Replacing search_client installation with editable version"
    pip uninstall -y search_client
    pip install -e /usr/src/search_client
fi


# Check for AWS credentials on localhost
# If the credentials are not available stop loading secrets to prevent errors
if [ "$APPLICATION_MODE" == "localhost" ] && [ ! -e "/home/app/.aws/credentials" ]; then
    echo "Not loading AWS secrets on localhost, because ~/.aws/credentials is missing. Errors may occur at runtime."
    export DET_AWS_LOAD_SECRETS=0
    unset AWS_PROFILE
fi


# We're serving static files through Whitenoise. See: http://whitenoise.evans.io/en/stable/index.html#
# If you doubt this decision then read the "infrequently asked question" section for details.
# Here we gather static files that get served through uWSGI if they don't exist.
# We don't do this in Dockerfile to allow M-chips to build AMD platform containers without Rosetta chocking.
if [ -z "$(ls -A /usr/src/static/)" ]; then
    python manage.py collectstatic --noinput
fi


# Executing the normal commands
exec "$@"
