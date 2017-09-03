SimpleMMO
=========

[![Build Status](https://secure.travis-ci.org/cnelsonsic/SimpleMMO.png?branch=master)](http://travis-ci.org/cnelsonsic/SimpleMMO)

Quick Installation
------------------

1. Install [Docker](https://www.docker.com/).
1. `make cli`

Once this finishes running, you should be dropped to a prompt.

Type 'help' for help.


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

Database
---------

### SQL
The bulk of database work is done in an SQL database, you can use MySQL, Postgres,
or even SQLite.
Basically anything that Peewee (and by extension, SQLAlchemy) supports.

API Documentation
-----------------
[The API (for both HTTP and Python modules) is available here.](http://cnelsonsic.github.com/SimpleMMO/html/index.html)
