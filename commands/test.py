from time import sleep

from invoke.tasks import task
from invoke import Collection


@task(help={
    "start_server": "Whether to start a development server in the background before running the tests",
    "test_file": "A path to a file containing a subset of tests to run",
    "warnings": "Whether to print warnings in the test report",
    "fast": "Whether to exclude tests marked as slow"
})
def run(ctx, start_server=True, test_file=None, warnings=False, fast=False):
    """
    Runs the tests for the harvester
    """
    with ctx.cd("harvester"):
        if start_server:
            print("Starting development server ...")
            ctx.run("python manage.py runserver", echo=True, asynchronous=True)
            sleep(120)
            print("Done starting development server!")
        # Specify some flags we'll be passing on to pytest based on command line arguments
        test_file = test_file if test_file else ""
        warnings_flag = "--disable-warnings" if not warnings else ""
        if test_file:
            # Selecting happening through specifying the tests file.
            # Ignoring other mark filtering
            marks_flag = ""
        else:
            # Excluding "search" mark by default to allow parallel tests in the future
            marks_flag = '-m "not slow and not search"' if fast else '-m "not search"'
        # Run pytest command
        ctx.run(f"pytest {test_file} {warnings_flag} {marks_flag}", echo=True, pty=True)
        if not test_file:
            # Run tests marked as search, these tests cannot run in parallel without great care/effort
            ctx.run(f"pytest {warnings_flag} -m search", echo=True, pty=True)


test_collection = Collection("test", run)
