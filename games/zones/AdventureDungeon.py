
from games.zones.basezone import BaseZone
from games.objects.chatbot import ChatBot


class Zone(BaseZone):

    def insert_objects(self):
        # Insert the totally helpful chatbot NPC
        ChatBot.create()


