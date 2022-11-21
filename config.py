from datetime import datetime
import os

class PlexATUser:
    username = ""
    password = ""
    servername = ""
    engine_order = []
    extra_order = []
    
    def __init__(self, p_username, p_password, p_servername, p_engine_order, p_extra_order):
        self.username = p_username
        self.password = p_password
        self.servername = p_servername
        self.engine_order = p_engine_order
        self.extra_order = p_extra_order



class PlexAutoTorrentConfig():
    TORRENT_FILE_PATH = "C:/torrents/PlexAutoTorrent/"
    QBITTORRENT_PATH = 'C:/Program Files/qbittorrent.exe'
    MOVIES_PATH = 'C:/Movies/'
    LOG_FILEPATH = os.path.dirname(os.path.realpath(__file__))+'/Logs/Log_'+datetime.utcnow().strftime('%Y%m%d')+'.txt'
    
    PLEXUSERS = [PlexATUser("Username", "password", "Servername", ["torrentengine1", "torrentengine2", "all"],  ["2160p", "1080p", "720p", ""])]
