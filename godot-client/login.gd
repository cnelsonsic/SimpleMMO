extends SceneTree

var http = 0

func _init():
    http = load("res://http.gd").new()

    var hostname = "localhost"
    var authserver_port = 1234
    var charserver_port = 1235
    var masterzoneserver_port = 1236

    print("Pinging %s:%d" % [hostname, authserver_port])
    var time_start = OS.get_ticks_msec()
    var result = ''
    for x in range(100):
        result = http.get(hostname, authserver_port, '/ping')
    var time_end = OS.get_ticks_msec()
    print("Ping is: %0.02fms" % ((time_end-time_start)/100.0))

    # Register
    result = http.post(hostname, authserver_port, '/register', {'username':'testing', 'password':'testing'})
    print(result[0])

    # Login
    result = http.post(hostname, authserver_port, '/login', {'username':'testing', 'password':'testing'})
    print(result[0])
    
    # New Character
    var character_name = "testing"
    result = http.post(hostname, charserver_port, '/new', {'character_name':character_name})
    print(result[0])

    # Get character's zone
    print("fetching zone")
    result = http.get(hostname, charserver_port, '/%s/zone' % character_name)
    print(result[0])
    var zone = result[0]['zone']

    # Get zone's uri
    result = http.get(hostname, masterzoneserver_port, '/%s' % zone)
    var zoneurl = result[0]['message']
    print(zoneurl)
    var hostname_port = zoneurl.split("//")[1]
    var zone_hostname = hostname_port.split(":")[0]
    var zone_port = int(hostname_port.split(":")[1])

    # Get zone's Objects
    result = http.get(zone_hostname, zone_port, '/objects')
    var last_check = OS.get_datetime()
    print(result[0])

    # Set online
    result = http.post(zone_hostname, zone_port, '/setstatus', {'character':character_name, 'status': 'online'})
    print(result[0])

    # Move
    result = http.post(zone_hostname, zone_port, '/movement', {'character':character_name, 'x': 0, 'y':0, 'z':0})
    print(result[0])

    # Get zone's Objects
    var since = '%d-%02d-%02d %02d:%02d:%02d:000000' % [last_check["year"], last_check["month"], last_check["day"], last_check["hour"], last_check["minute"], last_check["second"]]
    print(since)
    result = http.get(zone_hostname, zone_port, '/objects', {'since': since})
    print(result)
    print(result[0])

    print("Tat's all")
    quit()

