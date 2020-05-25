""" 
YOUTUBE CHANNELS TO KODI
"""
import os.path
import configparser
import sys
import json
import datetime
import re
import requests
import urllib
from pathlib import Path
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

 
addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
addonID       = addon.getAddonInfo('id')
addon_path = xbmc.translatePath("special://profile/addon_data/"+addonID)
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urllib.parse.parse_qs(sys.argv[2][1:])

         


HOME = xbmc.translatePath("special://profile/library/")
print(HOME)
YOUTUBE_DIR = HOME
CHANNELS = YOUTUBE_DIR+'series'
MOVIES = YOUTUBE_DIR+'movies'
MUSIC_VIDEOS = YOUTUBE_DIR+'music_videos'
VIDEOS = []
VIDEO_DURATION = {}
PDIALOG = xbmcgui.DialogProgress()

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

CONFIG = configparser.ConfigParser()
if os.path.isfile(addon_path+'//config.ini'):
    CONFIG.read(addon_path+'//config.ini')
else:
    CONFIG['api'] = {
        "API_key" : "sad"
    }
    CONFIG['channels'] = {}
    CONFIG['movies'] = {}
    CONFIG['music_videos'] = {}


#home=translatePath('home')











def __save():
    with open(addon_path+'//config.ini', 'w') as configfile:
        CONFIG.write(configfile)
        configfile.close()

def print(what):
    xbmcgui.Dialog().ok(addonname, what)


def ask(name, *args):

    if args:
        header = args[0]
    else:
        header = ""

    kb = xbmc.Keyboard('default', header, True)
    kb.setDefault(name)
    kb.setHiddenInput(False)
    kb.doModal()
    return(kb.getText())
  


def __check_key_validity(key):
    req = requests.get("https://www.googleapis.com/youtube/v3/channels?part=snippet&id=UCS5tt2z_DFvG7-39J3aE-bQ&key="+key)
    if req.status_code == 200:
        return 'valid'
    return 'invalid'


