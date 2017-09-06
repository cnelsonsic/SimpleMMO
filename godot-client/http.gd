
var http = 0
var cookies = ""

func _init():
    http = HTTPClient.new()

func connect(hostname, port):
    var err = http.connect(hostname, port) # Connect to host/port
    assert(err==OK) # Make sure connection was OK

    # Wait until resolved and connected
    OS.delay_usec(1)
    while( http.get_status()==HTTPClient.STATUS_CONNECTING or http.get_status()==HTTPClient.STATUS_RESOLVING):
        http.poll()
        OS.delay_usec(1)

    assert( http.get_status() == HTTPClient.STATUS_CONNECTED ) # Could not connect

func _request(method, endpoint, headers=[], data=""):
    var err = http.request(method,endpoint,headers,data) # Request a page from the site (this one was chunked..)

    assert( err == OK ) # Make sure all is OK

    OS.delay_usec(1)
    while (http.get_status() == HTTPClient.STATUS_REQUESTING):
        # Keep polling until the request is going on
        http.poll()
        OS.delay_usec(1)

    assert( http.get_status() == HTTPClient.STATUS_BODY or http.get_status() == HTTPClient.STATUS_CONNECTED ) # Make sure request finished well.

    if (http.has_response()):
        # If there is a response..


        var headers = {}
        for header in http.get_response_headers():
            if "Set-Cookie" in header:
                cookies += header.split("Set-Cookie: ")[1]
                cookies += ";  "
            else:
                var name = header.split(":")[0]
                var value = header.split(":")[1]
                headers[name] = value

        #var headers = http.get_response_headers_as_dictionary() # Get response headers

        # Getting the HTTP Body

        if !(http.is_response_chunked()):
            var bl = http.get_response_body_length()

        # This method works for both anyway

        var rb = RawArray() # Array that will hold the data

        while(http.get_status()==HTTPClient.STATUS_BODY):
            # While there is body left to be read
            http.poll()
            var chunk = http.read_response_body_chunk() # Get a chunk
            if (chunk.size()==0):
                # Got nothing, wait for buffers to fill a bit
                OS.delay_usec(1000)
            else:
                rb = rb + chunk # Append to read buffer

        # Done!

        var text = rb.get_string_from_ascii()
        var loaded_data = {}
        #if (headers.has('Content-Type') and headers['Content-Type'].find('text/html')) or text.beginswith("{"):
        if text.begins_with("{"):
            #print("Parsing %s as json!"%text)
            loaded_data.parse_json(text)
        elif text.begins_with("["):
            # Wrap json arrays in a dictionary so it parses.
            loaded_data.parse_json('{"_":%s}' % text)
            loaded_data = loaded_data['_']
        else:
            loaded_data = {'message': text}

        return [loaded_data, headers]

func get(hostname, port, endpoint, data={}):

    connect(hostname, port)

    var headers=[
        "User-Agent: SimpleMMO-Godot-Client/0.1 (Godot)",
        "Accept: application/json, text/plain",
    ]

    # Support HTTP GET with Request Body. See StackOverflow.
    var querystring=""
    if data != {}:
        var querystring = http.query_string_from_dict(data)
        endpoint = endpoint + '?' + querystring

    # TODO: Some bug with how cookies is generated.
    headers.append("Cookie: " + cookies)

    return _request(HTTPClient.METHOD_GET, endpoint, headers)


func post(hostname, port, endpoint, data):

    connect(hostname, port)

    var querystring = http.query_string_from_dict(data)
    var headers=[
        "User-Agent: SimpleMMO-Godot-Client/0.1 (Godot)",
        "Accept: application/json, text/plain",
        "Content-Type: application/x-www-form-urlencoded", 
        "Content-Length: " + str(querystring.length()),
        "Cookie: " + cookies,
    ]

    return _request(HTTPClient.METHOD_POST, endpoint, headers, querystring)


