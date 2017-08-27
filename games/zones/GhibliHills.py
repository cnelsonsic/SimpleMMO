# This file is imported when the zone wants to load an instance of this zone.

from games.zones.basezone import randloc, randrot, randscale
from games.zones.basezone import BaseZone

from elixir_models import Object

class Zone(BaseZone):
    def __init__(self, logger=None, *args, **kwargs):
        '''Initialize the zone.
        Insert whatever objects into the database programmatically.
        This includes loading things from a disk file if you so choose.

        It will not run more than once on the zone's database.
        If you want new content on an existing database, either make
        a script to apply changes, or just delete the database for
        that zone and recreate it when the zone is started up again.
        '''
        super(Zone, self).__init__()

        self.logger.info("Starting GhibliHills zone script...")


    def insert_objects(self):
        '''Insert any objects you want to be present in the zone into the
        database in this call.

        This gets called exactly once per database. If you change something here
        and want it to appear in the zone's database, you will need to clear the
        database first.

        Deleting the "Loading Complete" object will only cause duplicates.
        Do not do this.
        '''

        self.logger.info("Placing chickens...")

        # Place 10 chickens randomly:
        for i in xrange(10):
            obj = Object()
            obj.name = "Chicken #%d" % i
            obj.resource = 'chicken'
            obj.loc_x, obj.loc_y, obj.loc_z = randloc(), randloc(), randloc()
            obj.rot_x, obj.rot_y, obj.rot_z = randrot(), randrot(), randrot()
            obj.scale_x, obj.scale_y, obj.scale_z = randscale(), randscale(), randscale()
            obj.vel_x, obj.vel_y, obj.vel_z = 0, 0, 0
            obj.states.extend(['alive', 'whole', 'clickable'])
            obj.scripts = ['games.objects.chicken']
            obj.save()

        self.logger.info(str([o.name for o in Object.get_objects()]))

