import xbmcgui
import requests
import datetime
import os
import time
from resources.lib.variables import *

AddonString =  xbmcaddon.Addon().getLocalizedString

def convert(n,*args):
    returntime = str(datetime.timedelta(seconds=max(n,0))).split(':')
    if returntime[0] == '00':
        return returntime[1] + ' Minutes'
    return  returntime[0] + ' Hours ' + returntime[1] + ' Minutes'

def __get_token_reset():
    now = datetime.datetime.utcnow() - datetime.timedelta(hours=7)
    reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    seconds = (reset - now).seconds
    return seconds

# Thanks to <3
# https://github.com/kodi-community-addons/script.skin.helper.skinbackup/blob/master/resources/lib/utils.py
def recursive_delete_dir(fullpath):
    '''helper to recursively delete a directory'''
    if PY_V >= 3:
        success = True
        dirs, files = xbmcvfs.listdir(fullpath)

        for file in files:
            success = xbmcvfs.delete(os.path.join(fullpath, file))
        for directory in dirs:
            success = recursive_delete_dir(os.path.join(fullpath, directory))
        success = xbmcvfs.rmdir(fullpath)
        return success 
    else:
        success = True
        if not isinstance(fullpath, unicode):
            fullpath = fullpath.decode("utf-8")
        dirs, files = xbmcvfs.listdir(fullpath)
        for file in files:
            file = file.decode("utf-8")
            success = xbmcvfs.delete(os.path.join(fullpath, file))
        for directory in dirs:
            directory = directory.decode("utf-8")
            success = recursive_delete_dir(os.path.join(fullpath, directory))
        success = xbmcvfs.rmdir(fullpath)
        return success 

def __logger(a):
    if addon.getSetting('logger') == 'true':
        xbmc.log(str(a),level=xbmc.LOGINFO)

def __save(data=CONFIG, file=config_file):
    __logger(data)
    dump = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
    if PY_V >= 3:                                #Python 3
        with xbmcvfs.File(file, 'w') as f:
            result = f.write(dump) 

    else:
        f = xbmcvfs.File(file, 'w')       #Python 2
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
        return
        raise SystemExit()
    return(kb.getText())
  
def __get_playlists(channel_id):
    channel_url = 'https://www.googleapis.com/youtube/v3/playlists?part=contentDetails,id,snippet&maxResults=50&channelId='+ channel_id + "&key="+addon.getSetting('API_key')
    reply = c_download(channel_url)
    return reply


def c_download(req):
    url = req.replace("&key="+addon.getSetting('API_key'),'').split('?')
    url[1] = url[1]
    handle=url[0].split('/')[-1]
    cache_file=addon_path + '/cache/' + handle + '/' + url[1]
    if addon.getSetting('use_cache') == 'true':
        xbmcvfs.mkdirs(addon_path + '/cache/' + handle +'/')
        if xbmcvfs.exists(cache_file[:250]):
            time.sleep(0.2) #sleep timer for debugging
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
            try:
                    if 'error' in reply:
                        e_reason=reply['error']['errors'][0]['reason']
                        e_message=reply['error']['errors'][0]['message']
                        if e_reason == 'quotaExceeded':
                            e_message = "The request cannot be completed because you have exceeded your quota."
                        xbmcgui.Dialog().notification(addonname, e_message, addon_resources+'/icon.png', 10000)
                        __logger(e_message)
                        return "error: quota exceeded"
            except NameError:
                pass

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
    try:
        if 'error' in reply:
            e_reason=reply['error']['errors'][0]['reason']
            e_message=reply['error']['errors'][0]['message']
            if e_reason == 'quotaExceeded':
                e_message = "The request cannot be completed because you have exceeded your quota."
            xbmcgui.Dialog().notification(addonname, e_message, addon_resources+'/icon.png', 10000)
            __logger(e_message)
            raise SystemExit(" error: quota exceeded")
    except NameError:
        pass

    return reply        