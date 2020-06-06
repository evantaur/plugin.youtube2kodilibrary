""" 
YOUTUBE CHANNELS TO KODI
"""
from __future__ import division
from __future__ import with_statement
from __future__ import absolute_import
import sys
PY_V = sys.version_info[0]
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
import codecs
import shutil
import math
if PY_V == 2:
    from urlparse import urlparse

addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
addonID       = addon.getAddonInfo('id')
addon_resources = addon.getAddonInfo("path") + '/resources/'
addon_path = xbmc.translatePath("special://profile/addon_data/"+addonID)
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

if PY_V >= 3:                           #Python 3
    args = urllib.parse.parse_qs(sys.argv[2][1:])
else:                                   #Python 2
    args = str(sys.argv[2][1:])

         


HOME = xbmc.translatePath("special://profile/library/")
YOUTUBE_DIR = HOME
CHANNELS = YOUTUBE_DIR+'series'
MOVIES = YOUTUBE_DIR+'movies'
MUSIC_VIDEOS = YOUTUBE_DIR+'music_videos'
VIDEOS = []
VIDEO_DURATION = {}
PDIALOG = xbmcgui.DialogProgress()
LOCAL_CONF = {'update':False}
AddonString =  xbmcaddon.Addon().getLocalizedString 

#def AddonString(string_id):
#	return addon.getLocalizedString(string_id)

def __build_url(query):
    if PY_V >= 3:                       #Python 3
        return base_url + '?' + urllib.parse.urlencode(query)
    else:                               #Python 2
        return base_url + u'?' + urllib.urlencode(query)

def convert(n,*args):
    if 'text' in args:
        returntime = time.strftime('%H %M', time.gmtime(n)).split(' ')
        if returntime[0] == '00':
            return returntime[1] + ' Minutes'
        return  returntime[0] + ' Hours ' + returntime[1] + ' Minutes'
    return str(time.strftime('%H:%M:%S', time.gmtime(n))) 

def __get_token_reset():
    now = datetime.datetime.utcnow() - datetime.timedelta(hours=7)
    reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    seconds = (reset - now).seconds
    return seconds

CONFIG={}

config_file=addon_path+'\\config.json'       
if xbmcvfs.exists(config_file):
    if PY_V >= 3:
        with xbmcvfs.File(config_file) as f:     # PYTHON 3 v19+
            CONFIG = json.load(f)                #
    else:
        f = xbmcvfs.File(config_file)            # PYTHON 2 v18+
        CONFIG = json.loads(f.read())
        f.close()
else:
    CONFIG = {}
    CONFIG['channels'] = {}
    CONFIG['movies'] = {}
    CONFIG['music_videos'] = {}



def __save():
    dump = json.dumps(CONFIG, sort_keys=True, indent=4, separators=(',', ': '))
    if PY_V >= 3:                                #Python 3
        with open(addon_path+'//config.json', mode='w', encoding='UTF-8', errors='strict', buffering=1) as file:
            file.write(json.dumps(CONFIG, sort_keys=True, indent=4, separators=(',', ': ')))
            file.close()
    else:
        f = xbmcvfs.File(config_file, 'w')       #Python 2
        result = f.write(dump)                   #
        f.close()         

def __print(what):
    try:
        t = what + 1
        xbmcgui.Dialog().ok(addonname, AddonString(what))
    except TypeError:
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
    if kb.isConfirmed() == False:
        __print('Cancelled!')
    	raise SystemExit()
    return(kb.getText())
  
def __check_key_validity(key):
    req = requests.get("https://www.googleapis.com/youtube/v3/channels?part=snippet&id=UCS5tt2z_DFvG7-39J3aE-bQ&key="+key)
    if req.status_code == 200:
        return 'valid'
    return 'invalid'


