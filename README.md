# SilphRoadHelper
A helper for SilphRoad to check if any given pokemon are around a given area

This is an unofficial helper for the SilphRoad (thesilphroad.com). 
It takes a location (or a file with different locations) and a list of comma separated pokemons, and it tells you if those pokemons are in the area or not.

Please, visit their site every day and give them traffic. Do not stop using their site because of this helper. They did a great job putting up such a useful service

## Arguments
The script takes a few arguments:

### -l --location [Optional]
  The Location where you want to search pokemons for, in the lat,long format
### -s --source [Optional]
  The file containing all the locations to iterate through in the Format of a JSON array. Each index being the name of the location, and the value being an array of lat and lon
g
### --p --pokemon [Required]
  The pokemon(s) to find. It can be one or multiple comma separated IDs or Pokemon Names.
### -z --zoom [Optional]
  The level of zoom. For now, only levels between 10 and 18 are supported. Default 15
### -u --unverified [Optional]
  Include unverified nests? False by default
### -o --open [Optional]
  Open the URL in the desired location if any of the pokemons are found in that location. 
  Disabled automatically if reading locations from file

## Location
This is a simple Latitude, Longitude comma separated "touple". For example, Grapevine, TX is "32.9124,-97.0593". <br/>
If you seek to check multiple locations at the same time, you can do so by sending the -s argument instead of -l. <br />
The -s --source argument should point to a JSON file containing a dictionary with the name of the location and the lat, long touple: 

```json
  {
  "Work": [12.1234,98.7654],
  "Home": [56.7890, -12.345],
  "Gym" : [9.8765, 56.7890]
  }
```

When using the file, the script will iterate through the locations in the file and check for all the pokemons in each area and report them: 

```
python parse.py --s locations_set.json --p "horsea, totodile, charmander"

Couldn't find any horsea,totodile in Work
Couldn't find any horsea,totodile in Home
Yay! The following pokemons were found near Gym: horsea, totodile. Go to https://thesilphroad.com/atlas#_ZOOM_/_LAT_/_LONG_ and find out where they are!
```

## Pokemon
Pokemons can be passed as a single string, or a comma separated list of pokemons: 

```
python parse.py --pokemon "charmander"
```
-OR-
```
python parse.py --pokemon "charmander, bulbasaur, pikachu"
```
If the parser finds any of the 3 pokemons in the area given by either **-l** or **-s**, it will output a message showing that it was found.

## Zoom

The zoom alters the area in which silphroad will find the pokemons for you. The limit for now is 10 and 18

## Unverified nests

This enables or disables the unverified nests. Off by default. 

## Open Site 

This will enable / disable the automatic site being opened centered in the given locations if a pokemon is found.

## Known Issues
### -p option not working properly
The -p argument does not work. It has to be passed as --p or --pokemon. Will work on implementing a better argument system to enable this functionality
