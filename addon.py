u""" 
YOUTUBE CHANNELS TO KODI
"""
from __future__ import division
from __future__ import with_statement
from __future__ import absolute_import
import sys
import json
import datetime
import re
import requests
import urllib
import time
from urlparse import urlparse
#from pathlib import Path
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
import codecs
from io import open
 

def __logger(a):
    xbmc.log(unicode(a),level=xbmc.LOGNOTICE)



addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo(u'name')
addonID       = addon.getAddonInfo(u'id')
addon_path = xbmc.translatePath(u"special://profile/addon_data/"+addonID)
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = str(sys.argv[2][1:])
         


HOME = xbmc.translatePath(u"special://profile/library/")
YOUTUBE_DIR = HOME
CHANNELS = YOUTUBE_DIR+u'series'
MOVIES = YOUTUBE_DIR+u'movies'
MUSIC_VIDEOS = YOUTUBE_DIR+u'music_videos'
VIDEOS = []
VIDEO_DURATION = {}
PDIALOG = xbmcgui.DialogProgress()
LOCAL_CONF = {u'update':False}

def __build_url(query):
    return base_url + u'?' + urllib.urlencode(query)

CONFIG={}


config_file=addon_path+'\\config.json'
if xbmcvfs.exists(config_file):
    with open(config_file, mode='rb') as f:
        CONFIG = json.load(f)
else:
    CONFIG[u'channels'] = {}
    CONFIG[u'movies'] = {}
    CONFIG[u'music_videos'] = {}



def __save():
    write_dump=unicode(json.dumps(CONFIG, sort_keys=True, indent=4, separators=(',', ': ')))
    with open(addon_path+'//config.json', mode='w', encoding='UTF-8', errors='strict', buffering=1) as file:
        file.write(write_dump)
        file.close()

def __print(what):
    xbmcgui.Dialog().ok(addonname, what)


def __ask(name, *args):

    if args:
        header = args[0]
    else:
        header = u""

    kb = xbmc.Keyboard(u'default', header, True)
    kb.setDefault(name)
    kb.setHiddenInput(False)
    kb.doModal()
    return(kb.getText())
  


def __check_key_validity(key):
    req = requests.get(u"https://www.googleapis.com/youtube/v3/channels?part=snippet&id=UCS5tt2z_DFvG7-39J3aE-bQ&key="+key)
    if req.status_code == 200:
        return u'valid'
    return u'invalid'


def __add_channel(channel_id):
    data = {}
    channel_url = u"https://www.googleapis.com/youtube/v3/channels?part=brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails&id="+channel_id+u"&key="+addon.getSetting(u'API_key')
    req = requests.get(channel_url)
    reply = json.loads(req.content)
    if u'items' not in reply:
        raise SystemExit(u"no such channel")
    data[u'channel_id'] = channel_id
    data[u'title'] = reply[u'items'][0][u'brandingSettings'][u'channel'][u'title']
    if u'description' in reply[u'items'][0][u'brandingSettings'][u'channel']:
        data[u'plot'] = reply[u'items'][0][u'brandingSettings'][u'channel'][u'description']
    else:
        data[u'plot'] = data[u'title']
    
    data[u'aired'] = reply[u'items'][0][u'snippet'][u'publishedAt']
    data[u'thumb'] = reply[u'items'][0][u'snippet'][u'thumbnails'][u'high'][u'url']
    data[u'banner'] = reply[u'items'][0][u'brandingSettings'][u'image'][u'bannerImageUrl']
    data[u'fanart'] = reply[u'items'][0][u'brandingSettings'][u'image'][u'bannerTvHighImageUrl']
    uploads = reply[u'items'][0][u'contentDetails'][u'relatedPlaylists'][u'uploads']
    data[u'uploader_stripped'] = re.sub(ur'[^\w\s]', u'', data[u'title']).replace(u" ", u"_")
    xbmcvfs.mkdirs(CHANNELS+u'\\'+re.sub(ur'[^\w\s]', u'', data[u'title']))
    if channel_id not in CONFIG[u'channels']:
        CONFIG[u'channels'][channel_id] = {}
        CONFIG[u'channels'][channel_id][u'channel_name'] = data[u'title']
        CONFIG[u'channels'][channel_id][u'channel_type'] = u'series' #temporarily until music videos and movies are implemented
        CONFIG[u'channels'][channel_id][u'playlist_id'] = uploads
    output = u"""
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
    tvshow_file = CHANNELS+'\\'+ re.sub(ur'[^\w\s]', '', data['title']) + '\\'+'tvshow.nfo'
    file = open(tvshow_file, 'w', encoding="utf-8")
    file.write(output)
    file.close()
    __save()
    if u'last_page' in CONFIG[u'channels'][channel_id]:
        __parse_uploads(uploads,CONFIG[u'channels'][channel_id][u'last_page'])
    else:
        __parse_uploads(uploads,None)

def __parse_uploads(playlist_id, page_token=None, update=False):
    if page_token:
        url = u"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+u"&pageToken="+page_token+u"&key="+addon.getSetting(u'API_key')
    else:
        url = u"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+u"&key="+addon.getSetting(u'API_key')
    req = requests.get(url)
    reply = json.loads(req.content)
    vid = []
    totalResults=int(reply[u'pageInfo'][u'totalResults'])
    if LOCAL_CONF[u'update'] == False:
        PDIALOG.create(u'Fetching channel info', u'Please wait...')        
    for item in reply[u'items']:
        VIDEOS.append(item)
        if LOCAL_CONF[u'update'] == False:
            PDIALOG.update(int(100 * len(VIDEOS) / totalResults), u'Downloading info: ' + unicode(len(VIDEOS)) + u'/' + unicode(totalResults) )
        vid.append(item[u'snippet'][u'resourceId'][u'videoId'])
    __get_video_details(vid)
    if reply.get(u'nextPageToken'):
        CONFIG[u'channels'][reply[u'items'][0][u'snippet'][u'channelId']][u'last_page'] = reply[u'nextPageToken']
        __parse_uploads(playlist_id, reply[u'nextPageToken'])
    else:
        pass
        __render()


def __get_video_details(array):
    get = u','.join(array)
    url = u"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id="+get+u"&key="+addon.getSetting(u'API_key')
    req = requests.get(url)
    reply = json.loads(req.content)
    for item in reply[u'items']:
        VIDEO_DURATION[item[u'id']] = str(__yt_duration(item[u'contentDetails'][u'duration']))


def __yt_duration(in_time):
    duration = 0
    time = in_time.split(u"PT")[1]
    if u'H' in time and u'M' in time and u'S' in time:
        duration = int(time.split(u"H")[0])*60 + int(time.split(u"H")[1].split(u"M")[0])
    elif u'H' in time and u'M' in time:
        duration = int(time.split(u"H")[0])*60 + int(time.split(u"H")[1].split(u"M")[0])
    elif u'H' in time and u'S' in time:
        duration = int(time.split(u"H")[0])*60
    elif u'M' in time and u'S' in time:
        duration = int(time.split(u"M")[0])
    else:
        duration = 0
    return str(duration)

def __check_if_youtube_addon_has_api_key():
    try:
        yt_api_key = xbmcaddon.Addon('plugin.video.youtube').getSetting('youtube.api.key')
        if yt_api_key:
            ret = xbmcgui.Dialog().yesno(addonname, u'would you like to use the same API key you have set on YouTube addon?')
            if ret:
                return yt_api_key
    except RuntimeError:
        return None


def __start_up():
    #__logger(CONFIG)
    __save()
    API_KEY = addon.getSetting(u'API_key')
    if API_KEY == u"":
        ciyapi=__check_if_youtube_addon_has_api_key()
        if ciyapi != None:
            API_KEY=ciyapi
        else:
            __print(u"""
