#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'harvester.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Setting the default runserver port based on environment variable
    PROJECT = os.environ.get('APPLICATION_PROJECT')
    from django.core.management.commands.runserver import Command as runserver
    if PROJECT == "publinova":
        runserver.default_port = "8889"
    elif PROJECT == "mbodata":
        runserver.default_port = "8890"
    else:
        runserver.default_port = "8888"
    # Execute the command
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
