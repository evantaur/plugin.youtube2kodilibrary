""" 
YOUTUBE CHANNELS TO KODI
"""
import sys
import json
import datetime
import time
import re
import requests
import urllib
import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin
import shutil
 
addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
addonID       = addon.getAddonInfo('id')
addon_resources = addon.getAddonInfo("path") + '/resources/'
addon_path = xbmc.translatePath("special://profile/addon_data/"+addonID)
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urllib.parse.parse_qs(sys.argv[2][1:])
         


HOME = xbmc.translatePath("special://profile/library/")
YOUTUBE_DIR = HOME
CHANNELS = YOUTUBE_DIR+'series'
MOVIES = YOUTUBE_DIR+'movies'
MUSIC_VIDEOS = YOUTUBE_DIR+'music_videos'
VIDEOS = []
VIDEO_DURATION = {}
PDIALOG = xbmcgui.DialogProgress()
LOCAL_CONF = {'update':False}

def __build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

CONFIG={}
config_file=addon_path+'\\config.json'
if xbmcvfs.exists(config_file):
    with open(config_file, 'r') as f:
        CONFIG = json.load(f)
else:
    CONFIG = {}
    CONFIG['channels'] = {}
    CONFIG['movies'] = {}
    CONFIG['music_videos'] = {}

def __save():
    with open(addon_path+'//config.json', mode='w', encoding='UTF-8', errors='strict', buffering=1) as file:
        file.write(json.dumps(CONFIG, sort_keys=True, indent=4, separators=(',', ': ')))
        file.close()

def __print(what):
    xbmcgui.Dialog().ok(addonname, what)


def __ask(name, *args):

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


def __add_channel(channel_id,refresh=None):
    data = {}
    channel_url = "https://www.googleapis.com/youtube/v3/channels?part=brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails&id="+channel_id+"&key="+addon.getSetting('API_key')
    req = requests.get(channel_url)
    reply = json.loads(req.content)
    if 'items' not in reply:
        raise SystemExit("no such channel")
    data['channel_id'] = channel_id
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
    xbmcvfs.mkdirs(CHANNELS+'\\'+re.sub(r'[^\w\s]', '', data['title']))
    if channel_id not in CONFIG['channels']:
        CONFIG['channels'][channel_id] = {}
    CONFIG['channels'][channel_id]['channel_name'] = data['title']
    CONFIG['channels'][channel_id]['channel_type'] = 'series' #temporarily until music videos and movies are implemented
    CONFIG['channels'][channel_id]['branding'] = {}
    CONFIG['channels'][channel_id]['branding']['thumbnail'] = data['thumb']
    CONFIG['channels'][channel_id]['branding']['fanart'] = data['fanart']
    CONFIG['channels'][channel_id]['branding']['banner'] = data['banner']
    CONFIG['channels'][channel_id]['branding']['description'] = data['plot']
    CONFIG['channels'][channel_id]['playlist_id'] = uploads
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
    __parse_uploads(True,uploads,None)

def __parse_uploads(fullscan, playlist_id, page_token=None, update=False):
    if page_token and fullscan:
        url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+"&pageToken="+page_token+"&key="+addon.getSetting('API_key')
    else:
        url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+"&key="+addon.getSetting('API_key')
    req = requests.get(url)
    reply = json.loads(req.content)
    vid = []
    try:
        if 'error' in reply:
            e_reason=reply['error']['errors'][0]['reason']
            e_message=reply['error']['errors'][0]['message']
            if e_reason == 'quotaExceeded':
                e_message = "The request cannot be completed because you have exceeded your quota."
            xbmcgui.Dialog().notification(addonname, e_message, xbmcgui.NOTIFICATION_ERROR, 10000)
            __logger(e_message)
            if len(VIDEOS) >= 1:
                __render()
            raise SystemExit(" error: quota exceeded")
    except NameError:
        pass
    totalResults=int(reply['pageInfo']['totalResults'])
    if LOCAL_CONF['update'] == False:
        PDIALOG.create('Fetching channel info', 'Please wait...')        
    for item in reply['items']:
        VIDEOS.append(item)
        if LOCAL_CONF['update'] == False:
            PDIALOG.update(int(100 * len(VIDEOS) / totalResults), 'Downloading info: ' + str(len(VIDEOS)) + '/' + str(totalResults) )
        vid.append(item['snippet']['resourceId']['videoId'])
    __get_video_details(vid)
    if reply.get('nextPageToken') and fullscan:
        CONFIG['channels'][reply['items'][0]['snippet']['channelId']]['last_page'] = reply['nextPageToken']
        __parse_uploads(True, playlist_id, reply['nextPageToken'])
    else:
        __render()


