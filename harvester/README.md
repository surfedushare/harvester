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
docker compose -f docker-compose.yml up
docker compose -f docker-compose.yml down
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

Harvesting is organized per source. Sharekit, Edurep and HvA are all sources of metadata that can be harvested.
Sources like Sharekit and Edurep are repositories that contain many different providers
(Hogeschool Utrecht, Hogeschool Rotterdam etc. etc.). While other sources only contain one provider
(Hogeschool van Amsterdam). Some sources share some harvesting logic, because they work with the same platform.
However during harvesting all sources are separately harvested,
mostly because the URL's of the backend systems differ.

It's possible to see an overview of a project's sources in the admin by going to:
```
https://harvester.<environment>.<surfedushare|publinova>.nl/admin/sources/harvestsource/
```

Within sources different entities may or may not be supported. Examples of entities to harvest are: products and files.
Learning materials and research products are both considered "product" entities, because they share a lot of logic.

To see an overview of which sources support which entities you can navigate to:
```
https://harvester.<environment>.<surfedushare|publinova>.nl/admin/sources/harvestentity/
```

Metadata is harvested into ``Datasets``. These ``Datasets`` get stored in the relevant Django app.
Each entity has its own Django app, but models in these apps will inherit from the ``core`` app,
which holds most of the (shared) logic between entities.

Besides ``Dataset`` we also have the following models for each entity:
- ``Document`` stores the metadata for the entity
- ``Set`` stores a collection of ``Documents``. Sources determine which ``Documents`` are combined into logical sets.
Most sources only have one set, but especially sources supporting the (old) OAI-PMH protocol, will have logical sets.
- ``DatasetVersion`` each time we harvest we create copies of ``Documents`` to be able to rollback to previous metadata.
``Documents`` as well as ``Sets`` that come from the same harvesting process will share a ``DatasetVersion`` instance.

You can view models for entities from the different (Django) admin sections at:
```
https://harvester.<environment>.<surfedushare|publinova>.nl/admin/<entity>/
```
Note that these admin sections may also contain various ``Resource`` models.
``Resource`` models contain extra metadata like the full text of a file or PDF previews.

Starting a new harvest is relatively straightforward and can be done with a single command:

```
invoke hrv.harvest localhost
```

Or when dealing with AWS remotes:

```
APPLICATION_MODE=<mode> invoke hrv.harvest <mode>
```

#### What a harvest actually does

A harvest undertakes the following steps:

* Gather metadata from different repositories using ``Resource`` models stored in the ``sources`` Django app.
* Store metadata into the ``Document.properties`` attribute.
Each ``Document`` also belongs to a ``Set`` and ``DatasetVersion``. These models are entity specific
and are stored in the relevant entity Django apps.
* Run a number of background tasks. These tasks will set values in ``Document.derivatives``,
because the tasks derive the metadata from other metadata. These tasks may or may not use ``Resource`` models
to get the relevant metadata. Examples of tasks are: normalizing the "publisher_year" values
and extract the text from a file.
* Upsert all ``ProductDocuments`` to Open Search and omit any non-active ``ProductDocuments``.
Metadata from ``FileDocuments`` get merged into the Open Search representation of the products.
Any ``derivatives`` metadata from these ``Document`` models is combined with the ``properties`` data,
where ``derivatives`` may override ``properties``.


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

Seeing the results on AWS can be done by visiting the harvester admin or flow-er admin, using the addresses below.
Flow-er is a dashboard that keeps track of background tasks triggered by the harvesting process.
```
https://harvester.<environment>.<surfedushare|publinova>.nl/admin/
https://harvester.<environment>.<surfedushare|publinova>.nl/flower/
```

Where environment can be one of: dev, acc or prod.


Provisioning
------------

The harvester only needs to provision the database and Open Search.
To setup the database on an AWS environment run:

> If you setup the database in this way all data is irreversibly destroyed

```bash
APPLICATION_MODE=<environment> fab -H <bastion-host-domain> db.setup
```

To load the latest production data into the database and push that data to Open Search on an AWS environment run:

```bash
APPLICATION_MODE=<environment> invoke hrv.load-data <environment> -s production -a <entity>
```

Where entity is one of: products or files.
Make sure to load files before products to be able to load file data into products

To load data for localhost you have to use a slightly different command,
because your profile will need access to the source.

```bash
AWS_PROFILE=pol-prod invoke hrv.load-data localhost -s production -a <entity>
```

The harvester keeps its harvest results in the database. It may be required to clean these results to start fresh.
You can force deletion of previous results with:

```bash
APPLICATION_MODE=<environment> invoke hrv.clean-data <environment>
```
