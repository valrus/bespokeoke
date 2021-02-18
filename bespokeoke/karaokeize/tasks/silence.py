#!/usr/bin/env python3

import json

from .utils import make_task, silences_path


@make_task
def task_find_silences(output_dir_path):

    def find_silences(dependencies, targets):
        from pydub import AudioSegment
        from pydub.silence import detect_silence

        vocals_file_path = dependencies[0]
        audio = AudioSegment.from_file(vocals_file_path, format='wav')
        silences = detect_silence(audio, min_silence_len=500, silence_thresh=-35)
        silences_file_path = targets[0]
        with open(silences_file_path, 'w', encoding='utf-8') as silences_file:
            json.dump(
                [{'begin': begin, 'end': end} for begin, end in silences],
                silences_file
            )

    return {
        'actions': [(find_silences,)],
        'file_dep': [output_dir_path / 'vocals.wav'],
        'targets': [silences_path(output_dir_path)],
        'verbosity': 2
    }