def __get_video_details(array):
    get = ','.join(array)
    url = "https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id="+get+"&key="+addon.getSetting('API_key')
    req = requests.get(url)
    reply = json.loads(req.content)
    try:
        if 'error' in reply:
            e_reason=reply['error']['errors'][0]['reason']
            e_message=reply['error']['errors'][0]['message']
            if e_reason == 'quotaExceeded':
                e_message = "The request cannot be completed because you have exceeded your quota."
            xbmcgui.Dialog().notification(addonname, e_message, xbmcgui.NOTIFICATION_ERROR, 10000)
            __logger(e_message)
            if len(VIDEOS) >= 1:
                __render()
            raise SystemExit(" error: quota exceeded")
    except NameError:
        pass    
    for item in reply['items']:
        VIDEO_DURATION[item['id']] = __yt_duration(item['contentDetails']['duration'])


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
    API_KEY = addon.getSetting('API_key')
    if API_KEY == "":
        ciyapi=__check_if_youtube_addon_has_api_key()
        if ciyapi != None:
            API_KEY=ciyapi
        else:
            __print("""
You\'ll need to aquire YouTube API key for this addon to work.
for instructions see: https://developers.google.com/youtube/v3/getting-started
""")
            API_KEY=__ask('','API key')
        if API_KEY != "":
            if __check_key_validity(API_KEY) == 'valid':
                addon.setSetting('API_key',API_KEY)
                __print('Key is valid, thank you!')
            else:
                __print('Key is invalid')
                raise SystemExit(" error")
        else:
            __print('Nothing given')
            raise SystemExit
    


addon_handle = int(sys.argv[1])

SEARCH_QUERY={}
def __search(query):
    SEARCH_QUERY.clear()
    channel_url = "https://www.googleapis.com/youtube/v3/search?type=channel&part=id,snippet&maxResults=50&q="+query+"&key="+addon.getSetting('API_key')
    req = requests.get(channel_url)
    reply = json.loads(req.content)
    try:
        if 'error' in reply:
            e_reason=reply['error']['errors'][0]['reason']
            e_message=reply['error']['errors'][0]['message']
            if e_reason == 'quotaExceeded':
                e_message = "The request cannot be completed because you have exceeded your quota."
            __print(e_message)
            raise SystemExit(" error")
    except NameError:
        pass    
    if not 'items' in reply:
        __print('No such channel')
        raise SystemExit(" error")
    ###########################
    # No idea why the first(0) item not always showing on results, hack till i do
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
    __folders('search')





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
        if LOCAL_CONF['update'] == False:
            PDIALOG.update(int(100 * l_count / len(VIDEOS)), data['title'] )
        xbmcvfs.mkdirs(CHANNELS+'\\'+re.sub(r'[^\w\s]', '', data['author'])+'\\'+str(data['season']))
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
        CONFIG['channels'][data['channelId']]['last_video'] = {'video_id' : data['video_id'], 'aired' : aired_timestamp , 'season' : str(data['season']) , 'episode' : str(data['episode']) }
        __save()
        xbmc.executebuiltin("UpdateLibrary(video)")


def __refresh():
    xbmcgui.Dialog().notification(addonname, 'Updating channels', xbmcgui.NOTIFICATION_INFO, 5000)
    for items in CONFIG['channels']:
        VIDEOS.clear()
        VIDEO_DURATION.clear()
        LOCAL_CONF['update'] = True
        __parse_uploads(False,CONFIG['channels'][items]['playlist_id'],None, update=True)
    CONFIG['last_scan'] = int(time.time())
    __save()
    xbmcgui.Dialog().notification(addonname, 'Update finished', xbmcgui.NOTIFICATION_INFO, 5000)


