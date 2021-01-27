# -*- coding: utf-8 -*-
""" 
YOUTUBE CHANNELS TO KODI
"""
import os
import sys
import math
import requests
import xbmcgui
import re


from resources.lib.variables import *
from resources.lib.helper_functions import __logger,__ask,__save,__print, c_download,convert,__get_token_reset, recursive_delete_dir
from resources.lib.music_videos import __add_music, __parse_music
from resources.lib.channels import __add_channel, __parse_uploads,__add_channel_playlist,__parse_playlists,__get_playlists,__select_playlists
from resources.lib.menu import __folders,__search
from resources.lib.refresh import __refresh


def __check_key_validity(key):
    req = requests.get("https://www.googleapis.com/youtube/v3/channels?part=snippet&id=UCS5tt2z_DFvG7-39J3aE-bQ&key="+key)
    if req.status_code == 200:
        return 'valid'
    return 'invalid'

def __start_up():
    API_KEY = addon.getSetting('API_key')
    if API_KEY == "":
        ciyapi=xbmcaddon.Addon('plugin.video.youtube').getSetting('youtube.api.key')
        if ciyapi:
            API_KEY=ciyapi
            if __check_key_validity(API_KEY) == 'valid':
                addon.setSetting('API_key',API_KEY)
                return 1

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







def __Remove_from_index(a):
    index_file=addon_path+'\\index.json'
    if xbmcvfs.exists(index_file):
        if PY_V >= 3:
            with xbmcvfs.File(index_file) as f:     # PYTHON 3 v19+
                INDEX = json.load(f)                #
        else:
            f = xbmcvfs.File(index_file)            # PYTHON 2 v18+
            INDEX = json.loads(f.read())
            f.close()

    local_index_file=a
    if PY_V >= 3:
        with xbmcvfs.File(local_index_file) as f:     # PYTHON 3 v19+
            LOCAL_INDEX = json.load(f)                #
    else:
        f = xbmcvfs.File(local_index_file)            # PYTHON 2 v18+
        LOCAL_INDEX = f.read()
        f.close()
    res = list(filter(lambda i: i not in LOCAL_INDEX, INDEX))
    INDEX = res
    __logger(INDEX)
    __save(data=INDEX,file=index_file)


def __C_MENU(C_ID):
    #0: Refresh
    #1: Delete
    menuItems=[AddonString(30031),AddonString(30039)]
    try:
        ret = xbmcgui.Dialog().select('Manage: '+CONFIG['channels'][C_ID]['channel_name'], menuItems)
        if ret == 0:
            __parse_uploads(False, CONFIG['channels'][C_ID]['playlist_id'])
        elif ret == 1:
            cname=CONFIG['channels'][C_ID]['channel_name']
            cdir = CHANNELS+'\\'+C_ID
            __logger(cdir)
            #Are you sure to remove X...
            ret = xbmcgui.Dialog().yesno(AddonString(30035).format(cname), AddonString(30036).format(cname))
            if ret == True:
                local_index_file = CHANNELS+'\\'+ C_ID + '\\index.json'
                __Remove_from_index(local_index_file)
                CONFIG['channels'].pop(C_ID)
                __save()
                #Remove from library?
                ret = xbmcgui.Dialog().yesno(AddonString(30035).format(cname), AddonString(30037).format(cname))
                if ret:
                    success = recursive_delete_dir(cdir)
                    if success:
                        xbmc.executebuiltin("CleanLibrary(video)")
        else:
            pass
    except KeyError:
        pass
    #__folders('Manage')