You\'ll need to aquire YouTube API key for this addon to work.
for instructions see: https://developers.google.com/youtube/v3/getting-started
""")
            API_KEY=__ask(u'',u'API key')
        if API_KEY != u"":
            if __check_key_validity(API_KEY) == u'valid':
                addon.setSetting(u'API_key',API_KEY)
                __print(u'Key is valid, thank you!')
            else:
                __print(u'Key is invalid')
                raise SystemExit(u" error")
        else:
            __print(u'Nothing given')
            raise SystemExit
    


addon_handle = int(sys.argv[1])

SEARCH_QUERY={}
def __search(query):
    SEARCH_QUERY.clear()
    channel_url = u"https://www.googleapis.com/youtube/v3/search?type=channel&part=id,snippet&maxResults=50&q="+query+u"&key="+addon.getSetting(u'API_key')
    req = requests.get(channel_url)
    reply = json.loads(req.content)
    if not u'items' in reply:
        __print(u'No such channel')
        raise SystemExit(u" error")
    ###########################
    # No idea why the first(0) item not showing on results, hack till i do
    ###########################
    SEARCH_QUERY[reply[u'items'][0][u'snippet'][u'title']+u' '] = {}
    SEARCH_QUERY[reply[u'items'][0][u'snippet'][u'title']+u' '][u'id'] = reply[u'items'][0][u'snippet'][u'channelId']
    SEARCH_QUERY[reply[u'items'][0][u'snippet'][u'title']+u' '][u'description'] = reply[u'items'][0][u'snippet'][u'description']
    SEARCH_QUERY[reply[u'items'][0][u'snippet'][u'title']+u' '][u'thumbnail'] = reply[u'items'][0][u'snippet'][u'thumbnails'][u'high'][u'url']
    for item in reply[u'items']:
    #    __logger(unicode(item))
        SEARCH_QUERY[item[u'snippet'][u'title']] = {}
        SEARCH_QUERY[item[u'snippet'][u'title']][u'id'] = item[u'snippet'][u'channelId']
        SEARCH_QUERY[item[u'snippet'][u'title']][u'description'] = item[u'snippet'][u'description']
        SEARCH_QUERY[item[u'snippet'][u'title']][u'thumbnail'] = item[u'snippet'][u'thumbnails'][u'high'][u'url']
    __folders()





def __render():
    if len(VIDEOS) <= 0:
        raise SystemExit()
    if LOCAL_CONF['update'] == False:
        PDIALOG.create('Importing channel', 'Please wait...')
    year = 0
    episode = 0
    VIDEOS.reverse()
    l_count=0
    channelId=VIDEOS[0]['snippet']['channelId']
    if 'last_video' in CONFIG['channels'][VIDEOS[0]['snippet']['channelId']]:
        year = int(CONFIG['channels'][VIDEOS[0]['snippet']['channelId']]['last_video']['season'])
        episode = int(CONFIG['channels'][VIDEOS[0]['snippet']['channelId']]['last_video']['episode'])
        latest_aired = int(CONFIG['channels'][VIDEOS[0]['snippet']['channelId']]['last_video']['aired'])
        last_video_id = CONFIG['channels'][VIDEOS[0]['snippet']['channelId']]['last_video']['video_id']
    for item in VIDEOS:
        data = {}
        data['video_id'] = item['snippet']['resourceId']['videoId']
        aired = item['snippet']['publishedAt'].split('T')[0]
        ttime = item['snippet']['publishedAt'].split('T')[1]
        data['aired'] = aired
        aired_datetime = datetime.datetime(int(aired.split('-')[0]), int(aired.split('-')[1]), int(aired.split('-')[2]), int(ttime.split(':')[0]), int(ttime.split(':')[1]), 0, 0)  # pylint: disable=line-too-long      
        aired_timestamp = int((aired_datetime - datetime.datetime(1970,1,1)).total_seconds())
        try:
            if latest_aired > aired_timestamp or last_video_id == data['video_id']:
                continue
        except NameError:
            pass
        data['author'] = item['snippet']['channelTitle']
        data['channelId'] = item['snippet']['channelId']
        data['title'] = item['snippet']['title']
        data['plot'] = item['snippet']['description']
        season = int(aired.split('-')[0])
        if year != season:
            year = season
            season = year
            episode = 0
        data['video_duration'] = '%s' %(VIDEO_DURATION[data['video_id']])
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
        if LOCAL_CONF['update'] == False:
            PDIALOG.update(int(100 * l_count / len(VIDEOS)), data['title'] )
        xbmcvfs.mkdirs(CHANNELS+'\\'+re.sub(r'[^\w\s]', '', data['author'])+'\\'+str(data['season']))
        output = u"""
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
        CONFIG['channels'][data['channelId']]['last_video'] = {'video_id' : data['video_id'], 'aired' : aired_timestamp , 'season' : str(data['season']) , 'episode' : str(data['episode']) }
        __save()
        xbmc.executebuiltin("UpdateLibrary(video)")


