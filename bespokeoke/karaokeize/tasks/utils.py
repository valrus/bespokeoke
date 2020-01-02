#!/usr/bin/env python3

from doit.task import dict_to_task


def make_task(task_dict_func):
    '''Wrapper to decorate functions returning pydoit
    `Task` dictionaries and have them return pydoit `Task`
    objects
    '''
    def d_to_t(*args, **kwargs):
        ret_dict = task_dict_func(*args, **kwargs)
        return dict_to_task({'name': task_dict_func.__name__, **ret_dict})
    return d_to_t


def lyrics_path(output_path):
    return output_path / 'lyrics.txt'


def sync_map_path(output_path):
    return output_path / 'sync_map.json'


def silences_path(output_path):
    return output_path / 'silences.json'


def video_path(input_path, output_path):
    return output_path / f'{input_path.stem}_karaoke.mp4'
