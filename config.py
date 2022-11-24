from datetime import datetime
from settings import settings
from PlexAutoTorrentClasses import PatTvShow, PatUser, TvShowFollowType
import os


class config():
    #####
    PLEX_METADATA_URL = "https://metadata.provider.plex.tv/"
    PLEX_CONTAINER_SIZE = 200
    
    #####
    ENGINE_ID_SOURCE = "imdb"#
    ENGINE_EXTRA_EMPTY = "."



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
