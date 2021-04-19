#!/usr/bin/env python3

import json
import textwrap

from .utils import make_task, sync_map_path, video_path, silences_path


def _find_fragment_endpoints(fragment_begin, fragment_end, silences):
    for silence in silences:
        if silence['begin'] <= fragment_begin < silence['end']:
            fragment_begin = silence['end']
        if silence['begin'] <= fragment_end < silence['end']:
            fragment_end = silence['begin']
    return (fragment_begin / 1000.0), (fragment_end / 1000.0)


def _generate_lyric_clips(lyrics_map, silences):
    for fragment in lyrics_map['fragments']:
        lyric = textwrap.fill('\n'.join(fragment['lines']), 30)
        if not lyric:
            continue
        fragment_begin, fragment_end = _find_fragment_endpoints(
            float(fragment['begin']) * 1000,
            float(fragment['end']) * 1000,
            silences
        )
        if fragment_end - fragment_begin <= 0:
            continue
        lyric_clip = (
            TextClip(txt=lyric, size=(800, 600), color='white', font='Courier-Bold').
            set_start(fragment_begin).
            set_duration(fragment_end - fragment_begin).
            set_pos(('center', 'center'))
        )
        yield lyric_clip


@make_task
def task_create_video(input_path, output_dir_path):
    try:
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        from moviepy.video.VideoClip import ColorClip, TextClip
        from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

        def create_video(dependencies, targets):
            backing_track_path = output_dir_path / 'accompaniment.wav'
            with open(sync_map_path(output_dir_path), encoding='utf-8') as sync_json_file, \
                open(silences_path(output_dir_path), encoding='utf-8') as silence_json_file:
                lyric_clips = list(
                    _generate_lyric_clips(
                        json.load(sync_json_file),
                        json.load(silence_json_file)
                    )
                )
            backing_track_clip = AudioFileClip(str(backing_track_path))
            background_clip = ColorClip(
                size=(1024, 768), color=[0, 0, 0],
                duration=backing_track_clip.duration
            )
            karaoke = (
                CompositeVideoClip([background_clip] + lyric_clips).
                set_duration(backing_track_clip.duration).
                set_audio(backing_track_clip)
            )
            karaoke.write_videofile(
                str(targets[0]),
                fps=10,
                # Workaround for missing audio
                # https://github.com/Zulko/moviepy/issues/820
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )

        yield {
            'actions': [(create_video,)],
            'file_dep': [
                output_dir_path / 'accompaniment.wav',
                sync_map_path(output_dir_path),
                silences_path(output_dir_path),
            ],
            'targets': [video_path(input_path, output_dir_path)],
            'verbosity': 2,
        }
    except ImportError:
        yield {
            'actions': [],
            'targets': [video_path(input_path, output_dir_path)],
            'verbosity': 2,
        }