def __folders(*args):
    if 'search' in args:
        for items in SEARCH_QUERY:
            xbmc.log(str(items))
            li = xbmcgui.ListItem(items)
            info = {'plot': SEARCH_QUERY[items]['description']}
            li.setInfo('video', info)
            li.setArt({'thumb': SEARCH_QUERY[items]['thumbnail']})
            url = __build_url({'mode': 'AddItem', 'foldername': SEARCH_QUERY[items]['id'] })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    elif 'Manage' in args:
        for items in CONFIG['channels']:
            plot = ""
            thumb = addon_resources+'/media/youtube_logo.jpg'
            if 'branding' in CONFIG['channels'][items]:
                thumb = CONFIG['channels'][items]['branding']['thumbnail']
                plot = CONFIG['channels'][items]['branding']['description']
                fanart = CONFIG['channels'][items]['branding']['fanart']
                banner = CONFIG['channels'][items]['branding']['banner']
            li = xbmcgui.ListItem(CONFIG['channels'][items]['channel_name'])
            info = {'plot': plot}
            li.setInfo('video', info)
            li.setArt({'thumb': thumb})
            li.addContextMenuItems([('Rescan', ''),('Remove','')])
            url = __build_url({'mode': 'C_MENU', 'foldername': items })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    elif 'menu' in args:
        menuItems = {'Add Channel':'Add channels', 'Manage':'Manage channelino','Refresh all':'Refresh challeino'}
        for items in menuItems:
            pass
            ezy=items.replace(' ','_')
            thumb = addon_resources+'/media/buttons/'+ezy+'.png'
            li = xbmcgui.ListItem(items)
            info = {'plot': menuItems[items]}
            li.setInfo('video', info)
            li.setArt({'thumb': thumb})
            #li.addContextMenuItems([('Rescan', ''),('Remove','')])
            url = __build_url({'mode': 'ManageItem', 'foldername': ezy })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

def __logger(a):
    xbmc.log(str(a),level=xbmc.LOGNOTICE)

def __menu(*args):
    menuItems = ['Add Channel', 'Manage','Refresh all']
    if args:
        xbmcplugin.endOfDirectory(addon_handle)
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
    elif menuItems[ret] == 'Manage':
        __folders('list')
    elif menuItems[ret] == 'Refresh all':
        LOCAL_CONF['update'] = False
        __refresh()



def __C_MENU(C_ID):
    menuItems=['Refresh','Delete']
    ret = xbmcgui.Dialog().select('Manage: '+CONFIG['channels'][C_ID]['channel_name'], menuItems)
    if menuItems[ret] == 'Refresh':
        __add_channel(C_ID)
    elif menuItems[ret] == 'Delete':
        cname=CONFIG['channels'][C_ID]['channel_name']
        cdir = CHANNELS+'\\'+re.sub(r'[^\w\s]', '', cname)
        __logger(cdir)
        ret = xbmcgui.Dialog().yesno('Delete: '+cname, 'Are you sure you wish to remove "'+cname+'"?')
        if ret:
            CONFIG['channels'].pop(C_ID)
            __save()
            ret = xbmcgui.Dialog().yesno('Delete: '+cname, 'Remove "'+cname+'" also from the library?')
            if ret:
                shutil.rmtree(cdir)
                xbmc.executebuiltin("CleanLibrary(video)")
                pass

__start_up()
mode = args.get('mode', None)

try:
    mode = sys.argv[2][1:].split(u'mode')[1][1:]
except IndexError:
    mode = None

try:
    foldername = sys.argv[2][1:].split(u'mode')[0].split(u'=')[1][:-1]
except IndexError:
    foldername = None



if mode is None:
    __folders('menu')
elif mode == 'AddItem':
    __add_channel(foldername)
elif mode == 'ManageItem':
    if foldername == 'Add_Channel':
        query=__ask('','Search for a channel')
        if query:
            LOCAL_CONF['update'] = False
            __search(query)
    elif foldername == 'Manage':
        __folders('Manage')
    elif foldername == 'Refresh_all':
        LOCAL_CONF['update'] = False
        __refresh()
elif mode == 'C_MENU':
    __C_MENU(foldername)
    
elif mode == 'Refresh':
    __refresh()


