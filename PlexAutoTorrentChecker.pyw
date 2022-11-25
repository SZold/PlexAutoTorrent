from collections import defaultdict
from datetime import datetime
import json
import os
from sys import argv
import traceback
from PlexAutoTorrentClasses import ProgressBar, QBittorrentStates
from plexapi.myplex import MyPlexAccount
from config import config
from settings import settings
import qbittorrentapi

_DO_LOG = False
_DO_DRYRUN = False

def doLogDebug(string):   
    txt = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')+" :: " + string  
    print(txt)
    #doLog(string)    
    a = ""

def doLog(string):    
    try:
        if(_DO_LOG and settings.LOG_FILEPATH != ''):
            txt = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')+" :: " + string + "\n"
            os.makedirs(os.path.dirname(settings.LOG_FILEPATH), exist_ok=True)
            f= open(settings.LOG_FILEPATH,"a")
            f.write(txt)
            print(txt)
            f.close()
    except:
        print(string)

def findPlexMedia(torrent):
    plexuser = settings.PLEXUSERS[0];
    plexuser.account = MyPlexAccount(plexuser.username, plexuser.password)
    plex = plexuser.account.resource(plexuser.servername).connect()  # returns a PlexServer instance 
    plex.library.search("")

def main(args):
    try:
        doLogDebug("Running PlexAutoTorrentChecker "+json.dumps(args)+":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")    
        global DEBUG_COUNT
        global _DO_LOG
        _DO_LOG = True if(args["logging"]) else False
        global _DO_DRYRUN
        _DO_DRYRUN = True if(args["dryrun"]) else False

        qbt_client = qbittorrentapi.Client(host=settings.QBITTORRENT_HOST, port=settings.QBITTORRENT_PORT,username=settings.QBITTORRENT_USER,password=settings.QBITTORRENT_PASS,)

        try:
            qbt_client.auth_log_in()
        except qbittorrentapi.LoginFailed as e:
            print(e)        
        doLogDebug(f'qBittorrent: {qbt_client.app.version} :: {qbt_client.app.web_api_version}')
        
        for torrent in qbt_client.torrents_info():
            if(QBittorrentStates.__dict__[torrent.state] in config.DOWNLOAD_PROGRESS_FORMAT):
                findPlexMedia(torrent)
                pb = ProgressBar.progress_bar_str(torrent.progress, config.PROGRESSBAR_WIDTH, config.PROGRESSBAR_START, config.PROGRESSBAR_STOP, config.PROGRESSBAR_WHOLE, config.PROGRESSBAR_BLANK, [])
                pb2 = ProgressBar.progress_bar_str_v2(torrent.progress, config.PROGRESSBAR_WIDTH, config.PROGRESSBAR_V2)

                doLogDebug(f'torrent: {torrent.name} :: {torrent.state} ::'+ config.DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.__dict__[torrent.state]].format(progressbar = pb2, t = torrent) + ' :: '+config.DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.__dict__[torrent.state]].format(progressbar = pb, t = torrent))

            
        doLog("PlexAutoTorrentChecker ::()::::::::::::")    
    except Exception:
        doLog(traceback.format_exc())
        return False


def arvToDict(args):
    d=defaultdict(list)
    args2 = []
    for a in args[1:]:
         args2.append(a) if not a.find("=") == -1 else args2.append( a + "=True")
    for k, v in ((k.lstrip('-'), v) for k,v in (a.split('=') for a in args2)):
        d[k].append(v) if not v.lower() in ['true', '1'] else d[k].append(True)
    return d


if __name__ == "__main__":
    main(arvToDict(argv))