def __add_channel(channel_id):
    print('adding: '+channel_id)
    if 'channels' not in CONFIG:
        CONFIG['channels'] = {}
    data = {}
    channel_url = "https://www.googleapis.com/youtube/v3/channels?part=brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails&id="+channel_id+"&key="+addon.getSetting('API_key')
    req = requests.get(channel_url)
    reply = json.loads(req.content)
    if 'items' not in reply:
        raise SystemExit("no such channel")
    data['title'] = reply['items'][0]['brandingSettings']['channel']['title']
    if 'description' in reply['items'][0]['brandingSettings']['channel']:
        data['plot'] = reply['items'][0]['brandingSettings']['channel']['description']
    else:
        data['plot'] = data['title']
    
    data['aired'] = reply['items'][0]['snippet']['publishedAt']
    data['thumb'] = reply['items'][0]['snippet']['thumbnails']['high']['url']
    data['banner'] = reply['items'][0]['brandingSettings']['image']['bannerImageUrl']
    data['fanart'] = reply['items'][0]['brandingSettings']['image']['bannerTvHighImageUrl']
    uploads = reply['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    data['uploader_stripped'] = re.sub(r'[^\w\s]', '', data['title']).replace(" ", "_")
    Path(CHANNELS+'\\'+re.sub(r'[^\w\s]', '', data['title'])).mkdir(parents=True, exist_ok=True)
    if data['uploader_stripped']+'_playlist_id' not in CONFIG['channels']:
        CONFIG['channels'][data['uploader_stripped']+'_playlist_id'] = uploads
    output = """
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n
    <tvshow>
            <title>{title}</title>
            <showtitle>{title}</showtitle>
            <plot>{plot}</plot>
            <genre>None</genre>
            <premiered>{aired}</premiered>
            <aired>{aired}</aired>
            <studio>{title}</studio>
            <thumb>{thumb}</thumb>
            <thumb aspect="poster">{fanart}</thumb>
            <thumb aspect="banner">{banner}</thumb>
            <fanart>
                    <thumb>{fanart}</thumb>
            </fanart>
            <tag>Youtube</tag>
    </tvshow>
    """.format(**data)
    tvshow_file = CHANNELS+'\\'+ re.sub(r'[^\w\s]', '', data['title']) + '\\'+'tvshow.nfo'
    file = open(tvshow_file, 'w', encoding="utf-8")
    file.write(output)
    file.close()
    __save()
    __parse_uploads(uploads)
def __parse_uploads(playlist_id, *args):
    if args:
        url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+"&pageToken="+args[0]+"&key="+addon.getSetting('API_key')
    else:
        url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+"&key="+addon.getSetting('API_key')
    req = requests.get(url)
    reply = json.loads(req.content)
    vid = []
    totalResults=int(reply['pageInfo']['totalResults'])
    PDIALOG.create('Fetching channel info', 'Please wait...')        
    for item in reply['items']:
        #print(x['snippet']['resourceId']['videoId'])
        VIDEOS.append(item)
        #kyrp.update(item['snippet']['title'], int(totalResults * len(VIDEOS) / 100))
        #PDIALOG.update(int(100 / 100),'das')
        PDIALOG.update(int(100 * len(VIDEOS) / totalResults), 'Downloading info: ' + str(len(VIDEOS)) + '/' + str(totalResults) )
        vid.append(item['snippet']['resourceId']['videoId'])
        #PLAYLIST.items[i].snippet.resourceId.videoId

    __get_video_details(vid)
    if reply.get('nextPageToken'):
        __parse_uploads(playlist_id, reply['nextPageToken'])
    else:
        __render()


def __get_video_details(array):
    get = ','.join(array)
    #print('***'+get)
    url = "https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id="+get+"&key="+addon.getSetting('API_key')
    req = requests.get(url)
    reply = json.loads(req.content)
    for item in reply['items']:
        #print(item['id'])
        #print(__yt_duration(item['contentDetails']['duration']))

        VIDEO_DURATION[item['id']] = __yt_duration(item['contentDetails']['duration'])
    #DETAILS.items[i].contentDetails.duration
    #print(reply)


def __yt_duration(in_time):
    duration = 0
    time = in_time.split("PT")[1]
    if 'H' in time and 'M' in time and 'S' in time:
        duration = int(time.split("H")[0])*60 + int(time.split("H")[1].split("M")[0])
    elif 'H' in time and 'M' in time:
        duration = int(time.split("H")[0])*60 + int(time.split("H")[1].split("M")[0])
    elif 'H' in time and 'S' in time:
        duration = int(time.split("H")[0])*60
    elif 'M' in time and 'S' in time:
        duration = int(time.split("M")[0])
    else:
        duration = 0
    return duration







def __start_up():
#    Path(CHANNELS).mkdir(parents=True, exist_ok=True)
#    Path(MOVIES).mkdir(parents=True, exist_ok=True)
#    Path(MUSIC_VIDEOS).mkdir(parents=True, exist_ok=True)
    API_KEY = addon.getSetting('API_key')
#    print(API_KEY)
    if API_KEY == "":
        print("""
You\'ll need to aquire YouTube API key for this addon to work.
for instructions see: https://developers.google.com/youtube/v3/getting-started
""")
        API_KEY=ask('','API key')
        if API_KEY != "":
            if __check_key_validity(API_KEY) == 'valid':
                addon.setSetting('API_key',API_KEY)
                print('Key is valid, thank you!')
            else:
                print('Key is invalid')
                raise SystemExit(" error")
        else:
            print('Nothing given')
            raise SystemExit
    










addon_handle = int(sys.argv[1])
#print(str(sys.argv))

SEARCH_QUERY={}
def __search(query):
    SEARCH_QUERY.clear()
    channel_url = "https://www.googleapis.com/youtube/v3/search?type=channel&part=id,snippet&maxResults=50&q="+query+"&key="+addon.getSetting('API_key')
    req = requests.get(channel_url)
    reply = json.loads(req.content)
    if not 'items' in reply:
        print('No such channel')
        raise SystemExit(" error")
    ###########################
    # No idea why the first(0) item not showing on results, hack till i do
    ###########################
    SEARCH_QUERY[reply['items'][0]['snippet']['title']+' '] = {}
    SEARCH_QUERY[reply['items'][0]['snippet']['title']+' ']['id'] = reply['items'][0]['snippet']['channelId']
    SEARCH_QUERY[reply['items'][0]['snippet']['title']+' ']['description'] = reply['items'][0]['snippet']['description']
    SEARCH_QUERY[reply['items'][0]['snippet']['title']+' ']['thumbnail'] = reply['items'][0]['snippet']['thumbnails']['high']['url']
    for item in reply['items']:
        xbmc.log(str(item))
        SEARCH_QUERY[item['snippet']['title']] = {}
        SEARCH_QUERY[item['snippet']['title']]['id'] = item['snippet']['channelId']
        SEARCH_QUERY[item['snippet']['title']]['description'] = item['snippet']['description']
        SEARCH_QUERY[item['snippet']['title']]['thumbnail'] = item['snippet']['thumbnails']['high']['url']
        #print(items['snippet']['title'] +' - '+ items['snippet']['channelId'] +'\n' + items['snippet']['description'] +'\n_______________________')
    __folders()





def __menu(*args):
    menuItems = ['Add Channel', 'List Channels','Refresh']
    if args:
        menuItems=(args[0])
    dialog = xbmcgui.Dialog()
    ret = dialog.select(addonname, menuItems)
    if menuItems[ret] == 'Add Channel':
        query=ask('','Search for a channel')
        if query:
            __search(query)
        else:
            __menu()
    elif menuItems[ret] == 'List Channels':
        __folders()





def __render():
    PDIALOG.create('Importing channel', 'Please wait...')
    #pDialog = xbmcgui.DialogProgressBG()
    year = 0
    episode = 0
    VIDEOS.reverse()
    l_count=0
    for item in VIDEOS:
        data = {}
        #print(item)
        data['author'] = item['snippet']['channelTitle']
        data['title'] = item['snippet']['title']
        data['plot'] = item['snippet']['description']
        #aired_exact=datetime.datetime(item['snippet']['publishedAt'])
        #2020-03-06T18:00:05Z
        aired = item['snippet']['publishedAt'].split('T')[0]
        ttime = item['snippet']['publishedAt'].split('T')[1]
        data['aired'] = aired
        data['aired_exact'] = datetime.datetime(int(aired.split('-')[0]), int(aired.split('-')[1]), int(aired.split('-')[2]), int(ttime.split(':')[0]), int(ttime.split(':')[1]), 0, 0)  # pylint: disable=line-too-long      
        season = int(aired.split('-')[0])
        if year != season:
            year = season
            season = year
            episode = 0
        data['video_id'] = item['snippet']['resourceId']['videoId']
        data['video_duration'] = VIDEO_DURATION[data['video_id']]
        if 'maxres' in item['snippet']['thumbnails']:
            data['thumb'] = item['snippet']['thumbnails']['maxres']['url']
        elif item['snippet']['thumbnails']['high']:
            data['thumb'] = item['snippet']['thumbnails']['high']['url']
        elif item['snippet']['thumbnails']['standard']:
            data['thumb'] = item['snippet']['thumbnails']['standard']['url']
        else:
            data['thumb'] = item['snippet']['thumbnails']['default']['url']
        episode += 1
        data['episode'] = episode
        data['season'] = season
        l_count += 1
        #pDialog.update(int(l_count * len(VIDEOS) / 100), message='S'+str(data['season'])+'E'+str(data['episode']))
        PDIALOG.update(int(100 * l_count / len(VIDEOS)), data['title'] )
        Path(CHANNELS+'\\'+re.sub(r'[^\w\s]', '', data['author'])+'\\'+str(data['season'])).mkdir(parents=True, exist_ok=True)
        output = """
<episodedetails>
    <title>{title}</title>
    <season>{season}</season>
    <episode>{episode}</episode>
    <plot>{plot}</plot>
    <aired>{aired}</aired>
    <studio>{author}</studio>
    <credits>{author}</credits>
    <director>{author}</director>
    <thumb>{thumb}</thumb>
    <runtime>{video_duration}</runtime>
    <fileinfo>
        <streamdetails>
        <durationinseconds>{video_duration}</durationinseconds>
        </streamdetails>
    </fileinfo>
</episodedetails>
""".format(**data)
        file_location = CHANNELS+'\\'+re.sub(r'[^\w\s]', '', data['author'])+'\\'+str(data['season']) + '\\s' + str(data['season']) +'e' + str(data['episode'])
        write_file = file_location+'.nfo'
        file = open(write_file, 'w', encoding="utf-8")
        file.write(output)
        file.close()
        write_file = file_location+'.strm'
        file = open(write_file, 'w', encoding="utf-8")
        file.write('plugin://plugin.video.youtube/play/?video_id='+data['video_id'])
        file.close()
        __save()
        xbmc.executebuiltin("UpdateLibrary(video)")


def __refresh():
    for key in CONFIG['channels']:
        VIDEOS.clear()
        VIDEO_DURATION.clear()

        if '_id' in key[-3:]:
            __parse_uploads(CONFIG['channels'][key])




def __folders(*args):
    #url = print('yay')
    #print(str(sys.argv[2]))
    for items in SEARCH_QUERY:
        xbmc.log(str(items))
        li = xbmcgui.ListItem(items)
        info = {'plot': SEARCH_QUERY[items]['description']}
        li.setInfo('video', info)
        li.setArt({'thumb': SEARCH_QUERY[items]['thumbnail']})
        url = build_url({'mode': 'ListItem', 'foldername': SEARCH_QUERY[items]['id'] })
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)
    


#__menu()









class ProgressBar(object):
    def __init__(self, title, text, progress):
        self.title = title
        self.text = text
        self.progress = 1
        self.pDialog = xbmcgui.DialogProgressBG()
        #self.create(title=title, text=text)    
        #self.update(progress=0,text=None)
    def create(self):
        self.pDialog.create(self.title, self.text)
        #print(f"I am a cat. My name is {self.name}. I am {self.age} years old.")

    def update(self,text,progress):
        self.pDialog.update(progress,text)


##########l_count * len(VIDEOS) / 100
#kyrp = ProgressBar('Downloading channel info','kulli',0)
#kyrp.create()

__start_up()

mode = args.get('mode', None)

if mode is None:
    __menu()
elif mode[0] == 'ListItem':
    __add_channel(args['foldername'][0])
    #xbmc.executebuiltin("XBMC.ActivateWindow(Home)")



#
#xbmc.UpdateLibrary()
#xbmc.executebuiltin("UpdateLibrary(video)")