#if cache then cache, else use live...
def c_download(req):
    url = req.replace("&key="+addon.getSetting('API_key'),'').split('?')
    url[1] = url[1]
    handle=url[0].split('/')[-1]
    cache_file=addon_path + '/cache/' + handle + '/' + url[1]
    if addon.getSetting('use_cache') == 'true':
        xbmcvfs.mkdirs(addon_path + '/cache/' + handle +'/')
        if xbmcvfs.exists(cache_file[:250]):
            if PY_V >= 3:                                # Python 3 v19+
                with open(cache_file[:250], 'r') as f:   # (READ)
                    return json.load(f)                  #
            else:
                f = xbmcvfs.File(cache_file[:250])       # PYTHON 2 v18+
                ret_json = json.loads(f.read())          # (READ)
                f.close()                                # 
                return ret_json                          #
        else:
            requrl = requests.get(req)
            reply = json.loads(requrl.content)
            if PY_V >= 3:                                # Python 3
                with open(cache_file[:250], mode='w', encoding='UTF-8', errors='strict', buffering=1) as file:
                    file.write(json.dumps(reply))        #
                    file.close()                         #
                return reply                             #
            else:
                f = xbmcvfs.File(cache_file[:250], 'w')  #Python 2
                result = f.write(json.dumps(reply))      #
                f.close()                                #
                return reply                             #

    else:
        requrl = requests.get(req)
        reply = json.loads(requrl.content)
        return reply




def __add_channel(channel_id,refresh=None):
    data = {}
    channel_url = "https://www.googleapis.com/youtube/v3/channels?part=brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails&id="+channel_id+"&key="+addon.getSetting('API_key')
    reply = c_download(channel_url)
    try:
        if 'error' in reply:
            e_reason=reply['error']['errors'][0]['reason']
            e_message=reply['error']['errors'][0]['message']
            if e_reason == 'quotaExceeded':
                e_message = "The request cannot be completed because you have exceeded your quota."
            xbmcgui.Dialog().notification(addonname, e_message, addon_resources+'/icon.png', 10000)
            __logger(e_message)
            if len(VIDEOS) >= 1:
                __render()
            raise SystemExit(" error: quota exceeded")
    except NameError:
        pass    
    if 'items' not in reply:
        __print(AddonString(30015)) #No Such channel
        return "no such channel"
    data['channel_id'] = channel_id
    data['title'] = reply['items'][0]['brandingSettings']['channel']['title']
    if 'description' in reply['items'][0]['brandingSettings']['channel']:
        data['plot'] = reply['items'][0]['brandingSettings']['channel']['description']
    else:
        data['plot'] = data['title']
    data['aired'] = reply['items'][0]['snippet']['publishedAt']
    if 'high' in reply['items'][0]['snippet']['thumbnails']:
        data['thumb'] = reply['items'][0]['snippet']['thumbnails']['high']['url']
    else:
        data['thumb'] = reply['items'][0]['snippet']['thumbnails']['default']['url']
    data['banner'] = reply['items'][0]['brandingSettings']['image']['bannerImageUrl']
    if 'bannerTvHighImageUrl' in reply['items'][0]['brandingSettings']['image']:
        data['fanart'] = reply['items'][0]['brandingSettings']['image']['bannerTvHighImageUrl']
    else:
        data['fanart'] = reply['items'][0]['brandingSettings']['image']['bannerImageUrl']
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
    tvshow_file = CHANNELS+'\\'+ re.sub(r'[^\w\s]', '', data['title']) + '\\'+'tvshow.nfo'
    if PY_V >= 3:
        with xbmcvfs.File(tvshow_file, 'w') as f:
            result = f.write(output) 
    else:
        f = xbmcvfs.File(tvshow_file, 'w')                    # Python 2
        result = f.write(bytearray(output.encode('utf-8')))   #
        f.close()  
    __save()
    __parse_uploads(True,uploads,None)


