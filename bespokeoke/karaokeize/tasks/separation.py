#!/usr/bin/env python3

from spleeter.separator import Separator

from .utils import make_task


@make_task
def task_separate_audio(input_path, output_dir_path):
    def separate_audio():
        output_dir_path.mkdir(parents=True, exist_ok=True)
        # Using embedded configuration.
        separator = Separator('spleeter:2stems', multiprocess=False)
        separator.separate_to_file(
            str(input_path),
            output_dir_path,
            filename_format='{instrument}.{codec}'
        )

    return {
        'actions': [(separate_audio,)],
        'file_dep': [input_path],
        'targets': [output_dir_path / 'accompaniment.wav', output_dir_path / 'vocals.wav'],
        'uptodate': [True],
        'verbosity': 2,
    }
