import re
import xbmcgui
import datetime
import time
import uuid
from resources.lib.variables import *
from resources.lib.helper_functions import c_download, __save,__logger,__print,__ask
from resources.lib.menu import __folders,__search

PDIALOG = xbmcgui.DialogProgress()
def __add_channel(channel_id,*args):
    data = {}
    channel_url = "https://www.googleapis.com/youtube/v3/channels?part=brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails&id="+channel_id+"&key="+addon.getSetting('API_key')
    reply = c_download(channel_url)
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
#    data['banner'] = reply['items'][0]['brandingSettings']['image']['bannerImageUrl']
#    if 'bannerTvHighImageUrl' in reply['items'][0]['brandingSettings']['image']:
#        data['fanart'] = reply['items'][0]['brandingSettings']['image']['bannerTvHighImageUrl']
#    else:
#        data['fanart'] = reply['items'][0]['brandingSettings']['image']['bannerImageUrl']
    data['banner'] = data['thumb']
    data['fanart'] = data['thumb']
    uploads = reply['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    data['uploader_stripped'] = re.sub(r'[^\w\s]', '', data['title']).replace(" ", "_")
    xbmcvfs.mkdirs(CHANNELS+'\\' + data['channel_id'])
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
    tvshow_file = CHANNELS+'\\'+ data['channel_id'] + '\\'+'tvshow.nfo'
    if PY_V >= 3:
        with xbmcvfs.File(tvshow_file, 'w') as f:
            result = f.write(output) 
    else:
        f = xbmcvfs.File(tvshow_file, 'w')                    # Python 2
        result = f.write(bytearray(output.encode('utf-8')))   #
        f.close()  
    if 'just_the_info' in args:
        return
    __save()
    __parse_uploads(True,uploads,None)

def __add_channel_playlist(channel_id):
    if 'playlists' not in CONFIG:
        CONFIG['playlists'] = {}
    data = {}
    custom_uuid='PL_'+uuid.uuid4().hex
    channel_url = "https://www.googleapis.com/youtube/v3/channels?part=brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails&id="+channel_id+"&key="+addon.getSetting('API_key')
    reply = c_download(channel_url)
    if 'items' not in reply:
        __print(AddonString(30015)) #No Such channel
        return "no such channel"
    playlists = __get_playlists(channel_id)
    data_set = __select_playlists(playlists)
    data['channel_id_original'] = channel_id
    data['channel_id'] = custom_uuid
    data['title'] = data_set['title']
    if 'description' in reply['items'][0]['brandingSettings']['channel']:
        data['plot'] = reply['items'][0]['brandingSettings']['channel']['description']
    else:
        data['plot'] = data['title']
    data['aired'] = reply['items'][0]['snippet']['publishedAt']
    if 'high' in reply['items'][0]['snippet']['thumbnails']:
        data['thumb'] = reply['items'][0]['snippet']['thumbnails']['high']['url']
    else:
        data['thumb'] = reply['items'][0]['snippet']['thumbnails']['default']['url']
    data['banner'] =  data['thumb'] 
    # 
    #
    #reply['items'][0]['brandingSettings']['image']['bannerImageUrl']
    #if 'bannerTvHighImageUrl' in reply['items'][0]['brandingSettings']['image']:
    #    data['fanart'] = data['thumb']
    #    #reply['items'][0]['brandingSettings']['image']['bannerTvHighImageUrl']
    #else:
    #    data['fanart'] = data['thumb']
    #    reply['items'][0]['brandingSettings']['image']['bannerImageUrl']
    data['fanart'] = data['thumb']
    data['banner'] = data['thumb']
    uploads = data_set['items']
    data['uploader_stripped'] = re.sub(r'[^\w\s]', '', data['title']).replace(" ", "_")
    xbmcvfs.mkdirs(CHANNELS+'\\' + data['channel_id'])
    if custom_uuid not in CONFIG['playlists']:
        CONFIG['playlists'][custom_uuid] = {}
    CONFIG['playlists'][custom_uuid]['channel_name'] = data['title']
    CONFIG['playlists'][custom_uuid]['channel_type'] = 'series' #temporarily until music videos and movies are implemented
    CONFIG['playlists'][custom_uuid]['branding'] = {}
    CONFIG['playlists'][custom_uuid]['branding']['thumbnail'] = data['thumb']
    CONFIG['playlists'][custom_uuid]['branding']['fanart'] = data['fanart']
    CONFIG['playlists'][custom_uuid]['branding']['banner'] = data['banner']
    CONFIG['playlists'][custom_uuid]['branding']['description'] = data['plot']
    CONFIG['playlists'][custom_uuid]['original_channel_id'] = channel_id
    CONFIG['playlists'][custom_uuid]['playlist_id'] = uploads
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
    tvshow_file = CHANNELS+'\\'+ data['channel_id'] + '\\'+'tvshow.nfo'
    if PY_V >= 3:
        with xbmcvfs.File(tvshow_file, 'w') as f:
            result = f.write(output) 
    else:
        f = xbmcvfs.File(tvshow_file, 'w')                    # Python 2
        result = f.write(bytearray(output.encode('utf-8')))   #
        f.close()



    local_index_file=CHANNELS+'\\'+ data['channel_id'] + '\\index.json'
    if xbmcvfs.exists(index_file) == False:
        __save(data=[],file=local_index_file)
    __save()
    __parse_playlists(True,uploads,custom_uuid,None)



PARSER = {'items' : 0,'total' : 0,'total_steps':0,'steps':0,'scan_year' : 0}

def __parse_playlists(fullscan, playlists, channel_id, page_token=None, update=False):
    local_index_file=CHANNELS+'\\'+ channel_id + '\\index.json'
    if xbmcvfs.exists(local_index_file):
        if PY_V >= 3:
            with xbmcvfs.File(local_index_file) as f:     # PYTHON 3 v19+
                LOCAL_INDEX = json.load(f)                #
        else:
            f = xbmcvfs.File(local_index_file)            # PYTHON 2 v18+
            LOCAL_INDEX = json.loads(f.read())
            f.close()
    else:
        LOCAL_INDEX = []   




    __logger(playlists)
    for playlist_id in playlists:
        __logger('Getting info for playlist: ' + playlist_id)
        url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+"&key="+addon.getSetting('API_key')
        #reply = c_download(url)
        last_video_id='Nevergonnagiveyouup'
        while True:
            PARSER['items'] = 0
            reply = c_download(url)
            vid = []
            totalResults=int(reply['pageInfo']['totalResults'])
            if addon.getSetting('toggle_import_limit') == 'true':
                totalResults = min(int(reply['pageInfo']['totalResults']),int(addon.getSetting('import_limit')))
            if (PARSER['total_steps'] == 0):
                PARSER['total_steps'] = int(totalResults * 4)
            PARSER['total'] = totalResults
            if PARSER['steps'] < 1 and LOCAL_CONF['update'] == False:
                PDIALOG.create(AddonString(30016), AddonString(30025))

            for item in reply['items']:
                if LOCAL_CONF['update'] == False and PDIALOG.iscanceled(): 
                    return
                season = int(item['snippet']['publishedAt'].split('T')[0].split('-')[0]) 
                item['snippet']['channelId'] = channel_id              
                item['snippet']['channelId'] = channel_id
                PARSER['items'] += 1
                PARSER['steps'] += 1
                item_vid = item['snippet']['resourceId']['videoId']
                if item_vid in INDEX:
                    break
                VIDEOS.append(item)
                vid.append(item['snippet']['resourceId']['videoId'])
                INDEX.append(item['snippet']['resourceId']['videoId'])
                if LOCAL_CONF['update'] == False:
                    # There seems to be a problem with \n and progress dialog in leia
                    # so let's not use it in leia....
                    if PY_V >= 3:
                        # "Downloading channel info"
                        dialog_string=AddonString(30046) + str(PARSER['items']) + '/' + str(PARSER['total']) + '\n' + AddonString(30017) + str(season)
                    else:
                        dialog_string=AddonString(30046) + str(PARSER['items']) + '/' + str(PARSER['total']) + '     ' + AddonString(30017) + str(season)
                    PDIALOG.update(int(100 * PARSER['steps'] / PARSER['total_steps']), dialog_string)
                __get_video_details(vid)
            if 'nextPageToken' not in reply or not fullscan or PARSER['items'] >= PARSER['total']:
                break
            page_token = reply['nextPageToken']
            url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+"&pageToken="+page_token+"&key="+addon.getSetting('API_key')
    if len(VIDEOS) > 0:
        __render('tv_playlist')    



def __parse_uploads(fullscan, playlist_id, page_token=None, update=False):
 
    __logger('Getting info for playlist: ' + playlist_id)
    url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+"&key="+addon.getSetting('API_key')
    reply = c_download(url)
    last_video_id='Nevergonnagiveyouup'
    while True:
        reply = c_download(url)
        vid = []
        totalResults=int(reply['pageInfo']['totalResults'])
        if addon.getSetting('toggle_import_limit') == 'true':
            totalResults = min(int(reply['pageInfo']['totalResults']),int(addon.getSetting('import_limit')))
        if (PARSER['total_steps'] == 0):
            PARSER['total_steps'] = int(totalResults * 4)
        PARSER['total'] = totalResults

        # needed because of changes to folder structure as it now uses channel id for folder name
        # instead of stripped down channel name (no need to worry about non ASCII characters.)
        if not xbmcvfs.exists(CHANNELS+'\\'+ reply['items'][0]['snippet']['channelId'] + '\\'+'tvshow.nfo'):
            success= __add_channel(reply['items'][0]['snippet']['channelId'],'just_the_info')
            __logger('great success')
        if PARSER['steps'] < 1 and LOCAL_CONF['update'] == False:
            PDIALOG.create(AddonString(30016), AddonString(30025))
        try:
            if 'last_video' in CONFIG['channels'][reply['items'][0]['snippet']['channelId']]:
                last_video_id = CONFIG['channels'][reply['items'][0]['snippet']['channelId']]['last_video']['video_id']
        except KeyError:
            __logger('no previous scan found')
        for item in reply['items']:
            if LOCAL_CONF['update'] == False and PDIALOG.iscanceled(): 
                return
            season = int(item['snippet']['publishedAt'].split('T')[0].split('-')[0])                
            VIDEOS.append(item)
            PARSER['items'] += 1
            PARSER['steps'] += 1
            item_vid = item['snippet']['resourceId']['videoId']
            if item_vid == last_video_id:
                break
            if item_vid in INDEX:
                break
            vid.append(item['snippet']['resourceId']['videoId'])
            INDEX.append(item['snippet']['resourceId']['videoId'])
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
    if len(VIDEOS) > 0:
        __render('tv')    




def __get_video_details(array):
    x = [array[i:i + 50] for i in range(0, len(array), 50)]
    for stacks in x:
        get = ','.join(stacks)
        url = "https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id="+get+"&key="+addon.getSetting('API_key')
        reply = c_download(url)
        for item in reply['items']:
            VIDEO_DURATION[item['id']] = __yt_duration(item['contentDetails']['duration'])
            if VIDEO_DURATION[item['id']] == "0":
            	__logger('Buggy ass video: ' + item['id'])
            PARSER['steps'] += 1

def __yt_duration(in_time):
    duration = 1
    if "PT" not in in_time:
        return str(0)
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

def __render(type,render_style='Full'):
    if type == 'tv' or type == 'tv_playlist':




        if len(VIDEOS) <= 0:
            return
        if LOCAL_CONF['update'] == False:
            #Importing channel, plz wait.
            PDIALOG.create(AddonString(30024), AddonString(30025))
        year = 0
        episode = 0
        l_count=0
        channelId=VIDEOS[0]['snippet']['channelId']

        local_index_file=CHANNELS+'\\'+ channelId + '\\index.json'
        LOCAL_INDEX = [] 
        if xbmcvfs.exists(local_index_file):
            if PY_V >= 3:
                with xbmcvfs.File(local_index_file) as f:     # PYTHON 3 v19+
                    LOCAL_INDEX = json.load(f)                #
            else:
                f = xbmcvfs.File(local_index_file)            # PYTHON 2 v18+
                LOCAL_INDEX = json.loads(f.read())
                f.close()

        if type == 'tv' and 'last_video' in CONFIG['channels'][VIDEOS[0]['snippet']['channelId']]:
                year = int(CONFIG['channels'][VIDEOS[0]['snippet']['channelId']]['last_video']['season'])
                episode = int(CONFIG['channels'][VIDEOS[0]['snippet']['channelId']]['last_video']['episode'])
                latest_aired = int(CONFIG['channels'][VIDEOS[0]['snippet']['channelId']]['last_video']['aired'])
                last_video_id = CONFIG['channels'][VIDEOS[0]['snippet']['channelId']]['last_video']['video_id']
        for item in sorted(VIDEOS, key = lambda i: i["snippet"]["publishedAt"],reverse=False):
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
            try:
                data['video_duration'] = VIDEO_DURATION[data['video_id']]
            except KeyError:
                data['video_duration'] = 0 # NO FUCKING IDEA WHAT IS GOING ON
            if 'maxres' in item['snippet']['thumbnails']:
                data['thumb'] = item['snippet']['thumbnails']['maxres']['url']
            elif 'high' in item['snippet']['thumbnails']:
                data['thumb'] = item['snippet']['thumbnails']['high']['url']
            elif 'standard' in item['snippet']['thumbnails']:
                data['thumb'] = item['snippet']['thumbnails']['standard']['url']
            else:
                data['thumb'] = item['snippet']['thumbnails']['default']['url']
            episode += 1
            data['episode'] = episode
            data['season'] = season
            l_count += 1
            if LOCAL_CONF['update'] == False:
                PDIALOG.update(int(100 * PARSER['steps'] / PARSER['total_steps']), data['title'] )
            xbmcvfs.mkdirs(CHANNELS+'\\'+data['channelId']+'\\'+str(data['season']))
            LOCAL_INDEX.append(data['video_id'])
            output = u"""<? xml version = \"1.0\" encoding = \"UTF-8\" standalone = \"yes\"?>
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
            file_location = CHANNELS+'\\'+data['channelId']+'\\'+str(data['season']) + '\\s' + str(data['season']) +'e' + str(data['episode'])
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

            if (addon.getSetting('YT_client') == "0"):
            	youtube_client='plugin://plugin.video.youtube/play/?video_id='
            elif (addon.getSetting('YT_client') == "1"):
            	youtube_client='plugin://plugin.video.tubed/?mode=play&video_id='

            if PY_V >= 3:
                with xbmcvfs.File(write_file, 'w') as f:
                    f.write(youtube_client+data['video_id'])             
            else:
                f = xbmcvfs.File(write_file, 'w')              # Python 2
                f.write(bytearray(youtube_client+data['video_id'].encode('utf-8')))
                f.close()                 
            PARSER['steps'] += 1
            if LOCAL_CONF['update'] == False:
                PDIALOG.update(int(100 * PARSER['steps'] / PARSER['total_steps']), data['title'] )        
            if type == 'tv':
                CONFIG['channels'][data['channelId']]['last_video'] = {'video_id' : data['video_id'], 'aired' : aired_timestamp , 'season' : str(data['season']) , 'episode' : str(data['episode']) }
            __save()
            __save(data=INDEX,file=index_file)
            __save(data=LOCAL_INDEX,file=local_index_file)
        if addon.getSetting('refresh_after_add') == 'true' and LOCAL_CONF['update'] == False:
            time.sleep(1)
            #xbmc.executebuiltin("UpdateLibrary(video)")



def __get_playlists(channel_id):
    playlist_dict = {}
    channel_url = 'https://www.googleapis.com/youtube/v3/playlists?part=contentDetails,id,snippet&maxResults=50&channelId='+ channel_id + "&key="+addon.getSetting('API_key')
    while True:
        reply = c_download(channel_url)
        if len(playlist_dict) == 0:
            playlist_dict = reply
        else:
            playlist_dict['items'].extend(reply['items'])
        if 'nextPageToken' not in reply:
            break
        else:
            page_token = reply['nextPageToken']
            channel_url = 'https://www.googleapis.com/youtube/v3/playlists?part=contentDetails,id,snippet&maxResults=50&channelId='+ channel_id + "&pageToken="+page_token+ "&key="+addon.getSetting('API_key')
    return playlist_dict

def __select_playlists(a,C_ID=[],selected=None):
    menuItems=[]
    _preselect=[]
    __logger(a)
    #__logger(json.dumps(a, indent=4, sort_keys=True))
    if C_ID:
        for idx,i in enumerate(a['items']):
            menuItems.append(i['snippet']['title'])
            if i['id'] in CONFIG['playlists'][C_ID]['playlist_id']:
                _preselect.append(idx)
        dialog = xbmcgui.Dialog()
        ret = dialog.multiselect("Choose playlists", menuItems,preselect=_preselect)
        if ret:
            __logger(ret)
            playlist_ids=[]
            for x in ret:
                playlist_ids.append(a['items'][x]['id'])
            return playlist_ids
    else:
        for i in a['items']:
            menuItems.append(i['snippet']['title'])
        __logger(a['items'])
        dialog = xbmcgui.Dialog()
        ret = dialog.multiselect("Choose playlists", menuItems)
        if ret:
            __logger(ret)
            playlist_ids=[]
            for x in ret:
                playlist_ids.append(a['items'][x]['id'])
            __logger(playlist_ids)
            playlist_title=__ask(a['items'][0]['snippet']['title'],'Name of playlist')
            return_object={}
            return_object['title'] = playlist_title
            return_object['items'] = playlist_ids
            return return_object

