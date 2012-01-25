#!/usr/bin/env python
# ##### BEGIN AGPL LICENSE BLOCK #####
# This file is part of SimpleMMO.
#
# Copyright (C) 2011, 2012  Charles Nelson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END AGPL LICENSE BLOCK #####

'''A server for running queries against.'''

import uuid
import random
import time

# Initialize mongodb
from pymongo.connection import Connection
connection = Connection("localhost")

db = connection.foo

# Clear out database.
db.foo.remove({})
db.foo.drop()

# Insert 10k rows into mongodb.
starttime = time.time()
DOCS = 10000
for i in xrange(10000):
    doc = {'obj': uuid.uuid4(), 'timestamp': i}
    db.foo.save(doc)
endtime = time.time()
print "Inserted %d docs in %05f seconds" % (DOCS, endtime-starttime)

db.foo.ensure_index('timestamp')

# Get rows between x and x+5 (Number of seconds probably between updates on client)
LENGTH = 5
TESTS = (10*10*10)
starttime = time.time()
for _ in xrange(TESTS):
    beginningstamp = random.randint(0, TESTS-LENGTH)
    endingstamp = beginningstamp+LENGTH
    x = [y['timestamp'] for y in db.foo.find({"timestamp": {"$gte": beginningstamp, "$lt": endingstamp}})]
    try:
        assert(len(x) == LENGTH)
    except(AssertionError):
        print "AssertionError"
        print len(x), LENGTH
        print beginningstamp, endingstamp
        print x
#         import pdb; pdb.set_trace()
endtime = time.time()

print "Queried %d times in %08f seconds, for an average of %08f seconds per test. (%d queries/sec)" % (TESTS, endtime-starttime, (endtime-starttime)/TESTS, 1/((endtime-starttime)/TESTS))

# Clear out database.
db.foo.remove({})
db.foo.drop()


