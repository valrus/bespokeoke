#!/usr/bin/env python3

from spleeter.separator import Separator

from .utils import make_task, separation_output_files


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

    yield {
        'actions': [(separate_audio,)],
        'file_dep': [input_path],
        'targets': list(separation_output_files(output_dir_path)),
        'uptodate': [True],
        'verbosity': 2,
    }
