# Harvester

Data harvester and search service for finding open access higher education learning materials.

The project consists of a Django Rest Framework API with an interactive documentation at /api/v1/docs/.
Harvesting background tasks are handled by a Celery.
There is also an admin available to manage some configuration options and inspect responses from sources
or locally stored data.

## Prerequisites

This project uses `Python 3.10`, `npm`, `Docker`, `docker-compose` and `psql`.
Make sure they are installed on your system before installing the project.

## Installation

The local setup is made in such a way that you can run the project inside and outside of containers.
It can be convenient to run some code for inspection outside of containers.
To stay close to the production environment it works well to run the project in containers.
External services like the database run in containers, so it's always necessary to use Docker.

#### Mac OS setup

We recommend installing Python through pyenv:

```
brew update && brew upgrade pyenv
pyenv install 3.10.4
```

When using macOS make sure you have `libmagic` installed. It can be installed using `brew install libmagic`.

#### General setup

First copy the `.env.example` file to `.env` and update the variable values to fit your system.
For a start the default values will do.

To install the basic environment and tooling you'll need to setup a local environment on a host machine with:

```bash
python3 -m venv venv --copies --upgrade-deps
source activate.sh
pip install -r requirements.txt
pip install git+https://github.com/surfedushare/search-client.git@master
```

When using vscode copy `activate.sh` to venv/bin so pylance can find it.

If you want to run the project outside of a container you'll need to add the following to your hosts file:

```
127.0.0.1 postgres
127.0.0.1 opensearch
127.0.0.1 harvester
127.0.0.1 service
127.0.0.1 redis
```

This way you can reach these containers outside of the container network through their names.
This is important for many setup commands as well as the integration tests and running the service locally.

To finish the container setup you can run these commands to build all containers:

```bash
invoke aws.sync-repository-state
invoke container.prepare-builds
docker-compose up --build
```

After that you can seed the database with data:

```bash
invoke db.setup
invoke hrv.load-data localhost -d <latest-dataset> -s production
```

The setup Postgres command will have created a superuser called supersurf. On localhost the password is "qwerty".
For AWS environments you can find the admin password under the Django secrets in the Secret Manager.


## Getting started

The local setup is made in such a way that you can run the components of the project inside and outside of containers.
External services like the database always run in containers.
Make sure that you're using a terminal that you won't be using for anything else,
as any containers will print their output to the terminal.
Similar to how the Django developer server prints to the terminal.

> When any containers run you can halt them with `CTRL+C`.
> To completely stop containers and release resources you'll need to run "stop" or "down" commands.
> As explained below.

With any setup it's always required to use the activate.sh script to **load your environment**.
This takes care of important things like local CORS and database credentials.

```bash
source activate.sh
```

After you've loaded your environment you can run all components of the project in containers with:

```bash
docker-compose up
docker-compose down
```

