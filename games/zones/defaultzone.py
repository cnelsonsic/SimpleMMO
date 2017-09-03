# This file is imported when the zone wants to load an instance of this zone.

class Zone(BaseZone):

    def insert_objects(self):
        '''Insert any objects you want to be present in the zone into the
        database in this call.

        This gets called exactly once per database. If you change something here
        and want it to appear in the zone's database, you will need to clear the
        database first.

        Deleting the "Loading Complete" object will only cause duplicates.
        Do not do this.
        '''

        # Place 100 barrels randomly:
        self.randobj(name="Barrel #%d", resource='barrel', states=['closed', 'whole', 'clickable'], count=100)

        # Place 10 chickens randomly:
        self.randobj(name="Chicken #%d", resource='chicken', scripts=['games.objects.chicken'], count=10)

        print [o.name for o in Object.objects()]

