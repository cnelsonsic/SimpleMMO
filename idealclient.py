'''This is an example implementation of an ideal client.
It won't work and probably won't even execute.'''

# Ping main server to make sure it's up, and really an authserver

# Send username/password credentials to server
# Server sends back a cookie that we send with all our requests.

# Ask charserver for list of characters associated with this account
# charserver returns a list of characters and their locations.
# We could also query any details about the character like inventory 
#   or money or current stats at this point

# We pick a character we want to play and query the charserver for its current zone
# charserver returns the zoneserver url

# We send a request to the zoneserver to mark our character as online/active
# Send an initial movement message to the zoneserver's movement handler to open the connection

# Request all objects in the zone. (Terrain, props, players are all objects)
# Bulk of loading screen goes here while we download object info.

### Repetitive ###
# Every second or so, request objects that have changed or been added since the last request.
# Send movement keys to the movement handler of the zoneserver as fast as possible to move the character about


