#!/usr/bin/env python3

import os
from pathlib import Path

from doit.task import dict_to_task
from doit.cmd_base import TaskLoader
from doit.doit_cmd import DoitMain


def run_tasks(tasks, args, config={'verbosity': 0}):
    '''Given a list of `Task` objects, a list of arguments,
    and a config dictionary, execute the tasks.
    '''

    if type(tasks) is not list:
        raise TypeError('tasks must be of type list.')

    class Loader(TaskLoader):
        @staticmethod
        def load_tasks(cmd, opt_values, pos_args):
            return tasks, config

    return DoitMain(Loader()).run(args)


def make_task(task_dict_func):
    '''Wrapper to decorate functions returning pydoit
    `Task` dictionaries and have them return pydoit `Task`
    objects
    '''
    def d_to_t(*args, **kwargs):
        ret_dict = task_dict_func(*args, **kwargs)
        return dict_to_task({'name': task_dict_func.__name__, **ret_dict})
    return d_to_t


def out_dir(input_path):
    return Path(f'{input_path.stem}.out')


@make_task
def task_gunzip_data():
    return {'name': 'gunzip',
            'actions': ['gunzip -c %(dependencies)s > %(targets)s'],
            'targets': ['Melee_data.csv'],
            'file_dep': ['Melee_data.csv.gz']}


@make_task
def task_deps_targets():

    def do_whatever(dependencies, targets):
        # note auto-injected dependencies and targets
        pass

    return {'actions': [do_whatever],
            'name': 'look at me',
            'file_dep': ['input.csv'],
            'targets': ['output.pdf']}


@make_task
def task_download_lyrics(input_path):

    def download_lyrics(targets):
        import lyricsgenius
        import taglib

        out_filename = targets[0]
        out_dir(input_path).mkdir(parents=True, exist_ok=True)
        mp3 = taglib.File(str(input_path))

        genius = lyricsgenius.Genius(os.environ['GENIUS_ACCESS_TOKEN'])
        song = genius.search_song(mp3.tags['TITLE'], mp3.tags['ARTIST'])
        with open(out_filename, 'w') as lyrics_file:
            print(song.lyrics, file=lyrics_file)

    return {
        'actions': [(download_lyrics,)],
        'file_dep': [input_path],
        'targets': [out_dir(input_path) / 'lyrics.txt'],
        'verbosity': 2
    }


@make_task
def task_separate_audio(input_path):
    def separate_audio():
        from spleeter.separator import Separator

        out_dir(input_path).mkdir(parents=True, exist_ok=True)
        # Using embedded configuration.
        separator = Separator('spleeter:2stems')
        separator.separate_to_file(str(input_path), out_dir(input_path))

    return {
        'actions': [(separate_audio,)],
        'file_dep': [input_path],
        'targets': [out_dir(input_path) / 'accompaniment.wav', out_dir(input_path) / 'vocals.wav'],
        'verbosity': 2,
    }

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('input_path', type=Path)
    args = parser.parse_args()

    tasks = []
    tasks.append(task_download_lyrics(args.input_path))
    tasks.append(task_separate_audio(args.input_path))

    run_tasks(tasks, ['run'])


if __name__ == '__main__':
    main()
