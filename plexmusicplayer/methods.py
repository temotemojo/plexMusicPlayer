from .utils import Track, QueueManager, MediaType
from os import environ
import requests
import xmltodict
import json

base_url = environ['PLEX_URL']
plex_token = "X-Plex-Token=" + environ['PLEX_TOKEN']

num2words1 = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', \
            6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten', \
            11: 'Eleven', 12: 'Twelve', 13: 'Thirteen', 14: 'Fourteen', \
            15: 'Fifteen', 16: 'Sixteen', 17: 'Seventeen', 18: 'Eighteen', 19: 'Nineteen'}
num2words2 = ['Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
# --------------------------------------------------------------------------------------------
# Plex Music Player - Methods

def findNumberInQuery(input):
    words = input.split()
    response = ""
    for word in  words: 
        print ('in for loop word='+word)
        value = ""
        if hasNumbers(word):
            print ('found number in loop')
            value = numberToWords(word)
            print(value)
        else:     
            value = word

        response = response + value
    print('reponse='+response)
    return response



def numberToWords(Number):
    print(":"+Number+":")
    if 1 <= Number < 19:
        print('Number='+Number)
        print(num2words1[Number])
        return num2words1[Number]
    elif 20 <= Number <= 99:
        tens, below_ten = divmod(Number, 10)
        return num2words2[tens - 2] + '-' + num2words1[below_ten]
    else:
        print("Number out of range")
        return Number

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def rebuildQueryWithoutSpaces(json_obj):
    if json_obj:
        query.replace(" ","")
        print(query)
        searchQueryUrl = base_url + "/search?query=" + query + "&" + plex_token + "&type=" + mediaType.value
        json_obj = getJsonFromPlex(searchQueryUrl)
    return json_obj

def getStreamUrl(sub_url):
    global base_url, plex_token
    return base_url + sub_url + "?download=1&" + plex_token

def getLookupUrl(sub_url):
    global base_url, plex_token
    plex_url = base_url + sub_url + "?" + plex_token
    return plex_url

def getJsonFromPlex(url):
    response = requests.get(url)
    xml_obj = xmltodict.parse(response.text)
    json_obj = json.loads(json.dumps(xml_obj))
    return json_obj

def parseTrackJson(json_obj):
    print('parseTrackJson')

    directory = json_obj['MediaContainer']['Track']
    if isinstance(directory, list):
        server = json_obj['MediaContainer']['Track'][0]['@sourceTitle']
        title = json_obj['MediaContainer']['Track'][0]['@title']
        album = json_obj['MediaContainer']['Track'][0]['@parentTitle']
        artist = json_obj['MediaContainer']['Track'][0]['@grandparentTitle']
        sub_url = json_obj['MediaContainer']['Track'][0]['Media']['Part']['@key']
    else:    
        print('not a list')
        server = json_obj['MediaContainer']['Track']['@sourceTitle']
        title = json_obj['MediaContainer']['Track']['@title']
        album = json_obj['MediaContainer']['Track']['@parentTitle']
        artist = json_obj['MediaContainer']['Track']['@grandparentTitle']
        sub_url = json_obj['MediaContainer']['Track']['Media']['Part']['@key']
    
    stream_url = getStreamUrl(sub_url)
    return Track(title, album, artist, stream_url), server

def parseAlbumJson(json_obj):
    print('parseAlbumJson')
    
    playlist = []
    directory = json_obj['MediaContainer']['Directory']
    if isinstance(directory, list):
        album = json_obj['MediaContainer']['Directory'][0]['@title']
        artist = json_obj['MediaContainer']['Directory'][0]['@parentTitle']
        server = json_obj['MediaContainer']['Directory'][0]['@sourceTitle']
        sub_url = json_obj['MediaContainer']['Directory'][0]['@key']
    else:        
        album = json_obj['MediaContainer']['Directory']['@title']
        artist = json_obj['MediaContainer']['Directory']['@parentTitle']
        server = json_obj['MediaContainer']['Directory']['@sourceTitle']
        sub_url = json_obj['MediaContainer']['Directory']['@key']
   
    album_url = getLookupUrl(sub_url)
    json_album = getJsonFromPlex(album_url)
    if '@title' in json_album['MediaContainer']['Track']:
        json_album['MediaContainer']['Track'] = [json_album['MediaContainer']['Track']]
    for track in json_album['MediaContainer']['Track']:
        title = track['@title']
        sub_url = track['Media']['Part']['@key']
        stream_url = getStreamUrl(sub_url)
        playlist.append(Track(title, album, artist, stream_url))
    return album, artist, server, playlist

def parseArtistJson(json_obj):
    print('parseArtistJson')
    playlist = []

    directory = json_obj['MediaContainer']['Directory']
    if isinstance(directory, list):
        artist = json_obj['MediaContainer']['Directory'][0]['@title']
        server = json_obj['MediaContainer']['Directory'][0]['@sourceTitle']
        sub_url = json_obj['MediaContainer']['Directory'][0]['@key']
    else:    
        artist = json_obj['MediaContainer']['Directory']['@title']
        server = json_obj['MediaContainer']['Directory']['@sourceTitle']
        sub_url = json_obj['MediaContainer']['Directory']['@key']
    
    artist_url = getLookupUrl(sub_url)
    json_artist = getJsonFromPlex(artist_url)
    if '@title' in json_artist['MediaContainer']['Directory']:
        json_artist['MediaContainer']['Directory'] = [json_artist['MediaContainer']['Directory']]
    for alb in json_artist['MediaContainer']['Directory']:
        album = alb['@title']
        sub_url = alb['@key']
        album_url = getLookupUrl(sub_url)
        json_album = getJsonFromPlex(album_url)
        if '@title' in json_album['MediaContainer']['Track']:
            json_album['MediaContainer']['Track'] = [json_album['MediaContainer']['Track']]
        for track in json_album['MediaContainer']['Track']:
            title = track['@title']
            sub_url = track['Media']['Part']['@key']
            stream_url = getStreamUrl(sub_url)
            playlist.append(Track(title, album, artist, stream_url))
    return artist, server, playlist

def processQuery(query, mediaType):
    global base_url, plex_token
    searchQueryUrl = base_url + "/search?query=" + query + "&" + plex_token + "&type=" + mediaType.value
    json_obj = getJsonFromPlex(searchQueryUrl)


    playlist = []
    try:
        if (mediaType == MediaType.Track):
            track, server = parseTrackJson(json_obj)
            speech = "Playing " + track.title + " by " + track.artist + " from " + server + "."
            playlist.append(track)
        elif (mediaType == MediaType.Album):
            album, artist, server, playlist = parseAlbumJson(json_obj)
            speech = "Playing " + album + " by " + artist + " from " + server + "."
        elif (mediaType == MediaType.Artist):
            if hasNumbers(query):
                print('has numbers')
                query = findNumberInQuery(query)
                searchQueryUrl = base_url + "/search?query=" + query + "&" + plex_token + "&type=" + mediaType.value
                json_obj = getJsonFromPlex(searchQueryUrl)
            else:
                print('does not have numbers')
            json_obj = rebuildQueryWithoutSpaces(json_obj)
            artist, server, playlist = parseArtistJson(json_obj)
            speech = "Playing " + artist + " from " + server + "."
        return speech, playlist
    except:
        speech = "I was not able to find " + query + " in your library."
        return speech, []