PARSER = {'items' : 0,'total' : 0,'total_steps':0,'steps':0,'scan_year' : 0}
def __parse_uploads(fullscan, playlist_id, page_token=None, update=False):
    __logger('Getting info for playlist: ' + playlist_id)
    url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+"&key="+addon.getSetting('API_key')
    reply = c_download(url)
    last_video_id='Nevergonnagiveyouup'
    while True:
        reply = c_download(url)
        vid = []
        try:
            if 'error' in reply:
                e_reason=reply['error']['errors'][0]['reason']
                e_message=reply['error']['errors'][0]['message']
                if e_reason == 'quotaExceeded':
                    e_message = "The request cannot be completed because you have exceeded your quota."
                xbmcgui.Dialog().notification(addonname, e_message, addon_resources+'/media/notify/error.png', 10000)
                __logger(e_message)
                if len(VIDEOS) >= 1:
                    __render()
                break
        except NameError:
            pass
        totalResults=int(reply['pageInfo']['totalResults'])
        if addon.getSetting('toggle_import_limit') == 'true':
            totalResults = min(int(reply['pageInfo']['totalResults']),int(addon.getSetting('import_limit')))
        if (PARSER['total_steps'] == 0):
            PARSER['total_steps'] = int(totalResults * 4)
        PARSER['total'] = totalResults
        if PARSER['steps'] < 1 and LOCAL_CONF['update'] == False:
            PDIALOG.create(AddonString(30016), AddonString(30025))
        try:
            if 'last_video' in CONFIG['channels'][reply['items'][0]['snippet']['channelId']]:
                last_video_id = CONFIG['channels'][reply['items'][0]['snippet']['channelId']]['last_video']['video_id']
        except KeyError:
            pass
            __logger('no previous scan found')
        for item in reply['items']:
            if LOCAL_CONF['update'] == False and PDIALOG.iscanceled(): 
                return
            season = int(item['snippet']['publishedAt'].split('T')[0].split('-')[0])                
            VIDEOS.append(item)
            PARSER['items'] += 1
            PARSER['steps'] += 1
            if item['snippet']['resourceId']['videoId'] == last_video_id:
                break
            vid.append(item['snippet']['resourceId']['videoId'])
            if LOCAL_CONF['update'] == False:
                # There seems to be a problem with \n and progress dialog in leia
                # so let's not use it in leia....
                if PY_V >= 3:
                	# "Downloading channel info"
                    dialog_string=AddonString(30016) + str(PARSER['items']) + '/' + str(PARSER['total']) + '\n' + AddonString(30017) + str(season)
                else:
                    dialog_string=AddonString(30016) + str(PARSER['items']) + '/' + str(PARSER['total']) + '     ' + AddonString(30017) + str(season)
                PDIALOG.update(int(100 * PARSER['steps'] / PARSER['total_steps']), dialog_string)
        __get_video_details(vid)
        if 'nextPageToken' not in reply or not fullscan or PARSER['items'] >= PARSER['total']:
            break
        page_token = reply['nextPageToken']
        url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+"&pageToken="+page_token+"&key="+addon.getSetting('API_key')

        #if reply.get('nextPageToken') and fullscan:
        #    CONFIG['channels'][reply['items'][0]['snippet']['channelId']]['last_page'] = reply['nextPageToken']
        #    __parse_uploads(True, playlist_id, reply['nextPageToken'])
    if len(VIDEOS) > 0:
        __render()    




def __get_video_details(array):
    x = [array[i:i + 50] for i in range(0, len(array), 50)]
    for stacks in x:
        get = ','.join(stacks)
        url = "https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id="+get+"&key="+addon.getSetting('API_key')
        reply = c_download(url)
        try:
            if 'error' in reply:
                e_reason=reply['error']['errors'][0]['reason']
                e_message=reply['error']['errors'][0]['message']
                if e_reason == 'quotaExceeded':
                    e_message = "The request cannot be completed because you have exceeded your quota."
                xbmcgui.Dialog().notification(addonname, e_message, addon_resources+'/icon.png', 10000)
                __logger(e_message)
                if len(VIDEOS) >= 1:
                    __render()
                raise SystemExit(" error: quota exceeded")
        except NameError:
            pass    
        for item in reply['items']:
            #stick = { item['id'] : __yt_duration(item['contentDetails']['duration']) }
            VIDEO_DURATION[item['id']] = __yt_duration(item['contentDetails']['duration'])
            PARSER['steps'] += 1

