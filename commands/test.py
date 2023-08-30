from time import sleep

from invoke.tasks import task
from invoke import Collection


@task(help={
    "start_server": "Whether to start a development server in the background before running the tests",
    "test_case": "A dotted path to package, TestCase or TestCase method to test"
})
def run(ctx, start_server=True, test_case=None):
    """
    Runs the tests for the harvester
    """
    with ctx.cd("harvester"):
        if start_server:
            print("Starting development server ...")
            ctx.run("python manage.py runserver", echo=True, asynchronous=True)
            sleep(120)
            print("Done starting development server!")
        test_case = test_case if test_case else ""
        ctx.run(f"python manage.py test {test_case}", echo=True, pty=True)


test_collection = Collection("test", run)
