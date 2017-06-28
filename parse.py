import sys
import getopt
import requests
import json
import webbrowser
import pathlib

# API Config
SCRIPT = "https://thesilphroad.com/atlas/getLocalNests.json"
NEST_VERIFIED = '1'
NEST_UNVERIFIED = '2'
NEST_CLUSTER = '1'
NEST_SPAWN_AREA = '2'
NEST_SPAWN_POINT = '3'
MARKER_NAME = 'localMarkers'
POKEMON_ID = 'pokemon_id'
URL_SKELETON = "https://thesilphroad.com/atlas#%s/%s/%s"

# Algorithm Config
POKEMON_FILE = 'pokemons.json'
POKEMON_INDEX = 'pokemon'
UNVERIFIED_INDEX = 'unverified'
OPEN_SITE_INDEX = 'open'
POKEMON_COLLECTION_INDEX = 'collection'

# Zoom limitations
ZOOM_INDEX = 'zoom'
ZOOM_DEFAULT = 15
ZOOM_MIN = 10
ZOOM_MAX = 18
ZOOM_LAT_INIT = 65.536
ZOOM_LONG_INIT = 163.84

# Location Definition
LOCATION_INDEX = 'location'
LOCATION_FILE_INDEX = 'source'
LOCATION_DEFAULT_NAME = ['Current Location']
LAT_NAME = 'lat'
LONG_NAME = 'long'


def load_as_json(filename):
    if not pathlib.Path(filename).exists():
        print("File %s does not exist" % filename)
        sys.exit(2)
    with open(filename) as data_file:
        data = json.load(data_file)
    return data

# Build the list of pokemons
poke_data = load_as_json(POKEMON_FILE)


def print_help(script):
    print(script + " -l <%s[Optional]> -s <%s[Optiona]> -p <%s[Optional]> \
                           -z <%s[Optional=%d]> -u <%s[Optional=False] -s <%s[Optional=False] -c <%s[Optional]>"
          % (LOCATION_INDEX, LOCATION_FILE_INDEX, POKEMON_INDEX,
             ZOOM_INDEX, ZOOM_DEFAULT, UNVERIFIED_INDEX, OPEN_SITE_INDEX, POKEMON_COLLECTION_INDEX))
    print("-l --%s The Location where you want to search pokemons for, in the lat,long format" % LOCATION_INDEX)
    print("-s --%s The file containing all the locations to iterate through in the Format "
          "of a JSON array. Each index being the name of the location, and the value being an array of lat and long" % LOCATION_FILE_INDEX)
    print("-p --%s The pokemon(s) to find. It can be one or multiple comma separated IDs or Pokemon Names." % POKEMON_INDEX)
    print("-z --%s The level of zoom. For now, only levels between 10 and 18 are supported" % ZOOM_INDEX)
    print("-u --%s Include unverified nests?" % UNVERIFIED_INDEX)
    print("-o --%s Open the URL in the desired location if any of the pokemons are found in that location. "
          "Disabled automatically if reading locations from file" % OPEN_SITE_INDEX)
    print("-c --%s Collection of pokemons being seek.")


def parse(argv):
    script = argv.pop(0)
    sopts = 'l:s:p:z:u:o:c:'
    lopts = []
    for key in (LOCATION_INDEX, POKEMON_INDEX, ZOOM_INDEX, UNVERIFIED_INDEX, OPEN_SITE_INDEX, LOCATION_FILE_INDEX, POKEMON_COLLECTION_INDEX):
        lopts.append("%s=" % key)

    data = {ZOOM_INDEX: ZOOM_DEFAULT, UNVERIFIED_INDEX: False,
            LOCATION_INDEX: False, POKEMON_INDEX: False, OPEN_SITE_INDEX: False, LOCATION_FILE_INDEX: False, POKEMON_COLLECTION_INDEX: False}

    try:
        opts, args = getopt.getopt(argv, sopts, lopts)
    except getopt.GetoptError:
        print_help(script)
        sys.exit(2)

    if len(opts) == 0:
        print_help(script)
        sys.exit(2)

    for opt, arg in opts:
        for longopt in lopts:
            key = longopt[:-1]
            if opt in ("-%s" % longopt[0:1], "--%s" % longopt[:-1]):
                data[key] = arg

    if LOCATION_INDEX in data and data[LOCATION_INDEX]:
        if "," not in data[LOCATION_INDEX] or str(data[LOCATION_INDEX]).count(",") != 1:
            print("Location is not sent in the way of LAT,LONG")
            sys.exit(2)
        loc_parts = str(data[LOCATION_INDEX]).split(",")
        data[LOCATION_INDEX] = {LOCATION_DEFAULT_NAME: ''}
        location_data = [float(loc_parts[0].strip()), float(loc_parts[1].strip())]
        data[LOCATION_INDEX][LOCATION_DEFAULT_NAME] = location_data

    if LOCATION_FILE_INDEX in data:
        data[LOCATION_INDEX] = {}
        location_set = load_as_json(data[LOCATION_FILE_INDEX])
        for name, loc in location_set.items():
            if not name or not loc:
                print("Location from file has to be in the form of [{'Location Alias': [Lat, Long]")
                sys.exit(2)
            data[LOCATION_INDEX][name] = [float(loc[0]), float(loc[1])]

    if (LOCATION_INDEX not in data) and (LOCATION_FILE_INDEX not in data):
        print("location is needed, and needs to be comma separated or "
              "needs to be a JSON file in the way of {'Location Alias': [Lat, Long]}")
        sys.exit(2)

    if data[POKEMON_COLLECTION_INDEX]:
        pokemons = load_as_json(data[POKEMON_COLLECTION_INDEX])
        data[POKEMON_INDEX] = ",".join(pokemons)

    if data[POKEMON_INDEX]:
        data[POKEMON_INDEX] = translate_pokemon(str(data[POKEMON_INDEX]).split(','))

    if POKEMON_INDEX not in data:
        print("pokemon is required and needs to be numeric")
        sys.exit(2)

    if ZOOM_INDEX in data:
        data[ZOOM_INDEX] = int(data[ZOOM_INDEX])
        if data[ZOOM_INDEX] < ZOOM_MIN or data[ZOOM_INDEX] > ZOOM_MAX:
            print("zoom needs to be between 10 and 18")

    parse_nests(data)


