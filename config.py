from datetime import datetime
import os

class PlexATUser:
    username = ""
    password = ""
    servername = ""
    movie_engine_order = []
    movie_extra_order = []
    show_engine_order = []
    show_extra_order = []
    
    def __init__(self, p_username, p_password, p_servername, p_movie_engine_order, p_movie_extra_order, p_show_engine_order, p_show_extra_order):
        self.username = p_username
        self.password = p_password
        self.servername = p_servername
        self.movie_engine_order = p_movie_engine_order
        self.movie_extra_order = p_movie_extra_order
        self.show_engine_order = p_show_engine_order
        self.show_extra_order = p_show_extra_order



class config():
    TORRENT_FILE_PATH = "C:/torrents/PlexAutoTorrent/"
    QBITTORRENT_PATH = 'C:/Program Files/qbittorrent.exe'
    MOVIES_PATH = 'C:/Movies/'
    LOG_FILEPATH = os.path.dirname(os.path.realpath(__file__))+'/Logs/Log_'+datetime.utcnow().strftime('%Y%m%d')+'.txt'
    TELEGRAM_BOT_TOKEN = ""
    TELEGRAM_RAW_ID = ""
    
    PLEXUSERS = [PlexATUser("Username", "password", "Servername", ["torrentengine1", "torrentengine2", "all"],  ["2160p", "1080p", "720p", ""])]
