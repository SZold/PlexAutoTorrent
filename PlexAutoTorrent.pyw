from collections import defaultdict
from datetime import datetime
import traceback
from PlexAutoTorrentClasses import Engine, PatTvShow, TvShowFollowType
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
_SHOWS_PATH = settings.SHOWS_PATH
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
                    #doLog(foundEngine+ ", "+foundObj[1] + ", " + movie.type+ ", "+imdb+":::  "+torrent[0]) "--skip-dialog", "true",
    return result

def doTorrentSearch(engine, title, category, extraData):
    if extraData == "":
        extraData = config.ENGINE_EXTRA_EMPTY
    proc = subprocess.run( ['pyw', 'nova2.py',  engine, category, extraData, title], capture_output=True)
    return proc

def toPlainStr(str):
    url_title = re.sub(r'[\W_]+', ' ', str)                     
    return url_title.strip();

def doMovies(movieList, plexConnection, plexuser):
    for movie in movieList:
        global DEBUG_COUNT
        DEBUG_COUNT['movie'] = DEBUG_COUNT['movie'] + 1
        imdb = list(filter(lambda guid: guid.id.startswith("imdb:"), movie.guids))        
        if(len(imdb) > 0):
            imdb = imdb[0].id.replace('imdb://', '')
        else:
            imdb = config.ENGINE_EXTRA_EMPTY

        url_title = re.sub(r'[\W_]+', ' ', movie.title) + " " + str(movie.year) 
        torrent_path =  _TORRENT_FILE_PATH+"/"+movie.type+"/"+re.sub(r'[\W_]+', '', imdb)+"_" + url_title +""

        movieOnPlex = plexConnection.library.search(guid=movie.guid, libtype=movie.type)

        if len(movieOnPlex) == 0:
            foundObj = None
            foundEngine = "--"
            for engine in plexuser.movie_engine_order:
                for extra in plexuser.movie_extra_order:
                    if foundObj is None:
                        torrent_path = _TORRENT_FILE_PATH+movie.type+"/"+re.sub(r'[\W_]+', '', imdb)+"_"+engine.id+"_" + url_title +""                    
                        
                        url_title = toPlainStr(movie.title)   
                        if(imdb == config.ENGINE_EXTRA_EMPTY):   
                            url_title = url_title + " " + str(movie.year)  
                        url_title = url_title + " " + extra  

                        #doLog(movie.title + ", "+ url_title + ", " + movie.type+", "+engine.id+", "+ str(movie.year)+ ", "+imdb)                        
                        os.chdir(os.path.dirname(SCRIPT_PATH))                        
                        #proc = subprocess.run( ['pyw', 'nova2.py',  engine, CAT_CONVERT[movie.type], url_title], capture_output=True)
                        proc = doTorrentSearch(engine.id, url_title.replace(" ", "."), CAT_CONVERT[movie.type], imdb)
                        results = proc.stdout.decode().split("\n")   
                        resultArr = results[0].split("|")
                        #TODO: Check For extras here instead of new query for each
                        if len(resultArr) > 1:
                            foundObj = resultArr
                            foundEngine = engine.id
                        else:
                            resultArr = ["","","","","","","","","",""]
            
            if foundObj is not None: 
                res = doDownloadTorrent(foundObj, torrent_path, _MOVIES_PATH+url_title)                
                if res is not None:                    
                    TELEGRAM_REPORT["movies"].append({"user": plexuser.username, "title": movie.title, "year": movie.year, "torrentpath": res})
            else:
                doLog(foundEngine+ ", "+movie.title + " " + str(movie.year) +", " + movie.type+ ", "+imdb+":::  Not Found! ")
                DEBUG_COUNT['notFound'] = DEBUG_COUNT['notFound'] + 1 
        else:            
            doLogDebug("OnPlex, "+movie.title + " "+str(movie.year)+ ", " + movie.type+ ", "+imdb+":::  Found On Plex!! ")
            DEBUG_COUNT['OnPlex'] = DEBUG_COUNT['OnPlex'] + 1 
                
        #doLog("\n\n")