def __yt_duration(in_time):
    duration = 1
    time = in_time.split("PT")[1]
    if 'H' in time and 'M' in time and 'S' in time:
        duration = int(time.split("H")[0])*60 + int(time.split("H")[1].split("M")[0])
    elif 'H' in time and 'M' in time:
        duration = int(time.split("H")[0])*60 + int(time.split("H")[1].split("M")[0])
    elif 'H' in time and 'S' in time:
        duration = int(time.split("H")[0])*60
    elif 'M' in time and 'S' in time:
        duration = int(time.split("M")[0])
    return str(duration)


def __check_if_youtube_addon_has_api_key():
    try:
        yt_api_key = xbmcaddon.Addon('plugin.video.youtube').getSetting('youtube.api.key')
        if yt_api_key:
        	# "would you like to use the same API key you have set on YouTube addon?"
            ret = xbmcgui.Dialog().yesno(addonname, AddonString(30018))
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
        	#whine about the missing API key...
            __print(AddonString(30019))
            wrongkey=""
            while True:
                API_KEY=__ask(wrongkey,AddonString(30020))
                if API_KEY != "":
                        if __check_key_validity(API_KEY) == 'valid':
                            addon.setSetting('API_key',API_KEY)
                            #Key is valid, ty....
                            __print(30021)
                            break
                        #key is validn't    
                        __print(30022)
                        wrongkey = API_KEY
                else:
                	#empty
                    __print(30023)
                    raise SystemExit
    newlimit = int(math.ceil(int(addon.getSetting('import_limit')) / 100.0)) * 100
    addon.setSetting('import_limit',str(newlimit))
    


addon_handle = int(sys.argv[1])

SEARCH_QUERY={}
def __search(query):
    SEARCH_QUERY.clear()
    channel_url = "https://www.googleapis.com/youtube/v3/search?type=channel&part=id,snippet&maxResults=50&q="+query+"&key="+addon.getSetting('API_key')
    #req = requests.get(channel_url)
    #reply = json.loads(req.content)
    reply = c_download(channel_url)
    try:
        if 'error' in reply:
            e_reason=reply['error']['errors'][0]['reason']
            e_message=reply['error']['errors'][0]['message']
            if e_reason == 'quotaExceeded':
                e_message = "The request cannot be completed because you have exceeded your quota.Quota resets in :\n\n"+ convert(__get_token_reset(),'text')
            __print(e_message)
            raise SystemExit(" error")
    except NameError:
        pass    
    if not 'items' in reply:
        __print(30015)
        raise SystemExit(" error")
    ###########################
    # No idea why the first(0) item not always showing on results, hack till i do
    ###########################
    SEARCH_QUERY[reply['items'][0]['snippet']['title']+' '] = {}
    SEARCH_QUERY[reply['items'][0]['snippet']['title']+' ']['id'] = reply['items'][0]['snippet']['channelId']
    SEARCH_QUERY[reply['items'][0]['snippet']['title']+' ']['description'] = reply['items'][0]['snippet']['description']
    SEARCH_QUERY[reply['items'][0]['snippet']['title']+' ']['thumbnail'] = reply['items'][0]['snippet']['thumbnails']['high']['url']
    for item in reply['items']:
        SEARCH_QUERY[item['snippet']['title']] = {}
        SEARCH_QUERY[item['snippet']['title']]['id'] = item['snippet']['channelId']
        SEARCH_QUERY[item['snippet']['title']]['description'] = item['snippet']['description']
        SEARCH_QUERY[item['snippet']['title']]['thumbnail'] = item['snippet']['thumbnails']['high']['url']
    __folders('search')


