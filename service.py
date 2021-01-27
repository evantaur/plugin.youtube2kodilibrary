""" 
SERVICE FILE
"""
import time
import json
import xbmc
import xbmcvfs
import xbmcaddon
import sys

PY_V = sys.version_info[0]

addonID       = xbmcaddon.Addon().getAddonInfo('id')
if PY_V >= 3:
    addon_path = xbmcvfs.translatePath("special://profile/addon_data/"+addonID)
else:
    addon_path = xbmc.translatePath("special://profile/addon_data/"+addonID)

NOW = int(time.time())
LAST_SCAN=872835240

#wait a little before starting
#time.sleep(5)

if xbmcvfs.exists(addon_path+'//config.json'):
    with open(addon_path+'//config.json', 'r') as f:
        CONFIG = json.load(f)
        if 'last_scan' in CONFIG:
            LAST_SCAN = CONFIG['last_scan']

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        # Sleep/wait for abort for 10 seconds
        if monitor.waitForAbort(5):
            # Abort was requested while waiting. We should exit
            break
        #xbmc.log(unicode(time.time()) + ' ' + unicode(LAST_SCAN), level=xbmc.LOGNOTICE)
        if (LAST_SCAN + int(xbmcaddon.Addon().getSetting('update_interval'))*3600) <= int(time.time()) and \
            xbmcaddon.Addon().getSetting('API_key') and \
            xbmcaddon.Addon().getSetting('auto_refresh'):
            time.sleep(15)
            xbmc.executebuiltin('RunPlugin(plugin://'+addonID+'/?mode=Refresh)')
            LAST_SCAN=int(time.time())

        #xbmc.log(CONFIG.channels), level=xbmc.LOGNOTICE)

#xbmc.executebuiltin("Action(Back,%s)" % xbmcgui.getCurrentWindowId())