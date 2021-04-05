#!/usr/bin/env python3

from pathlib import Path

from .utils import make_task, separation_output_files


@make_task
def task_compress_track(output_dir_path):
    for input_path in separation_output_files(output_dir_path):
        output_path = Path(input_path).with_suffix('.mp3')
        yield {
            'name': f'task_compress_{input_path.stem}',
            'actions': [
                ['ffmpeg', '-i', input_path, output_path]
            ],
            'file_dep': [input_path],
            'targets': [output_path],
            'uptodate': [True],
            'verbosity': 2
        }
