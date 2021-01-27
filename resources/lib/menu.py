import xbmcgui
import xbmcplugin
import time
import datetime 
import urllib


from resources.lib.helper_functions import __logger,__ask,__save,__print, c_download,convert,__get_token_reset
from resources.lib.variables import *

SEARCH_QUERY=[]
def __search(query,search_type='tv'):
    del SEARCH_QUERY[:]
    channel_url = "https://www.googleapis.com/youtube/v3/search?type=channel&part=id,snippet&maxResults=10&q="+query+"&key="+addon.getSetting('API_key')
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

    for item in reply['items']:
        data={}
        data['title'] = item['snippet']['title']
        data['id'] = item['snippet']['channelId']
        data['description'] = item['snippet']['description']
        data['thumbnail'] = item['snippet']['thumbnails']['high']['url']
        SEARCH_QUERY.append(data)
    __folders('search', search_type)

def __build_url(query):
    if PY_V >= 3:                       #Python 3
        return base_url + '?' + urllib.parse.urlencode(query)
    else:                               #Python 2
        return base_url + u'?' + urllib.urlencode(query)

def __folders(*args):
    if 'search' in args:
        smode = args[1]
        #__print(smode)
        for items in SEARCH_QUERY:
            __logger(json.dumps(items))
            li = xbmcgui.ListItem(items['title'])
            info = {'plot': items['description']}
            li.setInfo('video', info)
            li.setArt({'thumb': items['thumbnail']})
            url = __build_url({'mode': 'AddItem_'+smode, 'foldername': items['id'] })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    elif 'Manage' in args:
#TV-shows:
        thumb = addon_resources+'/media/buttons/TV_show.png'
        li = xbmcgui.ListItem(AddonString(30043)+':')
        li.setArt({'thumb': thumb})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li, isFolder=False)
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


#TV PLAYLISTS
        thumb = addon_resources+'/media/buttons/TV_playlist.png'
        li = xbmcgui.ListItem(AddonString(30045)+':')
        li.setArt({'thumb': thumb})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li, isFolder=False)
        for items in CONFIG['playlists']:
            plot = ""
            thumb = addon_resources+'/media/youtube_logo.jpg'
            if 'branding' in CONFIG['playlists'][items]:
                thumb = CONFIG['playlists'][items]['branding']['thumbnail']
                plot = CONFIG['playlists'][items]['branding']['description']
                fanart = CONFIG['playlists'][items]['branding']['fanart']
                banner = CONFIG['playlists'][items]['branding']['banner']
            li = xbmcgui.ListItem(CONFIG['playlists'][items]['channel_name'])
            info = {'plot': plot}
            li.setInfo('video', info)
            li.setArt({'thumb': thumb})
            #li.addContextMenuItems([('Rescan', ''),('Remove','')])
            url = __build_url({'mode': 'PLAYLIST_MENU', 'foldername': items })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)




#Music videos
        if len(CONFIG['music_videos']) > 0:
#SEPARATOR
            thumb = addon_resources+'/media/buttons/empty.png'
            li = xbmcgui.ListItem(' ')
            li.setArt({'thumb': thumb})
            li.setInfo('video', {'plot':'Oh hi there! :)'})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url='plugin://'+addonID, listitem=li, isFolder=False)        


            thumb = addon_resources+'/media/buttons/Music_video.png'
            li = xbmcgui.ListItem(AddonString(30042)+':')
            li.setArt({'thumb': thumb})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li, isFolder=False)
            for items in CONFIG['music_videos']:
                plot = ""
                thumb = addon_resources+'/media/youtube_logo.jpg'
                if 'branding' in CONFIG['music_videos'][items]:
                    thumb = CONFIG['music_videos'][items]['branding']['thumbnail']
                    plot = CONFIG['music_videos'][items]['branding']['description']
                    fanart = CONFIG['music_videos'][items]['branding']['fanart']
                    banner = CONFIG['music_videos'][items]['branding']['banner']
                li = xbmcgui.ListItem(CONFIG['music_videos'][items]['channel_name'])
                info = {'plot': plot}
                li.setInfo('video', info)
                li.setArt({'thumb': thumb})
                #li.addContextMenuItems([('Rescan', ''),('Remove','')])
                url = __build_url({'mode': 'MUSIC_MENU', 'foldername': items })
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)



    elif 'menu' in args:

#ADD CHANNEL [as a tv show]       
        thumb = addon_resources+'/media/buttons/Add_TV_show.png'
        li = xbmcgui.ListItem(AddonString(30028) +' ['+AddonString(30040)+']')
        li.setArt({'thumb': thumb})
        url = __build_url({'mode': 'ManageItem', 'foldername': 'Add_Channel_tv' })
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
#ADD CHANNEL PLAYLIST[as a tv show]       
        thumb = addon_resources+'/media/buttons/Add_TV_show.png'
        li = xbmcgui.ListItem(AddonString(30028) +' playlist ['+AddonString(30040)+']' )
        li.setArt({'thumb': thumb})
        url = __build_url({'mode': 'ManageItem', 'foldername': 'Add_Channel_tv_playlist' })
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)        
#ADD CHANNEL        
        thumb = addon_resources+'/media/buttons/Add_Music_video.png'
        li = xbmcgui.ListItem(AddonString(30028) +' ['+AddonString(30041)+']')
        li.setArt({'thumb': thumb})
        url = __build_url({'mode': 'ManageItem', 'foldername': 'Add_Channel_music' })
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
#False
        thumb = addon_resources+'/media/buttons/empty.png'
        li = xbmcgui.ListItem(' ')
        li.setArt({'thumb': thumb})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='plugin://'+addonID, listitem=li, isFolder=False)        
#SEPARATOR
        thumb = addon_resources+'/media/buttons/empty.png'
        li = xbmcgui.ListItem(' ')
        li.setArt({'thumb': thumb})
        li.setInfo('video', {'plot':'Oh hi there! :)'})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='plugin://'+addonID, listitem=li, isFolder=False)        
#SEPARATOR
        thumb = addon_resources+'/media/buttons/empty.png'
        li = xbmcgui.ListItem(' ')
        li.setArt({'thumb': thumb})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='plugin://'+addonID, listitem=li, isFolder=False)                
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
            li = xbmcgui.ListItem(AddonString(30033) + convert(countdown - now),'text')
            li.setArt({'thumb': thumb})
            li.setInfo('video', {'plot': AddonString(30034) + '\n' + convert(__get_token_reset(),'text') })
            li.addContextMenuItems([('Rescan', ''),('Remove','')])
            url = __build_url({'mode': 'OpenSettings', 'foldername': ' ' })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
            now = int(time.time())
    xbmcplugin.endOfDirectory(addon_handle)