from collections import defaultdict
from datetime import datetime
import traceback
from PlexAutoTorrentClasses import PatTvShow, TvShowFollowType
from config import config
import json
import os
import shutil
from plexapi.myplex import MyPlexAccount
import re
import urllib.parse
import nova2
import subprocess
from sys import argv
import requests

from settings import settings

_TORRENT_FILE_PATH = settings.TORRENT_FILE_PATH
_QBITTORRENT_PATH = settings.QBITTORRENT_PATH
_MOVIES_PATH = settings.MOVIES_PATH
_LOG_FILEPATH = settings.LOG_FILEPATH
_DO_LOG = False
_DO_DRYRUN = False

CAT_CONVERT = {
    "movie": "movies",
    "show": "tv"
}

TELEGRAM_REPORT = {
    "movies": [],
    "shows": [],
    "f1": [],
    "error": []
}

DEBUG_COUNT = {
        "users": 0,
        "movie": 0,
        "torrentFileFound": 0,
        "magnetDownloaded": 0,
        "torrentDownloaded": 0,
        "notFound": 0,
        "OnPlex": 0
}

SCRIPT_PATH = os.path.realpath(__file__)

def safe_copy(file_path, out_path):
    name = os.path.basename(file_path)
    if not os.path.exists(out_path):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        shutil.copy(file_path, out_path)
        doLog("Copied: '"+ file_path +"' to '"+ out_path+"'")
    else:        
        doLog("Found: '"+ file_path +"' to '"+ out_path+"'")

def doLogDebug(string):   
    txt = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')+" :: " + string  
    print(txt)
    #doLog(string)    
    a = ""

def doLog(string):    
    if(_DO_LOG):
        txt = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')+" :: " + string + "\n"
        os.makedirs(os.path.dirname(_LOG_FILEPATH), exist_ok=True)
        f= open(_LOG_FILEPATH,"a")
        f.write(txt)
        print(txt)
        f.close()

def doDownloadTorrent(torrentPluginResult, torrent_path, save_path):
    result = None
    if torrentPluginResult is not None: 
        doLogDebug("movie"+ torrent_path +"torrentPluginResult is not None")
        if len(torrentPluginResult) > 0:            
            os.chdir(os.path.dirname(SCRIPT_PATH))
            proc = subprocess.run( ['pyw', 'nova2dl.py',  torrentPluginResult[5], torrentPluginResult[0]], capture_output=True)
            torrent = proc.stdout.decode().split(" ") 
            #doLog(", "+torrentPluginResult[1] + ", " + torrent_path +":::  "+torrentPluginResult[-1])
            if len(torrent) > 0: 
                if(torrent[0].startswith("magnet:?")):       
                    if not _DO_DRYRUN:             
                        if not os.path.exists(torrent_path+"*"):
                            os.makedirs(os.path.dirname(torrent_path+".magnet"), exist_ok=True)
                            f= open(torrent_path+".magnet","w+")
                            f.write(torrent[0])
                            f.close()
                        os.chdir(os.path.dirname(_QBITTORRENT_PATH)) 
                        proc = subprocess.run([_QBITTORRENT_PATH, torrent[0], "--add-paused=false", "--skip-dialog=true", '--sequential', '--save-path='+save_path+'/']) 
                        if proc.returncode > 0:
                            TELEGRAM_REPORT["error"].append("Return: "+str(proc.returncode)+"; \n stderr: "+proc.stderr.decode()+"; \n stdout: "+proc.stdout.decode())
                            os.remove(torrent_path+".magnet") 
                            doLog(proc.returncode)  
                            doLog(proc.stderr.decode())
                            doLog(proc.stdout.decode())
                        else:    
                            DEBUG_COUNT['magnetDownloaded'] = DEBUG_COUNT['magnetDownloaded'] + 1 
                            result = torrent_path+".magnet"
                    else:    
                        DEBUG_COUNT['magnetDownloaded'] = DEBUG_COUNT['magnetDownloaded'] + 1 
                        doLogDebug("DRY RUN:  "+torrent_path+"; "+save_path)
                        result = torrent_path+".magnet"
                          
                    doLogDebug("Magnet Link:  ")
                else:  
                    if not _DO_DRYRUN:                     
                        safe_copy(torrent[0], torrent_path+".torrent")    
                        cmd = [_QBITTORRENT_PATH, '"'+torrent_path+".torrent"+'"', "--add-paused", "false", "--save-path",'"'+save_path+'/"']
                        cmd2 = ' '.join(cmd)
                        os.chdir(os.path.dirname(_QBITTORRENT_PATH))
                        proc = subprocess.run([_QBITTORRENT_PATH, ''+torrent_path+".torrent"+'', "--add-paused=false", '--sequential',  "--skip-dialog=true",'--save-path='+save_path+'/'])  
                        if proc.returncode > 0:
                            TELEGRAM_REPORT["error"].append("Return: "+str(proc.returncode)+"; \n stderr: "+proc.stderr.decode()+"; \n stdout: "+proc.stdout.decode())
                            os.remove(torrent_path+".torrent") 
                            doLog(proc.returncode)  
                            doLog(proc.stderr.decode())
                            doLog(proc.stdout.decode())  
                        else:
                            DEBUG_COUNT['torrentDownloaded'] = DEBUG_COUNT['torrentDownloaded'] + 1 
                            result = torrent_path+".torrent"
                    else:
                        DEBUG_COUNT['torrentDownloaded'] = DEBUG_COUNT['torrentDownloaded'] + 1 
                        doLogDebug("DRY RUN:  "+torrent_path+"; "+save_path)
                        result = torrent_path+".torrent"
                    #doLog(foundEngine+ ", "+foundObj[1] + ", " + movie.type+ ", "+imdb.id+":::  "+torrent[0]) "--skip-dialog", "true",
    return result



