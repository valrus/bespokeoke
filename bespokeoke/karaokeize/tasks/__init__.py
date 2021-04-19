#!/usr/bin/env python3

from .lexicons import (
    task_download_prosodylab_lexicon,
    task_download_librispeech_lexicon,
    task_combine_lexicons
)
from .separation import task_separate_audio
from .lyrics import task_download_lyrics
from .alignment import task_run_aligner
from .silence import task_find_silences
from .compress import task_compress_track
from .youtube import task_download_youtube_audio
from .karaokedokeize import task_karaokedokeize

from .video import task_create_video
