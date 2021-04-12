#!/usr/bin/env python3

import logging

import mutagen
import youtube_dl

from .utils import make_task, working_dir


def download_from_youtube(youtube_url, output_path):
    if not youtube_url:
        return

    youtube_dl_opts = {
        'format': 'bestaudio/best',
        # note: you need to have the ext here to ensure the output file
        # has the correct mp3 headers!
        'outtmpl': f'{output_path.stem}.%(ext)s',
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            { 'key': 'FFmpegMetadata' },
        ],
        'logger': logging.getLogger(),
        # 'progress_hooks': [my_hook],
    }

    with working_dir(output_path.parent):
        with youtube_dl.YoutubeDL(youtube_dl_opts) as downloader:
            downloader.download([youtube_url])


def add_metadata(input_path, title, artist):
    if not (title or artist):
        return

    audiofile_ez = mutagen.File(str(input_path), easy=True)
    if title:
        audiofile_ez['title'] = title
    if artist:
        audiofile_ez['artist'] = artist
    audiofile_ez.save()


@make_task
def task_download_youtube_audio(youtube_url, output_path, title=None, artist=None):
    yield {
        'actions': [
            (download_from_youtube, [youtube_url, output_path]),
            (add_metadata, [output_path, title, artist]),
        ],
        'targets': [output_path],
        'uptodate': [True],
        'verbosity': 2
    }
