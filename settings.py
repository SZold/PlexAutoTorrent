from datetime import datetime
from PlexAutoTorrentClasses import PatTvShow, PatUser, TvShowFollowType
import os


class settings():
    ##### FILEPATHs
    TORRENT_FILE_PATH = ""
    QBITTORRENT_PATH = ''
    MOVIES_PATH = ''
    SHOWS_PATH = ''
    LOG_FILEPATH = ''
    ##### TELEGRAM configs:
    TELEGRAM_BOT_TOKEN = ""
    TELEGRAM_RAW_ID = ""
    ##### QBITTORRENT configs:
    QBITTORRENT_HOST='localhost',
    QBITTORRENT_PORT=8080,
    QBITTORRENT_USER='admin',
    QBITTORRENT_PASS='adminadmin',
    ##### User configs:
    PLEXUSERS = [PatUser(username="plexuser", 
                         password="plexpass", 
                         servername="plexservername", 
                         movie_engine_order=["all"],  
                         movie_extra_order=["2160p", "1080p", "720p", ""], 
                         show_engine_order=["all"],  
                         show_extra_order=["1080p", "720p", ""])
    ]    

    #####
    TV_SHOW_LIBRARIES = ['TV Shows']
    FOLLOW_EVERY_SHOW_IN_LIBRARY = False #If True every show is going to be followed not just the ones in a user library; Default: False
    DEFAULT_TVSHOW_FOLLOWTYPE = TvShowFollowType.NextSeason # Default: TvShowFollowType.NextSeason
    DEFAULT_UNWATCHED_EPISODE_TRIGGER = 3 # Default: 3
    DEFAULT_EPISODES_TO_DOWNLOAD = 5 #How many episodes to download; -1 to download all episodes based on the follow_type # Default: 5