def doMovies(movieList, plexConnection, plexuser):
    for movie in movieList:
        global DEBUG_COUNT
        DEBUG_COUNT['movie'] = DEBUG_COUNT['movie'] + 1
        imdb = list(filter(lambda guid: guid.id.startswith("imdb:"), movie.guids))[0]
        url_title = re.sub(r'[\W_]+', ' ', movie.title) + " " + str(movie.year) 
        torrent_path =  _TORRENT_FILE_PATH+"/"+movie.type+"/"+re.sub(r'[\W_]+', '', imdb.id)+"_" + url_title +""

        movieOnPlex = plexConnection.library.search(guid=movie.guid, libtype=movie.type)

        if len(movieOnPlex) == 0:
            foundObj = None
            foundEngine = "--"
            for engine in plexuser.movie_engine_order:
                for extra in plexuser.movie_extra_order:
                    if foundObj is None:
                        torrent_path = _TORRENT_FILE_PATH+movie.type+"/"+re.sub(r'[\W_]+', '', imdb.id)+"_"+engine+"_" + url_title +""                    
                        
                        url_title = re.sub(r'[\W_]+', ' ', movie.title) + " " + str(movie.year) + " " + extra                    
                        url_title = url_title.strip();
                        #doLog(movie.title + ", "+ url_title + ", " + movie.type+", "+engine+", "+ str(movie.year)+ ", "+imdb.id)                        
                        os.chdir(os.path.dirname(SCRIPT_PATH))
                        proc = subprocess.run( ['pyw', 'nova2.py',  engine, CAT_CONVERT[movie.type], url_title], capture_output=True)
                        results = proc.stdout.decode().split("\n")   
                        resultArr = results[0].split("|")
                        if len(resultArr) > 1:
                            foundObj = resultArr
                            foundEngine = engine
                        else:
                            resultArr = ["","","","","","","","","",""]
            
            if foundObj is not None: 
                res = doDownloadTorrent(foundObj, torrent_path, _MOVIES_PATH+url_title)                
                if res is not None:                    
                    TELEGRAM_REPORT["movies"].append({"user": plexuser.username, "title": movie.title, "year": movie.year, "torrentpath": res})
            else:
                doLog(foundEngine+ ", "+movie.title + " " + str(movie.year) +", " + movie.type+ ", "+imdb.id+":::  Not Found! ")
                DEBUG_COUNT['notFound'] = DEBUG_COUNT['notFound'] + 1 
        else:            
            doLogDebug("OnPlex, "+movie.title + " "+str(movie.year)+ ", " + movie.type+ ", "+imdb.id+":::  Found On Plex!! ")
            DEBUG_COUNT['OnPlex'] = DEBUG_COUNT['OnPlex'] + 1 
                
        #doLog("\n\n")

def getTvShowConfigs(show, plexuser):
    result = PatTvShow( show=show,      
                        engines=[],
                        episode_to_download=settings.DEFAULT_EPISODES_TO_DOWNLOAD  ,
                        unwatched_episode_trigger=settings.DEFAULT_UNWATCHED_EPISODE_TRIGGER,
                        follow_type=settings.DEFAULT_TVSHOW_FOLLOWTYPE
                      )
    for label in show.labels:
        if label.tag == config.MEDIA_LABEL_EVERY_EPISODE:
            result.follow_type = TvShowFollowType.All
        elif label.tag == config.MEDIA_LABEL_SHOW_NEXT_SEASON:
            result.follow_type = TvShowFollowType.NextSeason
        elif label.tag == config.MEDIA_LABEL_SHOW_BATCH:
            result.follow_type = TvShowFollowType.Batch
        elif label.tag == config.MEDIA_LABEL_SHOW__FORCE:
            result.force = True
        elif label.tag.startswith(config.MEDIA_LABEL_SHOW_EPISODES_TO_DOWNLOAD+"="):
            lb = label.tag.split("=")
            result.episode_to_download = lb[1]
        elif label.tag.startswith(config.MEDIA_LABEL_TRIGGER+"="):
            lb = label.tag.split("=")
            result.unwatched_episode_trigger = lb[1]
        elif label.tag.startswith(config.MEDIA_LABEL_ENGINE+"="):
            lb = label.tag.split("=")
            result.engines.append(lb[1])
    if(len(result.engines) == 0):
        result.engines.append(plexuser.show_engine_order)
        
    return result

