#!/usr/bin/env python3

from contextlib import contextmanager
import os

from doit.task import dict_to_task


SEPARATION_OUTPUT_NAMES = [
    'accompaniment',
    'vocals'
]

def make_task(task_dict_func):
    '''Wrapper to decorate functions returning pydoit
    `Task` dictionaries and have them return pydoit `Task`
    objects
    '''
    def d_to_t(*args, **kwargs):
        for ret_dict in task_dict_func(*args, **kwargs):
            yield dict_to_task({'name': task_dict_func.__name__, **ret_dict})
    return d_to_t


def lyrics_path(output_path):
    return output_path / 'lyrics.txt'


def sync_map_path(output_path):
    return output_path / 'sync_map.json'


def silences_path(output_path):
    return output_path / 'silences.json'


def video_path(input_path, output_path):
    return output_path / f'{input_path.stem}_karaoke.mp4'


def separation_output_files(output_path):
    return (output_path / f'{name}.wav' for name in SEPARATION_OUTPUT_NAMES)


@contextmanager
def working_dir(target_dir):
    current_dir = os.getcwd()
    try:
        os.chdir(target_dir)
        yield
    finally:
        os.chdir(current_dir)
