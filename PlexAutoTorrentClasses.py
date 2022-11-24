from enum import Enum

class TvShowFollowType(Enum):
    NextSeason = 1
    Batch = 2
    All = 3

class Engine:
    id = ""
    extraGUID = ""
    seasonNumberFormatList = []
    episodeNumberFormatList = []
    def __init__(self, id, extraGUID="", episodeNumberFormatList=["S{S:02}E{E:02}"], seasonNumberFormatList=["S{S:02}"]):
        self.id = id
        self.extraGUID = extraGUID
        self.episodeNumberFormatList = episodeNumberFormatList
        self.seasonNumberFormatList = seasonNumberFormatList

class PatUser:
    username = ""
    password = ""
    servername = ""
    movie_engine_order = []
    movie_extra_order = []
    show_engine_order = []
    show_extra_order = []
    account = None
    
    def __init__(self, username, password, servername, 
                       movie_engine_order=[], movie_extra_order=[], 
                       show_engine_order=[], show_extra_order=[]):
        self.username = username
        self.password = password
        self.servername = servername
        self.movie_engine_order = movie_engine_order
        self.movie_extra_order = movie_extra_order
        self.show_engine_order = show_engine_order
        self.show_extra_order = show_extra_order

class PatTvShow:
    show = None
    imdb = ''
    title = None
    episode_to_download = 0
    follow_type = TvShowFollowType.NextSeason
    engines = []
    extras = []
    force = False
    skip = False
    unwatched_episode_trigger = 0

    def __init__(self, show=None, title="", episode_to_download=0, engines=[], extras=[], force=False, unwatched_episode_trigger = 0, follow_type = TvShowFollowType.NextSeason):
        self.title = title
        self.episode_to_download = episode_to_download
        self.show = show
        self.engines = engines
        self.extras = extras
        self.force = force
        self.unwatched_episode_trigger = unwatched_episode_trigger
        self.follow_type = follow_type

