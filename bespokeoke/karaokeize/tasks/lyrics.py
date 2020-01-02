#!/usr/bin/env python3

import os

import lyricsgenius
import taglib

from .utils import make_task, lyrics_path


@make_task
def task_download_lyrics(input_path, output_path):

    def download_lyrics(targets):
        out_filename = targets[0]
        output_path.mkdir(parents=True, exist_ok=True)
        mp3 = taglib.File(str(input_path))

        tag_lyrics = mp3.tags.get('LYRICS', [''])[0].strip()

        if tag_lyrics:
            with open(out_filename, 'w', encoding='utf-8') as lyrics_file:
                print(*tag_lyrics.splitlines(), sep='\n', file=lyrics_file)
        else:
            genius = lyricsgenius.Genius(os.environ['GENIUS_ACCESS_TOKEN'])
            # Remove section headers (e.g. [Chorus]) from lyrics when searching
            genius.remove_section_headers = True
            song = genius.search_song(mp3.tags['TITLE'], mp3.tags['ARTIST'])
            with open(out_filename, 'w', encoding='utf-8') as lyrics_file:
                print(song.lyrics, file=lyrics_file)

    return {
        'actions': [(download_lyrics,)],
        'file_dep': [input_path],
        'targets': [lyrics_path(output_path)],
        'verbosity': 2
    }