def translate_pokemon(pokemons):
    """
    Translate a list of Pokemons to their IDS.
    Allow IDs and Strings to be mixed and mached just in case
    :param pokemons:
    :return:
    """
    translated_pokemons = []
    for pokemon in pokemons:
        if pokemon.isdigit():
            translated_pokemons.append(pokemon)
        else:
            pokemon = pokemon.strip()
            if pokemon not in poke_data:
                print("Pokemon %s not found in list of pokemons" % pokemon)
                sys.exit(2)
            translated_pokemons.append(poke_data[pokemon])

    return translated_pokemons


def parse_nests(data):
    """
    Builds the API request with the right elements.
    Roughly calculates the Southern bounds of the location and the center
    Sends the request with the calculated data
    :param data:
    :return:
    """

    # If we have multiple locations
    # Force the open site option to false.
    if len(data[LOCATION_INDEX]) > 1:
        data[OPEN_SITE_INDEX] = False

    for name, location in data[LOCATION_INDEX].items():
        find_pokemon(data, location, name)


def calculate_zoom(axis, zoom):
    if axis == LAT_NAME:
        zoom_offset = ZOOM_LAT_INIT / (2 ** (zoom - 1))
    else:
        zoom_offset = ZOOM_LONG_INIT / (2 ** (zoom - 1))

    return zoom_offset


def find_pokemon(data, location, name):
    lat_zoom = calculate_zoom(LAT_NAME, data[ZOOM_INDEX])
    long_zoom = calculate_zoom(LONG_NAME, data[ZOOM_INDEX])
    slocation = [location[0] - lat_zoom, location[1] - long_zoom]
    nlocation = [location[0] + lat_zoom, location[1] + long_zoom]

    nest_levels = [NEST_VERIFIED]
    if UNVERIFIED_INDEX in data and data[UNVERIFIED_INDEX]:
        nest_levels.append(NEST_UNVERIFIED)

    nest_types = [NEST_CLUSTER, NEST_SPAWN_AREA, NEST_SPAWN_POINT]

    sdata = {
        'lat1': str(nlocation[0]),
        'lng1': str(nlocation[1]),
        'lat2': str(slocation[0]),
        'lng2': str(slocation[1]),
        'zoom': str(data[ZOOM_INDEX]),
        'center_lat': str(location[0]),
        'center_lng': str(location[1]),
        'mapFilterValues[nestVerificationLevels][]': nest_levels,
        'mapFilterValues[nestTypes][]': nest_types,
        'mapFilterValues[specieses][]': data[POKEMON_INDEX],
    }

    try:
        response = requests.post(SCRIPT, sdata)
    except requests.HTTPError:
        print("HTTP Error contacting %s with data %s" % (SCRIPT, sdata))
        sys.exit(2)

    response_dict = response.json()

    if (MARKER_NAME not in response_dict) or (len(response_dict[MARKER_NAME]) == 0):
        print("Couldn't find any pokemons in %s" % name)
        return

    pokemons_found = set()

    for key, pokemon_data in response_dict[MARKER_NAME].items():
        if POKEMON_ID in pokemon_data:
            pokemon = translate_id_to_name(pokemon_data[POKEMON_ID])
            pokemons_found.add(pokemon)
        else:
            print("Error %s returned from API but not in the pokemons data source" % POKEMON_ID)

    page_url = URL_SKELETON % (data[ZOOM_INDEX], location[0], location[1])

    if pokemons_found:
        print("Yay! The following pokemons were found near %s: %s. Go to %s and find out where they are!" %
              (name, ", ".join(pokemons_found), page_url))
        if data[OPEN_SITE_INDEX]:
            webbrowser.open(page_url)


def translate_id_to_name(pokemon_id):
    for pokemon, key in poke_data.items():
        if int(key) == int(pokemon_id):
            return pokemon

    print("Error: couldn't translate %s" % pokemon_id)

if __name__ == '__main__':
    parse(argv=sys.argv)
