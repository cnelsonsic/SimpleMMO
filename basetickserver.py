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

from __future__ import division

'''BaseTickServer
A server that should be overridden to provide a server with its own internal loop.
'''

import time

# import sched
# s = sched.scheduler(time.time, time.sleep)

from settings import CLIENT_UPDATE_FREQ, CLIENT_NETWORK_FPS

class BaseTickServer(object):
    '''This is a class that should be subclassed and tick() defined to do something
    every "tick".'''

    def __init__(self):
        self.tick_freq_multiplier = 1

    def tick(self):
        '''Do things every tick. Should be overridden.'''
        pass

    def start(self):
        self.current_tick = 0
        skip_ticks = CLIENT_UPDATE_FREQ
        max_frameskip = 5

        next_tick = 0
        self.running = True

        while self.running:
            loops = 0
            self.current_tick += 1
            while (self.current_tick > next_tick) and (loops < max_frameskip):
                # dt = ((current_tick + skip_ticks) - next_tick) / skip_ticks
                self.tick()
                next_tick += skip_ticks
                loops += 1


if __name__ == "__main__":
    bts = BaseTickServer()
    bts.start()