def getTvShowConfigs(show, plexuser):
    result = PatTvShow( show=show,      
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
        elif label.tag == config.MEDIA_LABEL_SKIP:
            result.skip = True
        elif label.tag.startswith(config.MEDIA_LABEL_IMDB+"="):
            lb = label.tag.split("=")
            result.imdb = lb[1]
        elif label.tag.startswith(config.MEDIA_LABEL_SHOW_EPISODES_TO_DOWNLOAD+"="):
            lb = label.tag.split("=")
            result.episode_to_download = lb[1]
        elif label.tag.startswith(config.MEDIA_LABEL_TRIGGER+"="):
            lb = label.tag.split("=")
            result.unwatched_episode_trigger = lb[1]
        elif label.tag.startswith(config.MEDIA_LABEL_ENGINE+"="):
            lb = label.tag.split("=")
            result.engines.append(Engine(lb[1]))
        elif label.tag.startswith(config.MEDIA_LABEL_EXTRA+"="):
            lb = label.tag.split("=")
            result.extras.append(lb[1])
    if(len(result.engines) == 0):
        result.engines = plexuser.show_engine_order
    if(len(result.extras) == 0):
        result.extras = plexuser.show_extra_order
        
    return result

def getShowEpisodeList(showList, plexConnection, plexuser):
    result = []
    if(settings.FOLLOW_EVERY_SHOW_IN_LIBRARY):
        showList = []
        for showInLib in settings.TV_SHOW_LIBRARIES:
            showList += plexConnection.library.section(showInLib).search("")
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
        if(tvshowConfig.imdb == ''):
            tvshowConfig.imdb = list(filter(lambda guid: guid.id.startswith("imdb:"), show.guids))        
            if(len(tvshowConfig.imdb) > 0):
                tvshowConfig.imdb = tvshowConfig.imdb[0].id.replace('imdb://', '') 
            else:
                tvshowConfig.imdb = config.ENGINE_EXTRA_EMPTY
                tvshowConfig.skip = True
        
        isShowOnPlexMetadata = False
        try:
            metadataEpisodeList = getPlexMetadataEpisodeList(plexuser, show)
            isShowOnPlexMetadata = True
        except:
            isShowOnPlexMetadata = False            
            if(not settings.FOLLOW_EVERY_SHOW_IN_LIBRARY):
                tvshowConfig.force = True
            else:
                tvshowConfig.skip = True
            metadataEpisodeList = []
            
        unwatchedList = list(filter(lambda ep: not ep.isPlayed, collectedEpisodeList))
        unwatchedCount = len(unwatchedList)
            
        if isShowOnPlexMetadata:
            nonCollectedSeasonEpisodeList = list(filter(lambda ep: {"s": ep.seasonNumber, "e": ep.episodeNumber} not in collectedSeasonEpisodeList, metadataEpisodeList))
        else:
            nonCollectedSeasonEpisodeList = []

        episodeToDownload = getNextEpisodesList(tvshowConfig, collectedSeasonEpisodeList, list(map(lambda ep: {"s": ep.seasonNumber, "e": ep.episodeNumber}, nonCollectedSeasonEpisodeList)))
        if(tvshowConfig.skip):
            a = ""
            #doLogDebug("SKIP ::"+showOnWatchList.title+"(metadata:"+str(isShowOnPlexMetadata)+") is skipped"+ " :: ")
        elif(not tvshowConfig.skip and (unwatchedCount < tvshowConfig.unwatched_episode_trigger) and (len(episodeToDownload) > 0)):
            a = ""
            doLog("DO   ::"+showOnWatchList.title+": "+ str(unwatchedCount)+ ' || '+ str(len(nonCollectedSeasonEpisodeList)) + " < "+str(tvshowConfig.unwatched_episode_trigger)+" :: "+json.dumps(episodeToDownload)+ " :: "+json.dumps(list(map(lambda en: en.id, tvshowConfig.engines))))
            result.append({"tvshowConfig": tvshowConfig, "episodeToDownload": episodeToDownload})
        elif(not tvshowConfig.skip and tvshowConfig.force):
            a = ""
            doLog("FORCE::"+showOnWatchList.title+"(metadata:"+str(isShowOnPlexMetadata)+") is forced download"+ " :: "+json.dumps(list(map(lambda en: en.id, tvshowConfig.engines))))
            result.append({"tvshowConfig": tvshowConfig, "episodeToDownload": episodeToDownload})
        else:
            a = ""
            #doLogDebug("NOT  ::"+showOnWatchList.title+": "+ str(unwatchedCount)+ ' && '+ str(len(nonCollectedSeasonEpisodeList)) + " >= "+str(tvshowConfig.unwatched_episode_trigger)+" :: "+str(len(episodeToDownload)))
        
    return result

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
        result = result[0: tvshowConfig.episode_to_download]

    return result

def getPlexMetadataEpisodeList(plexuser, show):
    result = []
    params = {}
    #params['X-Plex-Token'] = plexuser.account._token
    params['X-Plex-Container-Start'] = 0
    params['X-Plex-Container-Size'] = config.PLEX_CONTAINER_SIZE

    if(show.guid.startswith("plex://show/")):
        try:
            showGUID = show.guid.split("/")[-1]
            sURL = f'{plexuser.account.METADATA}/library/metadata/{showGUID}/children'
            mdShowXML =  plexuser.account.query(sURL, params=params)
        except Exception:
            doLog(f'ERROR: metadata not found for show {show.title} ({sURL})')
        
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


def doSearhShowEpisodes(showList):
    torrentList = []
    for showToSearch in showList:    
        try:
            showToSearch["torrent"] = []
            conf = showToSearch["tvshowConfig"]
            show = conf.show
            epList = showToSearch["episodeToDownload"] 
            imdb = conf.imdb
            seasonList = []
            for ep in epList:  
                if ep["s"] not in seasonList:
                    seasonList.append(ep["s"])

            url_title = ""        
            episodeFormatted = ""
            for se in seasonList:
                seasonFound = False 
                for engine in conf.engines:   
                    if not seasonFound:  
                        for extra in conf.extras:  
                            if not seasonFound:                                
                                for format in engine.seasonNumberFormatList:  
                                    if not seasonFound: 
                                        seasonFormatted = format.format(S = se)
                                        url_title = (toPlainStr(show.title)+" "+ seasonFormatted  + " " + extra)                                        
                                        proc = doTorrentSearch(engine.id, url_title.replace(" ", "."), CAT_CONVERT[show.type], imdb)  
                                        results = proc.stdout.decode().split("\n")   
                                        resultArr = results[0].split("|")
                                        #TODO: Check For extras here instead of new query for each
                                        if len(resultArr) > 1:
                                            if(extra == ''):
                                                extra = 'Unknown'
                                            seasonFound = True
                                            torrentList.append(
                                                {"show": show,
                                                 "imdb": imdb,
                                                 "extra": extra,
                                                 "seasonEpisode": {"s": se},
                                                 "torrent": resultArr, 
                                                 "folder":  toPlainStr(show.title)+" ("+toPlainStr(imdb)+")/"+("Season {S:01}".format(S = se)+"/"+extra)}
                                            )      
                if(seasonFound):
                    doLog("seFound     :"+url_title+" "+episodeFormatted+" ("+imdb+"): "+json.dumps(torrentList[-1]["torrent"])+"")    
                else:
                    url_title = ""        
                    episodeFormatted = "" 
                    for ep in list(filter(lambda e: e["s"]==se, epList)):  
                        episodeFound = False  
                        for engine in conf.engines:   
                            if not episodeFound:  
                                for extra in conf.extras:  
                                    if not episodeFound:
                                        for format in engine.episodeNumberFormatList:  
                                            if not episodeFound:
                                                episodeFormatted = format.format(S = ep["s"], E = ep["e"])
                                                url_title = (toPlainStr(show.title)+" "+ episodeFormatted  + " " + extra)
                                                proc = doTorrentSearch(engine.id, url_title.replace(" ", "."), CAT_CONVERT[show.type], imdb)      
                                                results = proc.stdout.decode().split("\n")   
                                                resultArr = results[0].split("|")
                                                #TODO: Check For extras here instead of new query for each
                                                if len(resultArr) > 1:
                                                    if(extra == ''):
                                                        extra = 'Unknown'
                                                    episodeFound = True
                                                    showToSearch["torrent"].append({"torrent": resultArr, 
                                                                                    }) 
                                                    torrentList.append(
                                                        {"show": show,
                                                        "imdb": imdb,
                                                        "extra": extra,
                                                        "seasonEpisode": ep,
                                                        "torrent": resultArr, 
                                                        "folder": toPlainStr(show.title)+" ("+toPlainStr(imdb)+")/"+("Season {S:01}".format(S = se))+"/"+("S{S:02}E{E:02}").format(S = ep["s"], E = ep["e"])+"/"+extra
                                                        }
                                                    ) 
                        if(episodeFound):
                            doLog("epFound     :"+url_title+" "+episodeFormatted+" ("+imdb+"): "+json.dumps(torrentList[-1]["torrent"])+"")    
                        #else:
                        #    doLogDebug("Not Found :"+url_title+" "+episodeFormatted+" ("+imdb+"): ")   
        except:
            doLog("Error     :"+traceback.format_exc())
    return torrentList


def main(args):
    try:
        doLogDebug("Running PlexAutoTorrent "+json.dumps(args)+":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")    
        global DEBUG_COUNT
        global _DO_LOG
        _DO_LOG = True if(args["logging"]) else False
        global _DO_DRYRUN
        _DO_DRYRUN = True if(args["dryrun"]) else False

        showEpisodeList = []
        for plexuser in settings.PLEXUSERS:
            DEBUG_COUNT['users'] = DEBUG_COUNT['users'] + 1
            doLogDebug("plexuser: "+ plexuser.username )
            plexuser.account = MyPlexAccount(plexuser.username, plexuser.password)
            plex = plexuser.account.resource(plexuser.servername).connect()  # returns a PlexServer instance 

            if not args["skipmovies"]:
                doLogDebug("movies: "+ plexuser.username )
                doMovies(plexuser.account.watchlist(filter='released', sort='rating:desc', libtype='movie'), plex, plexuser)
                
            if not args["skipshows"]:
                doLogDebug("shows: "+ plexuser.username )
                showEpisode = getShowEpisodeList(plexuser.account.watchlist(filter='released', sort='rating:desc', libtype='show'), plex, plexuser)
                if(showEpisode is not None):
                    showEpisodeList += showEpisode

        torrentList = doSearhShowEpisodes(showEpisodeList)

        for torrent in torrentList:
            url_title = toPlainStr(torrent["show"].title)
            se = ("S{S:02}").format(S = torrent["seasonEpisode"]["s"])
            if("e" in torrent["seasonEpisode"]):
                se = se + ("E{E:02}").format(E = torrent["seasonEpisode"]["e"])
            torrent_path = _TORRENT_FILE_PATH+torrent["show"].type+"/"+ url_title +" ("+toPlainStr(torrent["imdb"])+")/"+url_title+"_"+se+"_"+torrent["extra"]
            save_path = _SHOWS_PATH + torrent["folder"]

            if not os.path.exists(torrent_path+"*"):
                res = doDownloadTorrent(torrent["torrent"], torrent_path, save_path)                
                if res is not None:                    
                    TELEGRAM_REPORT["shows"].append({"url_title": url_title, "seasonEpisode": torrent["seasonEpisode"]})
            

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

def merge_two_dicts(x, y):
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z

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