def __PLAYLIST_MENU(C_ID):
    #0: Refresh
    #1: Delete
    menuItems=[AddonString(30031),'add/remove playlist items',AddonString(30039)]
    try:
        ret = xbmcgui.Dialog().select('Manage: '+CONFIG['playlists'][C_ID]['channel_name'], menuItems)
        if ret == 0:
             __parse_playlists(False, CONFIG['playlists'][C_ID]['playlist_id'], C_ID)
        elif ret == 1:
            playlists = __get_playlists(CONFIG['playlists'][C_ID]['original_channel_id'])
            data_set = __select_playlists(playlists,C_ID)
            if data_set:
                __logger(data_set)
                __logger('playlists follows:')
                CONFIG['playlists'][C_ID].pop('playlist_id')
                CONFIG['playlists'][C_ID]['playlist_id'] = data_set
                __save()

        elif ret == 2:
            cname=CONFIG['playlists'][C_ID]['channel_name']
            cdir = CHANNELS+'\\'+C_ID
            __logger(cdir)
            #Are you sure to remove X...
            ret = xbmcgui.Dialog().yesno(AddonString(30035).format(cname), AddonString(30036).format(cname))
            if ret == True:
                local_index_file = CHANNELS+'\\'+ C_ID + '\\index.json'
                __Remove_from_index(local_index_file)
                CONFIG['playlists'].pop(C_ID)
                __save()
                #Remove from library?
                ret = xbmcgui.Dialog().yesno(AddonString(30035).format(cname), AddonString(30037).format(cname))
                if ret:
                    success = recursive_delete_dir(cdir)
                    if success:
                        xbmc.executebuiltin("CleanLibrary(video)")
        else:
            pass
    except KeyError:
        pass
    #__folders('Manage')




def __MUSIC_MENU(C_ID):
    #0: Refresh
    #1: Delete
    menuItems=[AddonString(30031),AddonString(30039)]
    try:
        ret = xbmcgui.Dialog().select('Manage: '+CONFIG['music_videos'][C_ID]['channel_name'], menuItems)
        if ret == 0:
            __parse_music(False, CONFIG['music_videos'][C_ID]['playlist_id'])
        elif ret == 1:
            cname=CONFIG['music_videos'][C_ID]['channel_name']
            cdir = MUSIC_VIDEOS+'\\'+C_ID
            __logger(cdir)
            #Are you sure to remove X...
            ret = xbmcgui.Dialog().yesno(AddonString(30035).format(cname), AddonString(30036).format(cname))
            if ret == True:
                CONFIG['music_videos'].pop(C_ID)
                __save()
                #Remove from library?
                ret = xbmcgui.Dialog().yesno(AddonString(30035).format(cname), AddonString(30037).format(cname))
                if ret:
                    success = recursive_delete_dir(cdir)
                    if success:
                        xbmc.executebuiltin("CleanLibrary(video)")
    except KeyError:
        pass



__start_up()
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
elif mode == 'AddItem_tv':
    __add_channel(foldername)
elif mode == 'AddItem_tv_playlist':
    __add_channel_playlist(foldername)
elif mode == 'AddItem_music':
    __add_music(foldername)    
elif mode == 'ManageItem':
    if foldername == 'Add_Channel_tv':
        query=__ask('',AddonString(30038))
        if query:
            LOCAL_CONF['update'] = False
            __search(query,'tv')
    elif foldername == 'Add_Channel_tv_playlist':
        query=__ask('',AddonString(30038))
        if query:
            LOCAL_CONF['update'] = False
            __search(query,'tv_playlist')            
    elif foldername == 'Add_Channel_music':
        query=__ask('',AddonString(30038))
        if query:
            LOCAL_CONF['update'] = False
            __search(query,'music')            
    elif foldername == 'Manage':
        __folders('Manage')
    elif foldername == 'Refresh_all':
        LOCAL_CONF['update'] = False
        __refresh()
elif mode == 'C_MENU':
    __C_MENU(foldername)
elif mode == 'PLAYLIST_MENU':
    __PLAYLIST_MENU(foldername)    
elif mode == 'MUSIC_MENU':
    __MUSIC_MENU(foldername)    
elif mode == 'Refresh':
    __refresh()
elif mode == 'OpenSettings':
    xbmcaddon.Addon(addonID).openSettings()
elif 'SPLIT_EDITOR' in mode:
    params = dict(parse.parse_qsl(parse.urlsplit(sys.argv[2]).query))
    __logger('CUNT_SHIT '+json.dumps(params))
    channel_id = params['playlist']
    action = params['action']
    __PLAYLIST_EDITOR(params)
else:
    __folders('menu')

__folders('menu')

