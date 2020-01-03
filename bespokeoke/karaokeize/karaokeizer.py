#!/usr/bin/env python3

import logging
from pathlib import Path

from doit.cmd_base import TaskLoader
from doit.doit_cmd import DoitMain

from .tasks import *


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


def _default_out_dir(input_path):
    return input_path.parent / f'{input_path.stem}.out'


def build_and_run_tasks(args, doit_args):
    # list tasks explicitly here to pass args as necessary
    all_tasks = []
    if args.input_path:
        output_dir_path = args.output_path or _default_out_dir(args.input_path)
        all_tasks.extend(
            [
                task_download_lyrics(args.input_path, output_dir_path),
                task_separate_audio(args.input_path, output_dir_path),
                task_run_aligner(output_dir_path),
                task_find_silences(output_dir_path),
                task_create_video(args.input_path, output_dir_path),
            ]
        )

    run_tasks(all_tasks, doit_args)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_path', type=Path)
    parser.add_argument('-o', '--output_path', type=Path, default=None)
    args, doit_args = parser.parse_known_args()

    build_and_run_tasks(args, doit_args)


if __name__ == '__main__':
    main()
