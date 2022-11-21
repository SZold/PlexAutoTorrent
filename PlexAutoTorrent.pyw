from collections import defaultdict
from datetime import datetime
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

_TORRENT_FILE_PATH = config.TORRENT_FILE_PATH
_QBITTORRENT_PATH = config.QBITTORRENT_PATH
_MOVIES_PATH = config.MOVIES_PATH
_LOG_FILEPATH = os.path.dirname(os.path.realpath(__file__))+'/Logs/Log_'+datetime.utcnow().strftime('%Y%m%d')+'.txt'
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

engine_order = ["ncorehu", "ncoreen", "all"]
extra_order = ["2160p", "1080p", "720p", ""]

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
                    TELEGRAM_REPORT["movies"].append("Added torrent: "+movie.title+" " + str(movie.year) +", "+res)
            else:
                doLog(foundEngine+ ", "+movie.title + " " + str(movie.year) +", " + movie.type+ ", "+imdb.id+":::  Not Found! ")
                DEBUG_COUNT['notFound'] = DEBUG_COUNT['notFound'] + 1 
        else:            
            doLogDebug("OnPlex, "+movie.title + " "+str(movie.year)+ ", " + movie.type+ ", "+imdb.id+":::  Found On Plex!! ")
            DEBUG_COUNT['OnPlex'] = DEBUG_COUNT['OnPlex'] + 1 
                
        #doLog("\n\n")

def doShows(showList, plexConnection, plexuser):
    for show in showList:
        global DEBUG_COUNT
        tvdb = list(filter(lambda guid: guid.id.startswith("tvdb:"), show.guids))[0]
        showOnPlex = plexConnection.library.search(guid=show.guid, libtype=show.type)
        currEpisode = 0
        currSeason = 1
        nextSeason = 1
        result = None

        if len(showOnPlex) > 0:    
            showOnPlex = showOnPlex[0]
            currEpisode = showOnPlex.episodes()[-1].episodeNumber
            currSeason = showOnPlex.episodes()[-1].seasonNumber
            nextSeason = currSeason+1
        else:
            showOnPlex = show

        result = searchShowNext(plexuser, showOnPlex, "S"+f'{currSeason:02}'+"E"+f'{(currEpisode+1):02}')   #Search for next episode
        if result == None:
            result = searchShowNext(plexuser, showOnPlex, "S"+f'{(currSeason+1):02}'+"E01") #Search for next season first episode
        if result == None:
            result = searchShowNext(plexuser, showOnPlex, "S"+f'{(nextSeason):02}') # search for whole next season
        if result == None:
            result = searchShowNext(plexuser, showOnPlex, str(show.year)) # search for whole shpw

        if result == None:            
            doLogDebug("Next Episode Not Found, "+show.title + " "+str(show.year) + ", "+tvdb.id+"::: ")
            #ep = searchShowNext()

        else:            
            doLogDebug("Next Episode/Season Found, "+ result[1] + " "+ result[-1] + ", "+tvdb.id+"::: ")
            DEBUG_COUNT['OnPlex'] = DEBUG_COUNT['OnPlex'] + 1 

def searchShowNext(plexuser, show, str):
    doLogDebug("searchShowNext, "+show.title+": "+str + "::: ")
    foundObj = None
    tvdb = list(filter(lambda guid: guid.id.startswith("tvdb:"), show.guids))[0]
    for engine in plexuser.show_engine_order:
        for extra in plexuser.show_extra_order:
            if foundObj is None:
                url_title = re.sub(r'[\W_]+', ' ', show.title) + " " + str + " " + extra                    
                url_title = url_title.strip();

                torrent_path = _TORRENT_FILE_PATH+show.type+"/"+re.sub(r'[\W_]+', '', tvdb.id)+"_"+engine+"_" + url_title +""                    
                
                #doLog(movie.title + ", "+ url_title + ", " + movie.type+", "+engine+", "+ str(movie.year)+ ", "+imdb.id)                        
                os.chdir(os.path.dirname(SCRIPT_PATH))
                proc = subprocess.run( ['pyw', 'nova2.py',  engine, CAT_CONVERT[show.type], url_title], capture_output=True)
                results = proc.stdout.decode().split("\n")   
                resultArr = results[0].split("|")
                if len(resultArr) > 1:
                    foundObj = resultArr
                    foundEngine = engine
                else:
                    resultArr = ["","","","","","","","","",""]
    return foundObj


def main(args):
    doLogDebug("Running PlexAutoTorrent "+json.dumps(args)+":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")    
    global DEBUG_COUNT
    global _DO_LOG
    _DO_LOG = True if(args["logging"]) else False
    global _DO_DRYRUN
    _DO_DRYRUN = True if(args["dryrun"]) else False

    for plexuser in config.PLEXUSERS:
        DEBUG_COUNT['users'] = DEBUG_COUNT['users'] + 1
        doLogDebug("plexuser: "+ plexuser.username )
        account = MyPlexAccount(plexuser.username, plexuser.password)
        plex = account.resource(plexuser.servername).connect()  # returns a PlexServer instance 

        if not args["skipmovies"]:
             doLogDebug("movies: "+ plexuser.username )
             doMovies(account.watchlist(filter='released', sort='rating:desc', libtype='movie'), plex, plexuser)
            
        if not args["shipshows"]:
            doLogDebug("shows: "+ plexuser.username )
            #doShows(account.watchlist(filter='released', sort='rating:desc', libtype='show'), plex, plexuser)

    if(args["telegramreport"]):
        sendTelegramReport(json.dumps(TELEGRAM_REPORT)+" \n "+json.dumps(DEBUG_COUNT))

    doLog("telegramreport ::("+json.dumps(TELEGRAM_REPORT)+")")
    doLog("PlexAutoTorrent ::("+json.dumps(DEBUG_COUNT)+"):::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")

def sendTelegramReport(report):
    if(DEBUG_COUNT["torrentDownloaded"]+DEBUG_COUNT["magnetDownloaded"] > 0):
        token = config.TELEGRAM_BOT_TOKEN
        url = f"https://api.telegram.org/bot{token}"
        # keyboard = {
        #     "inline_keyboard": [
        #         [
        #             {"text": "Allow", "callback_data": "allow"},
        #             {"text": "Deny", "callback_data": "deny"}
        #         ]
        #     ]
        # }

        params = {"chat_id": config.TELEGRAM_RAW_ID, 
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

    

        #https://metadata.provider.plex.tv/library/sections/watchlist?X-Plex-Token=uxT7yvhM6M3GVfYG5Tsx
        #https://metadata.provider.plex.tv/library/metadata/5d9c084fec357c001f9ab4d8/children?X-Plex-Token=uxT7yvhM6M3GVfYG5Tsx
        #https://metadata.provider.plex.tv/library/metadata/5d9c0a8e02391c001f5a0e98/children?X-Plex-Token=uxT7yvhM6M3GVfYG5Tsx
        #https://metadata.provider.plex.tv/library/metadata/5d9c09b32192ba001f3210a2/children?X-Plex-Token=uxT7yvhM6M3GVfYG5Tsx
        #https://metadata.provider.plex.tv/library/metadata/602e649867f4c8002ce3a62d/children?X-Plex-Token=uxT7yvhM6M3GVfYG5Tsx&X-Plex-Container-Size=200
