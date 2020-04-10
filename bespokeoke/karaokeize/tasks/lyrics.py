#!/usr/bin/env python3

import os
import re

import lyricsgenius
import taglib

from .utils import make_task, lyrics_path


# match lines
SKIPPABLE_LINE_RE = re.compile(r'^[\[(].*?[\])]$')


@make_task
def task_download_lyrics(input_path, output_path):

    def skippable_line(line):
        return SKIPPABLE_LINE_RE.match(line)

    def download_lyrics(targets):
        out_filename = targets[0]
        output_path.mkdir(parents=True, exist_ok=True)
        mp3 = taglib.File(str(input_path))

        tag_lyrics = mp3.tags.get('LYRICS', [''])[0].strip()

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
        else:
            genius = lyricsgenius.Genius(os.environ['GENIUS_ACCESS_TOKEN'])
            # Remove section headers (e.g. [Chorus]) from lyrics when searching
            genius.remove_section_headers = True
            # TODO: Remove other annotation-y stuff as well
            song = genius.search_song(mp3.tags['TITLE'], mp3.tags['ARTIST'])
            with open(out_filename, 'w', encoding='utf-8') as lyrics_file:
                print(song.lyrics, file=lyrics_file)

    return {
        'actions': [(download_lyrics,)],
        'file_dep': [input_path],
        'targets': [lyrics_path(output_path)],
        'verbosity': 2
    }
