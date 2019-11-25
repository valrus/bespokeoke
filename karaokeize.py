#!/usr/bin/env python3

import logging
import os
import shutil
from pathlib import Path

from aeneas.exacttiming import TimeValue
from aeneas.executetask import ExecuteTask as AeneasExecuteTask
from aeneas.language import Language
from aeneas.syncmap import SyncMapFormat
from aeneas.task import Task as AeneasTask
from aeneas.task import TaskConfiguration
from aeneas.textfile import TextFileFormat
import aeneas.globalconstants as gc

from doit.task import dict_to_task
from doit.cmd_base import TaskLoader
from doit.doit_cmd import DoitMain

LIBRISPEECH_LEXICON_URL = 'http://www.openslr.org/resources/11/librispeech-lexicon.txt'
PROSODYLAB_LEXICON_URL = 'https://github.com/prosodylab/Prosodylab-Aligner/blob/master/eng.dict?raw=true'


def run_tasks(tasks, args, config=None):
    '''Given a list of `Task` objects, a list of arguments,
    and a config dictionary, execute the tasks.
    '''

    config = {} if config is None else config
    config.setdefault('verbosity', 0)
    config.setdefault('action_string_formatting', 'new')

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


def lyrics_path(input_path):
    return out_dir(input_path) / 'lyrics.txt'


def sync_map_path(input_path):
    return out_dir(input_path) / 'sync_map.json'


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

        tag_lyrics = mp3.tags.get('LYRICS', [''])[0].strip()

        if tag_lyrics:
            with open(out_filename, 'w') as lyrics_file:
                print(*tag_lyrics.splitlines(), sep='\n', file=lyrics_file)
        else:
            genius = lyricsgenius.Genius(os.environ['GENIUS_ACCESS_TOKEN'])
            song = genius.search_song(mp3.tags['TITLE'], mp3.tags['ARTIST'])
            with open(out_filename, 'w') as lyrics_file:
                print(song.lyrics, file=lyrics_file)

    return {
        'actions': [(download_lyrics,)],
        'file_dep': [input_path],
        'targets': [lyrics_path(input_path)],
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
        'uptodate': [True],
        'verbosity': 2,
    }

@make_task
def task_download_prosodylab_lexicon():
    return {
        'actions': [f'wget {PROSODYLAB_LEXICON_URL} -O {{targets}}'],
        'targets': ['prosodylab_lexicon.txt'],
        'uptodate': [True],
        'verbosity': 2
    }


@make_task
def task_download_librispeech_lexicon():
    return {
        'actions': [f'wget {LIBRISPEECH_LEXICON_URL} -O {{targets}}'],
        'targets': ['librispeech_lexicon.txt'],
        'uptodate': [True],
        'verbosity': 2
    }


def _read_lexicon(lexicon_file):
    for line in lexicon_file:
        word, _, orthography = line.partition(' ')
        yield word, orthography


@make_task
def task_combine_lexicons():
    def combine_lexicons(dependencies, targets):
        with open('prosodylab_lexicon.txt', encoding='utf-8') as prosodylab_lexicon:
            lexicon = {
                word: orthography
                for word, orthography in _read_lexicon(prosodylab_lexicon)
            }
        with open('librispeech_lexicon.txt', encoding='utf-8') as librispeech_lexicon:
            for word, orthography in _read_lexicon(librispeech_lexicon):
                lexicon.setdefault(word, orthography)
        with open(targets[0], 'w', encoding='utf-8') as combined_lexicon:
            for word, orthography in sorted(lexicon.items()):
                print(word, orthography, file=combined_lexicon)

    return {
        'actions': [(combine_lexicons,)],
        'file_dep': ['prosodylab_lexicon.txt', 'librispeech_lexicon.txt'],
        'targets': ['combined_lexicon.txt'],
        'uptodate': [True],
        'verbosity': 2
    }


@make_task
def task_run_aligner(input_path):
    def run_aeneas(dependencies, targets):
        audio_file_path = out_dir(input_path) / 'vocals.wav'
        lyrics_file_path = lyrics_path(input_path)
        # create Task object
        config = TaskConfiguration()
        config[gc.PPN_TASK_LANGUAGE] = Language.ENG
        config[gc.PPN_TASK_IS_TEXT_FILE_FORMAT] = TextFileFormat.PLAIN
        config[gc.PPN_TASK_OS_FILE_FORMAT] = SyncMapFormat.JSON
        task = AeneasTask()
        task.configuration = config
        task.audio_file_path_absolute = str(audio_file_path)
        task.text_file_path_absolute = str(lyrics_file_path)

        # process Task
        AeneasExecuteTask(task).execute()

        # print produced sync map
        task.sync_map.write(SyncMapFormat.JSON, targets[0], parameters=None)

    return {
        'actions': [(run_aeneas,)],
        'file_dep': [out_dir(input_path) / 'vocals.wav', lyrics_path(input_path)],
        'targets': [sync_map_path(input_path)],
        'verbosity': 2,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_path', type=Path)
    parser.add_argument('tasks', nargs='*', type=str)
    args = parser.parse_args()

    specified_tasks = [f'task_{task_name}' for task_name in args.tasks]

    # list tasks explicitly here to pass args as necessary
    all_tasks = [
        task_download_prosodylab_lexicon(),
        task_download_librispeech_lexicon(),
        task_combine_lexicons(),
    ]
    if args.input_path:
        all_tasks.extend(
            [
                task_download_lyrics(args.input_path),
                task_separate_audio(args.input_path),
                task_run_aligner(args.input_path)
            ]
        )

    tasks = (task for task in all_tasks if not specified_tasks or task.name in specified_tasks)

    run_tasks(tasks, ['run'])


if __name__ == '__main__':
    main()