def doShows(showList, plexConnection, plexuser):
    result = []
    for showOnWatchList in showList:
        global DEBUG_COUNT
        showOnServer = plexConnection.library.search(guid=showOnWatchList.guid, libtype='show')
        unwatchedCount = -1
        episodeToDownload = []
        isShowOnServer = False
        
        if len(showOnServer) != 0:
            isShowOnServer = True
            show = showOnServer[0]
            collectedEpisodeList = show.episodes()
            collectedSeasonEpisodeList = list(map(lambda ep: {"s": ep.seasonNumber, "e": ep.episodeNumber}, collectedEpisodeList))            
        else:
            isShowOnServer = False
            show = showOnWatchList
            collectedEpisodeList = []
            collectedSeasonEpisodeList = []
        
        tvshowConfig = getTvShowConfigs(show, plexuser)

        isShowOnPlexMetadata = False
        try:
            metadataEpisodeList = getPlexMetadataEpisodeList(plexuser, show)
            isShowOnPlexMetadata = True
        except:
            isShowOnPlexMetadata = False
            tvshowConfig.force = True
            metadataEpisodeList = []
            
        unwatchedList = list(filter(lambda ep: not ep.isPlayed, collectedEpisodeList))
        unwatchedCount = len(unwatchedList)
            
        if isShowOnPlexMetadata:
            nonCollectedSeasonEpisodeList = list(filter(lambda ep: {"s": ep.seasonNumber, "e": ep.episodeNumber} not in collectedSeasonEpisodeList, metadataEpisodeList))
        else:
            nonCollectedSeasonEpisodeList = []

        episodeToDownload = getNextEpisodesList(tvshowConfig, collectedSeasonEpisodeList, list(map(lambda ep: {"s": ep.seasonNumber, "e": ep.episodeNumber}, nonCollectedSeasonEpisodeList)))

        if((unwatchedCount < tvshowConfig.unwatched_episode_trigger) and (len(episodeToDownload) > 0)):
            doLog("DO   ::"+showOnWatchList.title+": "+ str(unwatchedCount)+ ' || '+ str(len(nonCollectedSeasonEpisodeList)) + " < "+str(tvshowConfig.unwatched_episode_trigger)+" :: "+json.dumps(episodeToDownload)+ " :: "+json.dumps(tvshowConfig.engines))
        elif(tvshowConfig.force):
            doLogDebug("FORCE::"+showOnWatchList.title+"(metadata:"+str(isShowOnPlexMetadata)+") is forced download"+ " :: "+json.dumps(tvshowConfig.engines) )
        else:
            doLogDebug("NOT  ::"+showOnWatchList.title+": "+ str(unwatchedCount)+ ' && '+ str(len(nonCollectedSeasonEpisodeList)) + " >= "+str(tvshowConfig.unwatched_episode_trigger)+" :: "+str(len(episodeToDownload)))
        
        result.append({"tvshowConfig": tvshowConfig, "episodeToDownload": episodeToDownload})

def getNextEpisodesList(tvshowConfig, collectedSeasonEpisodeList, nonCollectedSeasonEpisodeList):
    result = []
    if(not tvshowConfig.force):
        match tvshowConfig.follow_type:
            case TvShowFollowType.NextSeason:  
                if(len(collectedSeasonEpisodeList) > 1):   
                    for ncEP in nonCollectedSeasonEpisodeList:
                        if(ncEP["s"] == collectedSeasonEpisodeList[-1]["s"] and ncEP["e"] > collectedSeasonEpisodeList[-1]["e"]) or (ncEP["s"] == collectedSeasonEpisodeList[-1]["s"]+1):
                            result.append(ncEP)  
                else:  
                    for ncEP in nonCollectedSeasonEpisodeList:
                            if(ncEP["s"] == 1):
                                result.append(ncEP)    
            case TvShowFollowType.All: 
                result = nonCollectedSeasonEpisodeList  
            case TvShowFollowType.Batch: 
                result = nonCollectedSeasonEpisodeList[0: tvshowConfig.episode_to_download]
            case _:
                result = nonCollectedSeasonEpisodeList[0: tvshowConfig.episode_to_download]

    if(tvshowConfig.episode_to_download >= 0):
        result = nonCollectedSeasonEpisodeList[0: tvshowConfig.episode_to_download]

    return result

