# -*- coding: utf-8 -*-
import re
import xbmcgui
import datetime
import time
from resources.lib.variables import *
from resources.lib.helper_functions import c_download, __save,__logger
from resources.lib.menu import __folders,__search

PDIALOG = xbmcgui.DialogProgress()
def __add_music(channel_id):
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
    xbmcvfs.mkdirs(MUSIC_VIDEOS+'\\'+data['channel_id'])
    if channel_id not in CONFIG['music_videos']:
        CONFIG['music_videos'][channel_id] = {}
    CONFIG['music_videos'][channel_id]['channel_name'] = data['title']
    CONFIG['music_videos'][channel_id]['branding'] = {}
    CONFIG['music_videos'][channel_id]['branding']['thumbnail'] = data['thumb']
    CONFIG['music_videos'][channel_id]['branding']['fanart'] = data['fanart']
    CONFIG['music_videos'][channel_id]['branding']['banner'] = data['banner']
    CONFIG['music_videos'][channel_id]['branding']['description'] = data['plot']
    CONFIG['music_videos'][channel_id]['playlist_id'] = uploads
    __save()
    __parse_music(True,uploads,None)

#https://youtu.be/MC7ojZKf2Io
PARSER = {'items' : 0,'total' : 0,'total_steps':0,'steps':0,'scan_year' : 0}
def __parse_music(fullscan, playlist_id, page_token=None, update=False):
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
        if PARSER['steps'] < 1 and LOCAL_CONF['update'] == False:
            PDIALOG.create(AddonString(30016), AddonString(30025))
        try:
            if 'last_video' in CONFIG['music_videos'][reply['items'][0]['snippet']['channelId']]:
                last_video_id = CONFIG['music_videos'][reply['items'][0]['snippet']['channelId']]['last_video']['video_id']
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
                    dialog_string=AddonString(30016) + str(PARSER['items']) + '/' + str(PARSER['total'])
                else:
                    dialog_string=AddonString(30016) + str(PARSER['items']) + '/' + str(PARSER['total'])
                PDIALOG.update(int(100 * PARSER['steps'] / PARSER['total_steps']), dialog_string)
        __get_video_details(vid)
        if 'nextPageToken' not in reply or not fullscan or PARSER['items'] >= PARSER['total']:
            break
        page_token = reply['nextPageToken']
        url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist_id+"&pageToken="+page_token+"&key="+addon.getSetting('API_key')
    if len(VIDEOS) > 0:
        __render('music')

def __get_video_details(array):
    x = [array[i:i + 50] for i in range(0, len(array), 50)]
    for stacks in x:
        get = ','.join(stacks)
        url = "https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id="+get+"&key="+addon.getSetting('API_key')
        reply = c_download(url)
        for item in reply['items']:
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

def __render(type,render_style='Full'):
#RENDER MUSIC    
    if type == 'music':
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
        if 'last_video' in CONFIG['music_videos'][VIDEOS[0]['snippet']['channelId']]:
                latest_aired = int(CONFIG['music_videos'][VIDEOS[0]['snippet']['channelId']]['last_video']['aired'])
                last_video_id = CONFIG['music_videos'][VIDEOS[0]['snippet']['channelId']]['last_video']['video_id']
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

            #Determine ARTIST - TITLE pattern:

            



            #FAILSAFE
            data[u'title'] = item['snippet'][u'title']
            data[u'artist'] = item['snippet']['channelTitle']
            #__logger(data[u'artist'] +' :::: ' +data[u'title'])
            # ARTIST - TITLE
            if '-' in data['title']:
                data[u'title'] = item['snippet'][u'title'].split('-')[1]
                data[u'artist'] = item['snippet'][u'title'].split('-')[0]

            # EXACTLY THE SAME AS ABOVE BUT WITH HYPHEN MINUS
            #               (*angrily stares at Kælan Mikla*)

            elif ':' in data['title']:
                data[u'title'] = item['snippet'][u'title'].split(':')[1]
                data[u'artist'] = item['snippet'][u'title'].split(':')[0]

            elif '|' in data['title']:
                data[u'title'] = item['snippet'][u'title'].split('|')[1]
                data[u'artist'] = item['snippet'][u'title'].split('|')[0]





            data['channelId'] = item['snippet']['channelId']
            data['plot'] = item['snippet']['description']
            season = int(aired.split('-')[0])
            data['video_duration'] = VIDEO_DURATION[data['video_id']]
            if 'maxres' in item['snippet']['thumbnails']:
                data['thumb'] = item['snippet']['thumbnails']['maxres']['url']
            elif item['snippet']['thumbnails']['high']:
                data['thumb'] = item['snippet']['thumbnails']['high']['url']
            elif item['snippet']['thumbnails']['standard']:
                data['thumb'] = item['snippet']['thumbnails']['standard']['url']
            else:
                data['thumb'] = item['snippet']['thumbnails']['default']['url']
            l_count += 1





            if LOCAL_CONF['update'] == False:
                PDIALOG.update(int(100 * PARSER['steps'] / PARSER['total_steps']), data['title'] )
            output = u"""<? xml version = "1.0" encoding = "UTF-8" standalone = "yes"?>
<musicvideo>
    <title>{title}</title>
    <plot>{plot}</plot>
    <runtime>{video_duration}</runtime>
    <thumb>{thumb}</thumb>
    <thumb>{thumb}</thumb>
    <thumb>{thumb}</thumb>
    <thumb>{thumb}</thumb>
    <artist>{artist}</artist>
</musicvideo>
    """.format(**data)
            file_location = MUSIC_VIDEOS+'\\'+channelId+'\\'+data['video_id']
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
            CONFIG['music_videos'][data['channelId']]['last_video'] = {'video_id' : data['video_id'], 'aired' : aired_timestamp }
            __save()
        if addon.getSetting('refresh_after_add') == 'true' and LOCAL_CONF['update'] == False:
            time.sleep(1)
            #xbmc.executebuiltin("UpdateLibrary(video)")
            