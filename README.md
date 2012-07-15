SimpleMMO
=========

[![Build Status](https://secure.travis-ci.org/cnelsonsic/SimpleMMO.png?branch=master)](http://travis-ci.org/cnelsonsic/SimpleMMO)

Quick Installation
------------------
### Virtualbox/Vagrant Server Appliance
SimpleMMO ships with a virtualbox/vagrant appliance which you can spin up
for testing or development.
It provides a linux environment, and all the dependencies pre-configured for you.

#### Installing
You need [VirtualBox](https://www.virtualbox.org/) and [Vagrant](http://vagrantup.com/).

#### Running
When in the ``vagrant`` directory of the SimpleMMO checkout, run ``vagrant up``.
In 5-10 minutes, you should have a shiny new development/testing server.
You can access it via ``vagrant ssh``, which gives you a terminal inside your vagrant box.
Discussions on using vagrant are beyond the scope of this README, so ``vagrant -h`` is your friend.

#### Client
From inside the vagrant box (via ``vagrant ssh``), you can start up the command-line client with:

    ./client.py

The following commands are supported:

    register: Register a username and password combination.
    login: Log in as a user.
    update: Update the objects from the zone server.
    map: Show a map of the zone.
    detail: Show details about a given object by name or id.


### Native Server Install
You will need pip to install the requirements, you can do something like:

    sudo apt-get install python-pip
or

    sudo yum install python-pip

You'll need to use pip to install the required python packages:

    sudo pip install -r requirements.txt

SimpleMMO uses supervisor to control its server processes, so you will need to
start them by running `supervisord` while in the SimpleMMO checkout directory.
You can use `supervisorctl` to check up on the server processes.


Servers
-------

### AuthServer
The AuthServer authenticates a client's usernames and passwords.
Its main purpose is to provide the client with a cookie that the other
servers will recognize.
It also allows a user to look up a list of their characters.

### CharServer
The CharServer manages information about Characters.
Specifically, what zone a character is currently in.
In the future, this server will probably keep track of a character's statistics,
inventory, and things of that nature.

### MasterZoneServer
The MasterZoneServer is responsible for starting up individual zones.
It also allows a client to look up what URL is associated with a specific zone id.
The magic is that when it can't find a URL for a zoneid, it starts up a ZoneServer
when a zone-id isn't found.

### ZoneServer
ZoneServers get started by the MasterZoneServer automatically.
The ZoneServers accept requests for a given set of world data.
They are the actual areas where characters roam about and do game things.
There are also zone-limited chat and private messages.
There are global messages but they aren't handled by the ZoneServer.
Each ZoneServer is entirely self-contained and is only concerned with
what is contained inside itself.

#### ScriptServer
ScriptServer is a server that runs all the scripts for a Zone.
Each zone should ideally start its own ScriptServer.
Contained inside are little Python classes with various event handlers.
See `games/objects/chicken.py` for an example script.

#### PhysicsServer
The PhysicsServer is a bit complex and probably optional in the long run.
It looks at the database for the zone and simulates all the objects in the scene
as physical, pymunk objects.
Then it updates their positions in-world.
This is generally just for 'settling' and preventing intersection of physical
objects.
Again, this is optional and probably completely vestigial.

Databases
---------
SimpleMMO uses a combination of databases to do its job most effectively.

### SQL
The bulk of database work is done in an SQL database, you can use MySQL, Postgres,
or even SQLite.
Basically anything that Elixir (and by extension, SQLAlchemy) supports.

### MongoDB
Zones are a little different.
They use MongoDB for their data storage needs.
It's fast, but less fault tolerant than the SQL databases.
Keep in mind that when starting for the first time, it may generate a "prealloc"
file that is quite large, on the order of a few gigabytes.
For most people, this will not be a problem.
However on storage-limited systems, this may prove frustrating.

The real problem here is that there is a flag for mongod, --noprealloc, which
should work for its journal files as well, but does not.
See the bug at: https://jira.mongodb.org/browse/SERVER-2733 for more information.

API Documentation
-----------------
[The API (for both HTTP and Python modules) is available here.](http://cnelsonsic.github.com/SimpleMMO/html/index.html)
