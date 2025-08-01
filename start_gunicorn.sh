#!/bin/bash

# --- Define your paths and settings ---
VENV_PATH="/home/me/Dev/py/dj/rvenv_dep"
PROJECT_ROOT="/home/me/Dev/py/dj/tup_sfrp_github_v1/src"
SOCKET_PATH="/tmp/gunicorn_tup_sfrp.sock"

# This variable defines the Python module where Gunicorn will find your WSGI application.
# For a standard Django project where 'config' is your project folder and wsgi.py is inside it:
GUNICORN_APP_MODULE="config.wsgi"

# This variable defines which settings file Django should use.
# It's usually 'yourprojectname.settings'.
DJANGO_SETTINGS_MODULE_PATH="config.settings" # Renamed for clarity


# --- Change to the project's working directory ---
# This is crucial for Django to find its modules and for Gunicorn to work correctly
cd "$PROJECT_ROOT" || { echo "Failed to change directory to $PROJECT_ROOT" >&2; exit 1; }

# --- Activate the virtual environment ---
source "$VENV_PATH/bin/activate" || { echo "Failed to activate virtual environment" >&2; exit 1; }

# --- Set environment variables ---
# Django needs to know where its settings are
export DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE_PATH" # Correct variable usage

export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"

# --- Start Gunicorn ---
# Use exec to replace the current shell process with the gunicorn process.
# This means systemd will monitor gunicorn directly, not the wrapper script's bash process.
# IMPORTANT: Use GUNICORN_APP_MODULE here, not DJANGO_SETTINGS_MODULE_PATH
exec "$VENV_PATH/bin/gunicorn" --workers 3 --bind "unix:$SOCKET_PATH" "$GUNICORN_APP_MODULE:application"