def __refresh():
    __logger('refresh')
    xbmcgui.Dialog().notification(addonname, 'Updating channels', xbmcgui.NOTIFICATION_INFO, 5000)
    for items in CONFIG['channels']:
        try:
            VIDEOS.clear()
            VIDEO_DURATION.clear()
        except AttributeError:
            del VIDEOS[:]
            VIDEO_DURATION = {}
        LOCAL_CONF['update'] = True
        if 'last_page' in CONFIG['channels'][items]:
            __parse_uploads(CONFIG['channels'][items]['playlist_id'],CONFIG['channels'][items]['last_page'],update=True)
        else:
            __parse_uploads(CONFIG['channels'][items]['playlist_id'],None, update=True)
    CONFIG['last_scan'] = int(time.time())
    __save()
    xbmcgui.Dialog().notification(addonname, 'Update finished', xbmcgui.NOTIFICATION_INFO, 5000)




def __folders(*args):
    for items in SEARCH_QUERY:
        #__logger(unicode(items))
        li = xbmcgui.ListItem(items)
        info = {u'plot': SEARCH_QUERY[items][u'description']}
        li.setInfo(u'video', info)
        li.setArt({u'thumb': SEARCH_QUERY[items][u'thumbnail']})
        url = __build_url({u'mode': u'AddItem', u'foldername': SEARCH_QUERY[items][u'id'] })
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)
    

def __menu(*args):
    menuItems = ['Add Channel', 'List Channels','Refresh']
    if args:
        menuItems=(args[0])
    dialog = xbmcgui.Dialog()
    ret = dialog.select(addonname, menuItems)
    if ret == -1 or ret == None:
        xbmc.executebuiltin("Action(Back)")
        xbmc.executebuiltin("Action(Back)")
    elif menuItems[ret] == 'Add Channel':
        query=__ask('','Search for a channel')
        if query:
            LOCAL_CONF['update'] = False
            __search(query)
    elif menuItems[ret] == 'List Channels':
        __folders()
    elif menuItems[ret] == 'Refresh':
        LOCAL_CONF['update'] = False
        __refresh()


__start_up()
try:
    mode = sys.argv[2][1:].split(u'mode')[1][1:]
except IndexError:
    mode = None

try:
    foldername = sys.argv[2][1:].split(u'mode')[0].split(u'=')[1][:-1]
except IndexError:
    foldername = None

__logger(mode)
if mode is None:
    __menu()
elif mode == 'AddItem':
    __add_channel(foldername)
elif 'Refresh' in mode:
    __refresh()
#

#__logger(args)