def __FormatTVshowNFO(**args):
    out="""
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
    <runtime>video_duration</runtime>
    <fileinfo>
        <streamdetails>
        <durationinseconds>video_duration</durationinseconds>
        </streamdetails>
    </fileinfo>
</episodedetails>
""".format(**args)    
#####################
# MR DEBUG O'Matic  ##
#################################################
#        xbmc.log(unicode(output),level=xbmc.LOGNOTICE)
#        raise SystemExit(" error")
#################################################

def __render(render_style='Full'):
    if len(VIDEOS) <= 0:
        return
    if LOCAL_CONF['update'] == False:
    	#Importing channel, plz wait.
        PDIALOG.create(AddonString(30024), AddonString(30025))
    year = 0
    episode = 0
    l_count=0
    channelId=VIDEOS[0]['snippet']['channelId']
    VIDEOS.reverse()
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
                PARSER['steps'] += 2
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
            PDIALOG.update(int(100 * PARSER['steps'] / PARSER['total_steps']), data['title'] )
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
        if PY_V >= 3:
            with xbmcvfs.File(write_file, 'w') as f:
                result = f.write(output) 
        else:
            f = xbmcvfs.File(write_file, 'w') 
            f.write(bytearray(output.encode('utf-8')))
            f.close()   
        PARSER['steps'] += 1
        if LOCAL_CONF['update'] == False:
            PDIALOG.update(int(100 * PARSER['steps'] / PARSER['total_steps']), data['title'] )        
        write_file = file_location+'.strm'
        if PY_V >= 3:
            with xbmcvfs.File(write_file, 'w') as f:
                f.write('plugin://plugin.video.youtube/play/?video_id='+data['video_id'])             
        else:
            f = xbmcvfs.File(write_file, 'w')              # Python 2
            f.write(bytearray('plugin://plugin.video.youtube/play/?video_id='+data['video_id'].encode('utf-8')))
            f.close()                 
        PARSER['steps'] += 1
        if LOCAL_CONF['update'] == False:
            PDIALOG.update(int(100 * PARSER['steps'] / PARSER['total_steps']), data['title'] )        
        CONFIG['channels'][data['channelId']]['last_video'] = {'video_id' : data['video_id'], 'aired' : aired_timestamp , 'season' : str(data['season']) , 'episode' : str(data['episode']) }
        __save()
    if addon.getSetting('refresh_after_add') == 'true':
        time.sleep(1)
        xbmc.executebuiltin("UpdateLibrary(video)")


def __refresh():
	# Updating channels...
    xbmcgui.Dialog().notification(addonname, AddonString(30026), addon_resources+'/icon.png', 5000)
    for items in CONFIG['channels']:
        try:
            VIDEOS.clear()
            VIDEO_DURATION = {}
        except AttributeError:
            del VIDEOS[:]
            VIDEO_DURATION = {}            
        LOCAL_CONF['update'] = True
        __parse_uploads(False,CONFIG['channels'][items]['playlist_id'],None, update=True)
    CONFIG['last_scan'] = int(time.time())
    __save()
    #Update finished.
    xbmcgui.Dialog().notification(addonname, AddonString(30027), addon_resources+'/icon.png', 5000)


def __folders(*args):
    if 'search' in args:
        for items in SEARCH_QUERY:
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
            #li.addContextMenuItems([('Rescan', ''),('Remove','')])
            url = __build_url({'mode': 'C_MENU', 'foldername': items })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    elif 'menu' in args:
        menuItems = {'Add Channel':'Add channels', 'Manage':'Manage channelino','Refresh all':'Refresh challeino'}