Alternatively you can run [processes outside of containers](harvester/README.md#running-outside-of-containers).
It can be useful to run services outside their containers for connecting debuggers or diagnose problems with Docker.

#### Available apps

Either way the database admin tool become available under:

```bash
http://localhost:8081/
```

#### Resetting your database

Sometimes you want to start fresh.
If your database container is not running it's quite easy to throw all data away and create the database from scratch.
To irreversibly destroy your local database with all data run:

```bash
docker volume rm search-portal_postgres_database
```

And then follow the steps to [install the service](service/README.md#installation) and
[install the harvester](harvester/README.md#installation) to recreate the databases and populate them.

## Tests

You can run tests for the harvester by running:

```bash
invoke test.run
```


## Deploy

Once your tests pass you can make a new build for the project you want to deploy.
This section outlines the most common options for deployment.
Use `invoke -h <command>` to learn more about any invoke command.

Before deploying you'll want to decide on a version number.
It's best to talk to the team about which version number you want to use for a deploy.
To see a list of all currently available images for a project and the versions they are tagged with you can run
the following command.

```bash
invoke aws.print-available-images
```

Make sure that the version inside of `harvester/package.py` is different from any other version in the AWS registries.
Commit a version change if this is not the case.

You can build the harvester and nginx container by running the following command:

```bash
invoke container.build
```

After you have created the image you can push it to AWS.
This command will push to a registry that's available to all environments on AWS:

```bash
invoke container.push
```

When an image is pushed to the registry you need to promote it for the environment you desire:

```bash
APPLICATION_MODE=<environment> invoke container.promote
```

To change the running containers on AWS you then need to deploy for the environment you have updated images for:

```bash
APPLICATION_MODE=<environment> invoke container.deploy
```

This last deploy command will wait until all containers in the AWS cluster have been switched to the new version.
This may take some time and the command will indicate that it is waiting to complete.
If you do not want to wait you can `CTRL+C` in the terminal safely. This cancels the waiting, not the deploy itself.


#### Release

A special case of deploying is releasing. You should take the following steps during releasing:

- There are a few things that you should check in a release PR, because it influences the release steps:
  - Are there any database migrations?
  - Are there changes to Open Search indices?
  - Is it changing the public harvester API that the search service is consuming?
  - Is it depending on infrastructure changes?
- Plan your release according to the questions above.
  Use common sense for this and take into account that we do rolling updates.
  For example if you're deleting stuff from the database, indices, API or infratructure,
  then code that stops using the stuff should be deployed before the actual deletions take place.
  If you're adding to the database, indices, API or infrastructure then they should get added
  before code runs that expect these additions.
  We write down these steps, together with their associated commands if applicable, in Pivotal tickets to remember them.
- With complicated changes we prefer to try them on development
  and we create the release plan when putting the changes on acceptance.
  When we release to production following the plan should be sufficient to make a smooth release.
- When dealing with breaking changes we make a release tag on the default branch.
  The tag is equal to the release version prefixed with a "v" so for instance: v0.0.1
  This allows us to easily jump back to a version without these breaking changes through git.
- Once the release plan is executed on production and a tag for the previous release is created when necessary then
  we merge the release PR into its branch.
- Execute the necessary deploy commands described above.
- check https://harvester.prod.surfedushare.nl/ for the right version
- check https://harvester.prod.publinova.nl/ for the right version

This completes the release. Post a message into Teams if people are waiting for certain features.

As you can see the release may consist of many steps and release plans can become elaborate.
Here is an overview of commands that are regularly used during a release and their relevant documentation:

- [Database migration](#Migrate)
- [Harvesting](harvester/README.md#Harvesting on AWS)
- Index recreation. See: `invoke -h hrv.index-dataset-version`
  (this doesn't collect documents from sources like harvesting, but does recreate indices for a Dataset)
- [Terraform](https://www.terraform.io/intro)

#### Rollback

To execute a rollback you need to "promote" a previous version and then deploy it.
First of all you need to list all versions that are available with the following command.

```bash
invoke aws.print-available-images <target-project-name>
```

You can pick a `<rollback-version>` from the command output.
Then depending on the `<environment>` you want to rollback for: `production`, `acceptance` or `development`.
You can run the following commands to rollback to the version you want.

```
APPLICATION_MODE=<environment> invoke container.promote --version=<rollback-version>
```

And after that you need to deploy the containers on AWS Fargate:

```
APPLICATION_MODE=<environment> invoke container.deploy <environment>
```

#### Migrate

To migrate the database on AWS you can run the migration command:

```bash
APPLICATION_MODE=<environment> invoke db.migrate <environment>
```

## Provisioning

There are a few commands that can help to provision things like the database on AWS.
We're using Fabric for provisioning.
You can run `fab -h <command>` to learn more about a particular Fabric command.

For more details on how to provision things on AWS see [provisioning the harvester](harvester/README.md#provisioning)

## Linting

The python code uses flake8 as a linter. You can run it with the following command:

```bash
flake8 .
```
