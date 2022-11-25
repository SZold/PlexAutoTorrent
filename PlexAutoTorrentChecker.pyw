from collections import defaultdict
from datetime import datetime
import json
import os
import re
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

def toPlainStr(str):
    url_title = re.sub(r'[\W_]+', ' ', str)                     
    return url_title.strip()

def findPlexMedia(torrent, plex, qbt_client):
    tags = torrent.tags.split(", ")
    plexid = ""
    for tag in tags:
        if tag.startswith(config.QBITTORRENT_PLEXID_TAG.format(plexid = '')):
            plexid =tag.replace(config.QBITTORRENT_PLEXID_TAG.lower().format(plexid = ''), "")            
            tagtmp = (tag.replace(config.QBITTORRENT_PLEXID_TAG.lower().format(plexid = ''), "")).split("-")
            if len(tagtmp) == 3:
                tagtmp = tagtmp[0]+"://"+tagtmp[1]+"/"+tagtmp[2]
    for plexMovie in plex.library.section("Movies").search(""):
        plexMovieid = toPlainStr(plexMovie.guid).replace(" ", "-")
        if plexid == plexMovieid:
            if setTorrentProgress(plexMovie, torrent.progress, torrent.state, config.QBITTORRENT_PLEX_MOVIEPROGRESS_FIELD_ID):                
                torrent.tags = torrent.tags + ","+config.QBITTORRENT_COMPLETE_TAG.lower()
            return plexMovie

    for plexShow in plex.library.section("Tv Shows").search(""):
        plexShowid = toPlainStr(plexShow.guid).replace(" ", "-")
        if plexid == plexShowid:
            if setTorrentProgress(plexShow, torrent.progress, torrent.state, config.QBITTORRENT_PLEX_SHOWPROGRESS_FIELD_ID):                
                torrent.tags = torrent.tags + ","+config.QBITTORRENT_COMPLETE_TAG.lower()
            contents = qbt_client.torrents_files(torrent.hash).data
            episodeList = plexShow.episodes()
            for content in contents:
                contentFilename = content.name.split("/")[-1]
                for episode in episodeList:
                    for media in episode.media:
                        for part in media.parts:
                            mediaFilename = part.file.split("\\")[-1]
                            if(mediaFilename == contentFilename):
                                state = "downloading"
                                if hasattr(content, 'is_seed') :
                                    state = "uploading"
                                setTorrentProgress(episode, content.progress, state, config.QBITTORRENT_PLEX_SHOWPROGRESS_FIELD_ID)

            return plexShow

def setTorrentProgress(plexMediaItem, progress, state, field):
    if(QBittorrentStates.__dict__[state] in config.DOWNLOAD_PROGRESS_FORMAT and progress < 1):
        pb = ProgressBar.progress_bar_str(progress, config.PROGRESSBAR_WIDTH, config.PROGRESSBAR_START, config.PROGRESSBAR_STOP, config.PROGRESSBAR_WHOLE, config.PROGRESSBAR_BLANK, [])
        s = config.DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.__dict__[state]].format(progressbar = pb, progress = progress, state = state)
        plexMediaItem.editField(field, s, locked=True)
        return False
    else:
        plexMediaItem.editField(field, "", locked=False)
        plexMediaItem.refresh()
        return True

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
            
            plexuser = settings.PLEXUSERS[0];
            plexuser.account = MyPlexAccount(plexuser.username, plexuser.password)
            plex = plexuser.account.resource(plexuser.servername).connect()  # returns a PlexServer instance     
        except Exception as e:
            print(e)        
            doLogDebug(f'Exception: {E} ::')
        doLogDebug(f'qBittorrent: {qbt_client.app.version} :: {qbt_client.app.web_api_version}')
        
        for torrent in qbt_client.torrents_info():
            tags = torrent.tags.split(", ")
            if(config.QBITTORRENT_PLEXAUTOTORRENT_TAG.lower() in tags):
                if(config.QBITTORRENT_COMPLETE_TAG.lower() not in tags):
                    plexMediaItem = findPlexMedia(torrent, plex, qbt_client)
                    if(plexMediaItem == None):
                        torrent.add_tags(torrent.tags.replace(config.QBITTORRENT_PLEXAUTOTORRENT_TAG.lower(), ""))


            
        doLog("PlexAutoTorrentChecker ::()::::::::::::")    
    except Exception as e:
        doLog(e)
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