def getPlexMetadataEpisodeList(plexuser, show):
    result = []
    params = {}
    #params['X-Plex-Token'] = plexuser.account._token
    params['X-Plex-Container-Start'] = 0
    params['X-Plex-Container-Size'] = config.PLEX_CONTAINER_SIZE

    showGUID = show.guid.replace("plex://show/", "")
    sURL = f'{plexuser.account.METADATA}/library/metadata/{showGUID}/children'
    try:
        mdShowXML =  plexuser.account.query(sURL, params=params)
    except Exception:
        doLog(f'ERROR: metadata not found for show ({sURL})')
    
    for season in plexuser.account.findItems(mdShowXML):
        if not (season.seasonNumber == 0 and config.SKIP_SPECIALS):
            seasonGUID = season.guid.replace("plex://season/", "")
            epURL = f'{plexuser.account.METADATA}/library/metadata/{seasonGUID}/children'
            try:
                mdSeasonXML =  plexuser.account.query(epURL, params=params)      
            except Exception:
                doLog(f'ERROR: metadata not found for season ({epURL})')    

            for episode in plexuser.account.findItems(mdSeasonXML):
                result.append(episode)
    return result

def main(args):
    try:
        doLogDebug("Running PlexAutoTorrent "+json.dumps(args)+":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")    
        global DEBUG_COUNT
        global _DO_LOG
        _DO_LOG = True if(args["logging"]) else False
        global _DO_DRYRUN
        _DO_DRYRUN = True if(args["dryrun"]) else False

        for plexuser in settings.PLEXUSERS:
            DEBUG_COUNT['users'] = DEBUG_COUNT['users'] + 1
            doLogDebug("plexuser: "+ plexuser.username )
            plexuser.account = MyPlexAccount(plexuser.username, plexuser.password)
            plex = plexuser.account.resource(plexuser.servername).connect()  # returns a PlexServer instance 

            if not args["skipmovies"]:
                doLogDebug("movies: "+ plexuser.username )
                #doMovies(plexuser.account.watchlist(filter='released', sort='rating:desc', libtype='movie'), plex, plexuser)
                
            if not args["shipshows"]:
                doLogDebug("shows: "+ plexuser.username )
                doShows(plexuser.account.watchlist(filter='released', sort='rating:desc', libtype='show'), plex, plexuser)

        if(args["telegramreport"]):
            sendTelegramReport(json.dumps(TELEGRAM_REPORT)+" \n "+json.dumps(DEBUG_COUNT))

        doLog("telegramreport ::("+json.dumps(TELEGRAM_REPORT)+")")
        doLog("PlexAutoTorrent ::("+json.dumps(DEBUG_COUNT)+"):::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")    
    except Exception:
        doLog(traceback.format_exc())
        return False

def sendTelegramReport(report):
    if(DEBUG_COUNT["torrentDownloaded"]+DEBUG_COUNT["magnetDownloaded"] > 0):
        token = settings.TELEGRAM_BOT_TOKEN
        url = f"https://api.telegram.org/bot{token}"
        # keyboard = {
        #     "inline_keyboard": [
        #         [
        #             {"text": "Allow", "callback_data": "allow"},
        #             {"text": "Deny", "callback_data": "deny"}
        #         ]
        #     ]
        # }

        params = {"chat_id": settings.TELEGRAM_RAW_ID, 
                  "text": (report)
                  #,"reply_markup": json.dumps(keyboard)
                 }
                 
        if not _DO_DRYRUN:    
            r = requests.get(url + "/sendMessage", params=params)            
        else:
            doLogDebug("DRY RUN:  "+url+"url; "+json.dumps(params))


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


class Object:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)    

        #https://metadata.provider.plex.tv/library/sections/watchlist?X-Plex-Token=uxT7yvhM6M3GVfYG5Tsx
        #https://metadata.provider.plex.tv/library/metadata/5d9c084fec357c001f9ab4d8/children?X-Plex-Token=uxT7yvhM6M3GVfYG5Tsx
        #https://metadata.provider.plex.tv/library/metadata/5d9c0a8e02391c001f5a0e98/children?X-Plex-Token=uxT7yvhM6M3GVfYG5Tsx
        #https://metadata.provider.plex.tv/library/metadata/5d9c09b32192ba001f3210a2/children?X-Plex-Token=uxT7yvhM6M3GVfYG5Tsx
        #https://metadata.provider.plex.tv/library/metadata/602e649867f4c8002ce3a62d/children?X-Plex-Token=uxT7yvhM6M3GVfYG5Tsx&X-Plex-Container-Size=200
