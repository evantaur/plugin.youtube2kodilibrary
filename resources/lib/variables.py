# -*- coding: utf-8 -*-
import xbmcaddon
import xbmc
import xbmcvfs
import sys
import json
import urllib

PY_V = sys.version_info[0]


addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
addonID       = addon.getAddonInfo('id')
addon_resources = addon.getAddonInfo("path") + '/resources/'

if PY_V >= 3:
    addon_path = xbmcvfs.translatePath("special://profile/addon_data/"+addonID)
else:
    addon_path = xbmc.translatePath("special://profile/addon_data/"+addonID)



base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

if PY_V >= 3:                           #Python 3
    args = urllib.parse.parse_qs(sys.argv[2][1:])
else:                                   #Python 2
    args = str(sys.argv[2][1:])

         


if PY_V >= 3:
    HOME = xbmcvfs.translatePath("special://profile/library/")
else:
    HOME = xbmc.translatePath("special://profile/library/")

YOUTUBE_DIR = HOME
CHANNELS = YOUTUBE_DIR+'series'
MOVIES = YOUTUBE_DIR+'movies'
MUSIC_VIDEOS = YOUTUBE_DIR+'music_videos'
#MUSIC_VIDEOS = YOUTUBE_DIR+'musicvideos'
VIDEOS = []
VIDEO_DURATION = {}
#PDIALOG = xbmcgui.DialogProgress()
LOCAL_CONF = {'update':False}
AddonString =  xbmcaddon.Addon().getLocalizedString


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
    CONFIG['playlists'] = {}

if not 'playlists' in CONFIG:
    CONFIG['playlists'] = {}
index_file=addon_path+'\\index.json'
if xbmcvfs.exists(index_file):
    if PY_V >= 3:
        with xbmcvfs.File(index_file) as f:     # PYTHON 3 v19+
            INDEX = json.load(f)                #
    else:
        f = xbmcvfs.File(index_file)            # PYTHON 2 v18+
        INDEX = json.loads(f.read())
        f.close()
else:
    INDEX = []   