Harvester
=========

A Django project made to run long-running tasks.
It will connect to different repositories and index learning materials from these repositories
in an Open Search instance.


Running outside of containers
-----------------------------

There are two ways to get the ``harvester`` component started.
You can either start all services as explained in the [getting started guide](../README.md#getting-started).
Or you can start services manually with the commands described below.
It can be useful to run these services outside their containers for connecting debuggers
or diagnose problems with Docker.

##### Supporting services

You can start/stop supporting services like Postgres, Redis and Open Search with the following:

```bash
docker-compose -f docker-compose.yml up
docker-compose -f docker-compose.yml down
```

When these supporting services run you can run the processes described below one-by-one outside of containers.

##### The Django development server for the admin

```bash
make run-django
```

This makes the admin available at:

```
http://localhost:8888/admin/
```


##### A Celery development worker for processing background tasks

```
celery -A harvester worker -l info
```

##### [optional] A Django shell to call background tasks synchronously

```
python manage.py shell
```

##### [optional] A Flow-er service that monitors background tasks

```
flower -A harvester
```


Harvesting
----------

Harvesting is fairly straightforward. You need at least one 'active' ``Dataset``.
The test ``Dataset`` is active by default.
You can activate a ``Dataset`` through the Django admin under the ``core`` app.
Once harvested all materials belonging to a ``Dataset`` will be fully processed and stored under a ``DatasetVersion``.
If the ``Dataset`` is marked as ``is_latest`` the Open Search aliases will point to the newly created indices.

You can run the following command to harvest content and update all active ``Datasets`` at once:

```
invoke hrv.harvest localhost
```

Or when dealing with AWS remotes:

```
APPLICATION_MODE=<mode> invoke hrv.harvest <mode>
```

#### What a harvest actually does

A harvest undertakes the following steps:

* Gather metadata from different repositories
* Store metadata into a ``Document`` that belongs to a ``DatasetVersion``
* Extract content from files with Tika and add it to ``Document``
* Create previews for files using different tools and add links to ``Document``
* Upsert all ``Documents`` to Open Search and remove deleted ``Documents`` there as well


#### How to add more materials to a Dataset

In the admin you can see that a ``Dataset`` contains a number of ``Sources``.
By adding or removing a source you add or remove materials from those ``Sources``.
A source needs a ``spec`` which refers to the ``setSpec`` definition in the
[OAI-PMH protocol](http://www.openarchives.org/OAI/openarchivesprotocol.html#Set).
Make sure that value matches a ``setSpec`` that exists inside the repository you want to target.


Harvesting on AWS
-----------------

As explained before in the harvesting section you'll need to run the following to harvest for a particular environment:

```
APPLICATION_MODE=<mode> invoke hrv.harvest <mode>
or
APPLICATION_MODE=<mode> invoke hrv.harvest <mode> --reset
```

Where mode can be one of: localhost, development, acceptance or production.
Resetting while harvesting will fetch all data from all sources anew.

Seeing the results on AWS can be done by visiting the harvester admin or flower admin, using these addresses:
```
https://harvester.<environment>.surfedushare.nl/admin/
https://harvester.<environment>.surfedushare.nl/flower/
```

Where environment can be one of: dev, acc or prod.


Provisioning
------------

The service only needs to provision the database and Open Search.
To setup the database on an AWS environment run:

> If you setup the database in this way all data is irreversibly destroyed

```bash
APPLICATION_MODE=<environment> fab -H <bastion-host-domain> db.setup
```

To load the latest production data into the database and push that data to Open Search on an AWS environment run:

```bash
APPLICATION_MODE=<environment> invoke hrv.load-data <environment> -s production -a products
APPLICATION_MODE=<environment> invoke hrv.load-data <environment> -s production -a files
```

To load data for localhost you have to use a slightly different command,
because your profile will need access to the source.

```bash
AWS_PROFILE=pol-prod invoke hrv.load-data localhost -s production -a products
AWS_PROFILE=pol-prod invoke hrv.load-data localhost -s production -a files
```

The harvester keeps its harvest results in the database. It may be required to clean these results to start fresh.
You can force deletion of previous results with:

```bash
APPLICATION_MODE=<environment> invoke hrv.clean-data <environment>
```
