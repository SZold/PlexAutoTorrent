from datetime import datetime
from settings import settings
from PlexAutoTorrentClasses import QBittorrentStates
import os


class config():
    #####
    PLEX_METADATA_URL = "https://metadata.provider.plex.tv/"
    PLEX_CONTAINER_SIZE = 200
    
    #####
    ENGINE_ID_SOURCE = "imdb"#
    ENGINE_EXTRA_EMPTY = "."


    #:■◼▢⬕▢⏹■◧⏹◻□:⬛⬜◼️⏸️|▬▬▭▭|◼◼◻◻|▰▰▱▱|▂▂|═══|═━──┄┈|24%█▮▯:::╞═▰════════╡ 20%▰▱20%■▢▢▢▢▢▢▢▢▢ 10% 10% 10%
    PROGRESSBAR_WIDTH = 10
    PROGRESSBAR_START = ""   # "["
    PROGRESSBAR_STOP  = ""   # "]"
    PROGRESSBAR_WHOLE = "▰" # "█"
    PROGRESSBAR_BLANK = "─"  # " "
    PROGRESSBAR_STEP_CHARS = [] #[" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]    "▉▊▋▌▍▎▏ "
    PROGRESSBAR_V2 = ["⠀", "⠁", "⠃", "⠇", "⡇", "⡏", "⡟", "⡿"]

    ## https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#torrent-management
    # in formatting "{t}" = torrent object; "{progressbar} and {progressbarv2} are progressbars made with unicode charachters based on the PROGRESSBAR_ configurations"
    DOWNLOAD_PROGRESS_FORMAT = {}
    DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.downloading] = "⬇️{t.progress:.0%}"
    DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.allocating] = "🔃{t.progress:.0%}"
    DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.checkingDL] = "🔄{t.progress:.0%}"
    DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.checkingResumeData] = "🔄{t.progress:.0%}"
    DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.metaDL] = "⏬{t.progress:.0%}"
    DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.moving] = "➡️{t.progress:.0%}"
    
    DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.pausedDL] = "⏸️{t.progress:.0%}"
    DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.queuedDL] = "⏯️{t.progress:.0%}"
    DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.stalledDL] = "⏹️{t.progress:.0%}"
    DOWNLOAD_PROGRESS_FORMAT[QBittorrentStates.error] = "🛑{t.progress:.0%}"

    QBITTORRENT_PLEXAUTOTORRENT_TAG = "PlexAutoTorrent"
    QBITTORRENT_COMPLETE_TAG = "PlexAutoTorrentCompleted"
    QBITTORRENT_PLEXID_TAG = "plexid_{plexid}"

    CHECK_DESCRIPTION_FOR_GUIDS = False 
    SKIP_SPECIALS = True 

    MEDIA_LABEL_SKIP = "PlexAutoTorrent__Skip"
    MEDIA_LABEL_SHOW_BATCH = "PlexAutoTorrent__TvShow_FollowBatch"
    MEDIA_LABEL_SHOW_NEXT_SEASON = "PlexAutoTorrent__TvShow_FollowNextSeason"
    MEDIA_LABEL_EVERY_EPISODE = "PlexAutoTorrent__TvShow_FollowEveryEpisode"
    MEDIA_LABEL_SHOW_EPISODES_TO_DOWNLOAD = "PlexAutoTorrent__TvShow_Episodes_To_Download"# Example: "config.MEDIA_LABEL_SHOW_EPISODES_TO_DOWNLOAD=10"
    MEDIA_LABEL_TRIGGER = "PlexAutoTorrent__TvShow_Trigger"# Example: "config.PlexAutoTorrent__TvShow_Trigger=5"
    MEDIA_LABEL_ENGINE = "PlexAutoTorrent__TvShow_Engine"# Example: "config.PlexAutoTorrent__TvShow_Engine=ncorehu"
    MEDIA_LABEL_EXTRA = "PlexAutoTorrent__TvShow_Extra"# Example: "config.PlexAutoTorrent__TvShow_Extra=2160p"
    MEDIA_LABEL_IMDB = "PlexAutoTorrent__IMDB"# Example: "config.PlexAutoTorrent__IMDB=tt23752726"
    MEDIA_LABEL_SHOW__FORCE = "PlexAutoTorrent__TvShow_FORCE" #Override the episode list of PlexMetadata, force try next episodes based on season and episode number
