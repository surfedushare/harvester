from invoke.tasks import task
from invoke import Collection


@task
def run(ctx):
    with ctx.cd("harvester"):
        ctx.run("python manage.py test", echo=True, pty=True)


test_collection = Collection("test", run)
