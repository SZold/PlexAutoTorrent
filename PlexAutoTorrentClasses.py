from enum import Enum
import abc
import math
import shutil
import sys
import time

from typing import TextIO

class TvShowFollowType(Enum):
    NextSeason = 1
    Batch = 2
    All = 3

class QBittorrentStates(Enum):
    default =  0	 	#Some error occurred, applies to paused torrents
    error =  1	 	#Some error occurred, applies to paused torrents
    missingFiles = 2	 	#Torrent data files is missing
    uploading = 3	 	#Torrent is being seeded and data is being transferred
    pausedUP = 4	 	#Torrent is paused and has finished downloading
    queuedUP = 5	 	#Queuing is enabled and torrent is queued for upload
    stalledUP = 6	 	#Torrent is being seeded, but no connection were made
    checkingUP = 7	 	#Torrent has finished downloading and is being checked
    forcedUP = 8	 	#Torrent is forced to uploading and ignore queue limit
    allocating = 9	 	#Torrent is allocating disk space for download
    downloading = 10	 	#Torrent is being downloaded and data is being transferred
    metaDL = 11	 	#Torrent has just started downloading and is fetching metadata
    pausedDL = 12	 	#Torrent is paused and has NOT finished downloading
    queuedDL = 13	 	#Queuing is enabled and torrent is queued for download
    stalledDL = 14	 	#Torrent is being downloaded, but no connection were made
    checkingDL = 15	 	#Same as checkingUP, but torrent has NOT finished downloading
    forcedDL = 16	 	#Torrent is forced to downloading to ignore queue limit
    checkingResumeData = 17	 	#Checking resume data on qBt startup
    moving = 18	 	#Torrent is moving to another location
    unknown = 19	 	#Unknown status

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


"""
Produce progress bar with ANSI code output.
"""
class ProgressBar(object):
    def __init__(self, target: TextIO = sys.stdout):
        self._target = target
        self._text_only = not self._target.isatty()
        self._update_width()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if(exc_type is None):
            # Set to 100% for neatness, if no exception is thrown
            self.update(1.0)
        if not self._text_only:
            # ANSI-output should be rounded off with a newline
            self._target.write('\n')
        self._target.flush()
        pass

    def _update_width(self):
        self._width, _ = shutil.get_terminal_size((80, 20))

    def update(self, progress : float):
        # Update width in case of resize
        self._update_width()
        # Progress bar itself
        if self._width < 12:
            # No label in excessively small terminal
            percent_str = ''
            progress_bar_str = ProgressBar.progress_bar_str(progress, self._width - 2)
        elif self._width < 40:
            # No padding at smaller size
            percent_str = "{:6.2f} %".format(progress * 100)
            progress_bar_str = ProgressBar.progress_bar_str(progress, self._width - 11) + ' '
        else:
            # Standard progress bar with padding and label
            percent_str = "{:6.2f} %".format(progress * 100) + "  "
            progress_bar_str = " " * 5 + ProgressBar.progress_bar_str(progress, self._width - 21)
        # Write output
        if self._text_only:
            self._target.write(progress_bar_str + percent_str + '\n')
            self._target.flush()
        else:
            self._target.write('\033[G' + progress_bar_str + percent_str)
            self._target.flush()

    @staticmethod
    def progress_bar_str(progress : float, width : int, startChar = "[", endChar = "]", wholeChar = "█", blankChar = "-", partCharList = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]):
        # 0 <= progress <= 1
        progress = min(1, max(0, progress))
        whole_width = math.floor(progress * width)
        remainder_width = (progress * width) % 1
        part_char = ""
        if(len(partCharList) > 0):
            part_width = math.floor(remainder_width * len(partCharList))
            part_char = partCharList[part_width]
            if (width - whole_width - 1) < 0:
                part_char = ""
        line = startChar + wholeChar * whole_width + part_char + blankChar * (width - whole_width - 1) + endChar
        return line

    @staticmethod
    def progress_bar_str_v2(progress : float, width : int, partCharList = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]):
        # 0 <= progress <= 1
        progress = min(1, max(0, progress))
        whole_width = math.floor(progress * width)
        remainder_width = (progress * width) % 1
        part_char = ""
        if(len(partCharList) > 0):
            part_width = math.floor(progress * len(partCharList))
            part_char = partCharList[part_width]
            if (width - whole_width - 1) < 0:
                part_char = ""
        return part_char