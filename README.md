# DCI Control-server

## installation

### Using OpenShift

[OpenShift](https://www.openshift.com/) is the simplest and recommanded way to
deploy the Control-Server.

First create an account on [OpenShift website](https://www.openshift.com/),
install the rhc command and run `rhc setup`.

In this example `mydomain` is your domain as returned by the `rhc domain list` command.

    $ rhc create-app dcistable python-3.3 postgresql-9.2
    (...)
    Your application 'dcistable' is now available.
      URL:        http://dcistable-mydomain.rhcloud.com/
      SSH to:     552643edfcf933d464000135@dcistable-mydomain.rhcloud.com
      Git remote: ssh://blablabla@dcistable-mydomain.rhcloud.com/~/git/dcistable.git/
      Cloned to:  /home/goneri/dcistable
    $ git push ssh://blablabla@dcistable-mydomain.rhcloud.com/~/git/dcistable.git/ master:master -f

Your website should be able on the http://dcistable-mydomain.rhcloud.com/ URL. If it's not the
case, you can call `rhc tail dcistable` to watch the application logs.


### Manual

#### PostgreSQL configuration

install and configure PostgreSQL:

    # yum install postgresql-server postgresql-contrib

Allow local account with password:

    # editor /var/lib/pgsql/data/pg_hba.conf

Add the following line on the top of the file:

    host    all             all             127.0.0.1/32            md5

Restart PostgreSQL with the new settings:

    # systemctl restart postgresql.service

Connect with the postgres user:

    sudo su - postgres
    $ createuser -P boa
    Enter password for new role:
    Enter it again:

    $ createdb boa -O boa
    $ psql -U boa -W -h 127.0.0.1 dci_control_server < db_schema/dci-control-server.sql


# REST interface

The REST API is available for any type of objects. You can browse them on http://127.0.0.1:5000

## Create a remotecis

POST http://127.0.0.1:5000/remotecis
Content-Type: application/json

[{"name": "barack"}, {"name": "mitt"}]

## List the existing remotecis with a limit

GET http://127.0.0.1:5000/remotecis?max_results=1

## Search a given remoteci

GET http://127.0.0.1:5000/remotecis?where={"id":"9f97593b-d263-c1e4-f2de-b1b4e36ba87c"}

## Retrieve a remoteci using its UUID

GET http://127.0.0.1:5000/remotecis/9f97593b-d263-c1e4-f2de-b1b4e36ba87c

## Update a remoteci

Here we reuse the ETAG from the command bellow in the
`If-Match` line.

PATCH http://127.0.0.1:5000/remotecis/9f97593b-d263-c1e4-f2de-b1b4e36ba87c
If-Match: 7fd095f13e88793f985f760269cc608960228779
Content-Type: application/json

{"name": "Jim", "etag": "bibi"}

## Get the updated remoteci

GET http://127.0.0.1:5000/remotecis/Jim

# DCI - CLI

First you can specify the DCI control-server url by using an environment
variable:

    $ export DCI_CONTROL_SERVER=http://zorglub.com

By default it is http://127.0.0.1:5000

## List the remotecis

    $ dci --list-remotecis

## Get a job

    $ dci --get-job <remoteci-uuid>

## Get a job and execute it

    $ dci --auto <remoteci-uuid>

The parameter remoteci-uuid should be the id of the remoteci which will run the job.
