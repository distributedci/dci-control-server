# DCI Control-server

## installation

### PostgreSQL configuration

install and configure PostgreSQL:

    yum install postgresql-server postgresql-contrib

Allow local account with password:

    editor /var/lib/pgsql/data/pg_hba.conf

Add the following line on the top of the file:

    host    all             all             127.0.0.1/32            md5

Restart PostgreSQL with the new settings:

    systemctl restart postgresql.service

Connect with the postgres user:

    sudo su - postgres
        $ createuser -P boa
    Enter password for new role:
    Enter it again:

    $ createdb boa -O boa
    $ psql -U boa -W -h 127.0.0.1 dci_control_server < db_schema/dci-control-server.sql


# REST interface

The REST API is available for any type of objects:

- platform
- environment
- file
- job
- jobstate
- scenario

## Create a platforms

POST http://127.0.0.1:5000/platforms
Content-Type: application/json

[{"name": "barack"}, {"name": "mitt"}]

## List the existing platforms with a limit

GET http://127.0.0.1:5000/platforms?max_results=1

## Search a given platform

GET http://127.0.0.1:5000/platforms?where={"id":"9f97593b-d263-c1e4-f2de-b1b4e36ba87c"}

## Retrieve a platform using its UUID

GET http://127.0.0.1:5000/platforms/9f97593b-d263-c1e4-f2de-b1b4e36ba87c

## Update a platform

Here we reuse the ETAG from the command bellow in the
`If-Match` line.

PATCH http://127.0.0.1:5000/platforms/9f97593b-d263-c1e4-f2de-b1b4e36ba87c
If-Match: 7fd095f13e88793f985f760269cc608960228779
Content-Type: application/json

{"name": "Jim", "etag": "bibi"}

## Get the updated platform

GET http://127.0.0.1:5000/platforms/Jim
