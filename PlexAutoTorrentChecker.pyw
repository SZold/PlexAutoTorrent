from collections import defaultdict
from datetime import datetime
import json
import os
import traceback
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

def main(args):
    try:
        doLogDebug("Running PlexAutoTorrentChecker "+json.dumps(args)+":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")    
        global DEBUG_COUNT
        global _DO_LOG
        _DO_LOG = True if(args["logging"]) else False
        global _DO_DRYRUN
        _DO_DRYRUN = True if(args["dryrun"]) else False

        qbt_client = qbittorrentapi.Client(host='localhost', port=8080,username='admin',password='adminadmin',)
        
        try:
            qbt_client.auth_log_in()
        except qbittorrentapi.LoginFailed as e:
            print(e)
        
        print(f'qBittorrent: {qbt_client.app.version}')
        print(f'qBittorrent Web API: {qbt_client.app.web_api_version}')
            
        doLog("PlexAutoTorrentChecker ::("+json.dumps(DEBUG_COUNT)+"):::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")    
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
