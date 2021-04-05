#!/usr/bin/env python3

from .utils import make_task, SEPARATION_OUTPUT_NAMES


@make_task
def task_karaokedokeize():
    '''Convenience task group to do the minimum necessary for Karaokedoke.'''
    yield {
        'actions': None,
        'task_dep': ['task_run_aligner'] + [
            f'task_compress_{name}'
            for name in SEPARATION_OUTPUT_NAMES
        ]
    }