#ADD CHANNEL        
        thumb = addon_resources+'/media/buttons/Add_Channel.png'
        li = xbmcgui.ListItem(AddonString(30028))
        li.setArt({'thumb': thumb})
        url = __build_url({'mode': 'ManageItem', 'foldername': 'Add_Channel' })
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
#Manage        
        thumb = addon_resources+'/media/buttons/Manage.png'
        li = xbmcgui.ListItem(AddonString(30029))
        li.setArt({'thumb': thumb})
        url = __build_url({'mode': 'ManageItem', 'foldername': 'Manage' })
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
#ADD CHANNEL        
        thumb = addon_resources+'/media/buttons/Refresh_All.png'
        li = xbmcgui.ListItem(AddonString(30030))
        li.setArt({'thumb': thumb})
        url = __build_url({'mode': 'ManageItem', 'foldername': 'Refresh_all' })
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)        
#SEPARATOR
        thumb = addon_resources+'/media/buttons/empty.png'
        li = xbmcgui.ListItem(' ')
        li.setArt({'thumb': thumb})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='plugin://'+addonID, listitem=li, isFolder=True)
#SEPARATOR
        thumb = addon_resources+'/media/buttons/empty.png'
        li = xbmcgui.ListItem(' ')
        li.setArt({'thumb': thumb})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='plugin://'+addonID, listitem=li, isFolder=True)        
#SEPARATOR
        thumb = addon_resources+'/media/buttons/empty.png'
        li = xbmcgui.ListItem(' ')
        li.setArt({'thumb': thumb})
        li.setInfo('video', {'plot':'Oh hi there! :)'})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='plugin://'+addonID, listitem=li, isFolder=True)        
#SEPARATOR
        thumb = addon_resources+'/media/buttons/empty.png'
        li = xbmcgui.ListItem(' ')
        li.setArt({'thumb': thumb})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='plugin://'+addonID, listitem=li, isFolder=True)                
#ADDON SETTINGS
        thumb = addon_resources+'/media/buttons/Settings.png'
        li = xbmcgui.ListItem('Addon Settings')
        li.setArt({'thumb': thumb})
        li.addContextMenuItems([('Rescan', ''),('Remove','')])
        url = __build_url({'mode': 'OpenSettings', 'foldername': ' ' })
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
#ADDON INFO (Next update)
        if 'last_scan' in CONFIG:
            now = int(time.time())
            countdown=int(CONFIG['last_scan'] + int(xbmcaddon.Addon().getSetting('update_interval'))*3600)
            thumb = addon_resources+'/media/buttons/Update.png'
            li = xbmcgui.ListItem(AddonString(30033) + convert(countdown - now))
            li.setArt({'thumb': thumb})
            li.setInfo('video', {'plot': AddonString(30034) + '\n' + convert(__get_token_reset(),'text') })
            li.addContextMenuItems([('Rescan', ''),('Remove','')])
            url = __build_url({'mode': 'OpenSettings', 'foldername': ' ' })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
            now = int(time.time())

    xbmcplugin.endOfDirectory(addon_handle)

def __logger(a):
    xbmc.log(str(a),level=xbmc.LOGNOTICE)

def __C_MENU(C_ID):
	#0: Refresh
	#1: Delete
    menuItems=[AddonString(30031),AddonString(30039)]
    ret = xbmcgui.Dialog().select('Manage: '+CONFIG['channels'][C_ID]['channel_name'], menuItems)
    if ret == 0:
        __add_channel(C_ID)
    elif ret == 1:
        cname=CONFIG['channels'][C_ID]['channel_name']
        cdir = CHANNELS+'\\'+re.sub(r'[^\w\s]', '', cname)
        __logger(cdir)
        #Are you sure to remove X...
        ret = xbmcgui.Dialog().yesno(AddonString(30035).format(cname), AddonString(30036).format(cname))
        if ret == True:
            CONFIG['channels'].pop(C_ID)
            __save()
            #Remove from library?
            ret = xbmcgui.Dialog().yesno(AddonString(30035).format(cname), AddonString(30037).format(cname))
            if ret:
                shutil.rmtree(cdir)
                xbmc.executebuiltin("CleanLibrary(video)")
                pass

__start_up()


#mode = args.get('mode', None)

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
        query=__ask('',AddonString(30038))
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
elif mode == 'OpenSettings':
    xbmcaddon.Addon(addonID).openSettings()    


