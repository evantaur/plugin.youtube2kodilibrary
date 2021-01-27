import re
import xbmcgui
import datetime
import time
from resources.lib.variables import *
from resources.lib.helper_functions import c_download, __save,__logger
from resources.lib.menu import __folders,__search
from resources.lib.music_videos import __parse_music
from resources.lib.channels import __parse_uploads,__parse_playlists

def __refresh():
    # Updating channels...
    xbmcgui.Dialog().notification(addonname, AddonString(30026), addon_resources+'/icon.png', 2500)
    for items in CONFIG['playlists']:
        try:
            VIDEOS.clear()
            VIDEO_DURATION = {}
        except AttributeError:
            del VIDEOS[:]
            VIDEO_DURATION = {}            
        LOCAL_CONF['update'] = True
        pl_items=CONFIG['playlists'][items]['playlist_id']
        __parse_playlists(False, pl_items, items)
    for items in CONFIG['channels']:
        try:
            VIDEOS.clear()
            VIDEO_DURATION = {}
        except AttributeError:
            del VIDEOS[:]
            VIDEO_DURATION = {}            
        LOCAL_CONF['update'] = True
        __parse_uploads(False,CONFIG['channels'][items]['playlist_id'],None, update=True)
    for items in CONFIG['music_videos']:
        try:
            VIDEOS.clear()
            VIDEO_DURATION = {}
        except AttributeError:
            del VIDEOS[:]
            VIDEO_DURATION = {}            
        LOCAL_CONF['update'] = True
        __parse_music(False,CONFIG['music_videos'][items]['playlist_id'],None, update=True)
        __save()




    CONFIG['last_scan'] = int(time.time())
    __save()
    #Update finished.
    xbmcgui.Dialog().notification(addonname, AddonString(30027), addon_resources+'/icon.png', 2500)