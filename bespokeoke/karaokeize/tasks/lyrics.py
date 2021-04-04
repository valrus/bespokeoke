#!/usr/bin/env python3

import os
import re

import lyricsgenius
import mutagen

from .utils import make_task, lyrics_path

try:
    from ..genius_token import GENIUS_ACCESS_TOKEN
except ImportError:
    GENIUS_ACCESS_TOKEN = os.environ.get('GENIUS_ACCESS_TOKEN')


# match lines
SKIPPABLE_LINE_RE = re.compile(r'^[\[(].*?[\])]$')

LYRICS_TAG_KEYS = {
    'MP4': '\xa9lyr',
    'MP3': 'USLT'
}

@make_task
def task_download_lyrics(input_path, output_path):

    def skippable_line(line):
        return SKIPPABLE_LINE_RE.match(line)

    def download_lyrics(targets):
        out_filename = targets[0]
        output_path.mkdir(parents=True, exist_ok=True)
        audiofile = mutagen.File(str(input_path))
        tag_lyrics = audiofile.tags.get(LYRICS_TAG_KEYS[audiofile.__class__.__name__])

        if tag_lyrics:
            with open(out_filename, 'w', encoding='utf-8') as lyrics_file:
                print(
                    *[
                        stripped_line for stripped_line in
                        (line.strip() for line in tag_lyrics.splitlines())
                        if not skippable_line(stripped_line)
                    ],
                    sep='\n', file=lyrics_file
                )
        elif GENIUS_ACCESS_TOKEN:
            audiofile_ez = mutagen.File(str(input_path), easy=True)
            genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)
            # Remove section headers (e.g. [Chorus]) from lyrics when searching
            genius.remove_section_headers = True
            # TODO: Remove other annotation-y stuff as well
            song = genius.search_song(audiofile_ez['title'][0], audiofile_ez['artist'][0])
            with open(out_filename, 'w', encoding='utf-8') as lyrics_file:
                print(song.lyrics, file=lyrics_file)
        else:
            raise ValueError("No GENIUS_ACCESS_TOKEN, can't download lyrics")

    yield {
        'actions': [(download_lyrics,)],
        'file_dep': [input_path],
        'targets': [lyrics_path(output_path)],
        'verbosity': 2
    }
