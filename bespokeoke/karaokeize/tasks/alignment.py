#!/usr/bin/env python3

import io
import json

from aeneas.adjustboundaryalgorithm import AdjustBoundaryAlgorithm
from aeneas.dtw import DTWAlgorithm
from aeneas.executetask import ExecuteTask as AeneasExecuteTask
from aeneas.language import Language
from aeneas.runtimeconfiguration import RuntimeConfiguration
from aeneas.syncmap import SyncMapFormat
from aeneas.syncmap.headtailformat import SyncMapHeadTailFormat
from aeneas.task import Task as AeneasTask
from aeneas.task import TaskConfiguration
from aeneas.textfile import TextFileFormat
import aeneas.globalconstants as gc

from .utils import make_task, lyrics_path, sync_map_path, silences_path


def _find_nonsilent_range(silences_file_path):
    '''Find the beginning and end of the non-silent parts of a track.

    Returns (begin, end), both in milliseconds.'''
    with io.open(silences_file_path) as silences_file:
        silences = json.load(silences_file)
    beginning = silences[0]['end']
    return range(beginning, silences[-1]['begin'] - beginning + 1)


@make_task
def task_run_aligner(output_path):

    def run_aeneas(targets):
        audio_file_path = output_path / 'vocals.wav'
        lyrics_file_path = lyrics_path(output_path)
        nonsilent_range = _find_nonsilent_range(silences_path(output_path))

        # create (aeneas) Task object
        config = TaskConfiguration()
        config[gc.PPN_TASK_LANGUAGE] = Language.ENG
        config[gc.PPN_TASK_IS_TEXT_FILE_FORMAT] = TextFileFormat.MPLAIN

        # Strip silence from beginning and end of the input
        config[gc.PPN_TASK_IS_AUDIO_FILE_HEAD_LENGTH] = nonsilent_range[0] / 1000.0
        config[gc.PPN_TASK_IS_AUDIO_FILE_PROCESS_LENGTH] = nonsilent_range[-1] / 1000.0

        # remove long nonspeech intervals from the output sync map
        config[gc.PPN_TASK_ADJUST_BOUNDARY_NONSPEECH_MIN] = 0.5
        config[gc.PPN_TASK_ADJUST_BOUNDARY_NONSPEECH_STRING] = gc.PPV_TASK_ADJUST_BOUNDARY_NONSPEECH_REMOVE

        # The new boundary between two consecutive fragments will be set at value seconds from the current value.
        # A negative value will move the boundary back, a positive value will move the boundary forward.
        # We don't want to do this here, as the user may want to set boundaries themselves
        # and we don't want to make them set them 0.5 seconds (or whatever) early.
        # Shift event boundaries on the frontend instead.
        # config[gc.PPN_TASK_ADJUST_BOUNDARY_ALGORITHM] = AdjustBoundaryAlgorithm.OFFSET
        # config[gc.PPN_TASK_ADJUST_BOUNDARY_OFFSET_VALUE] = -0.5

        config[gc.PPN_TASK_OS_FILE_FORMAT] = SyncMapFormat.JSON
        task = AeneasTask()
        task.configuration = config
        task.audio_file_path_absolute = str(audio_file_path)
        task.text_file_path_absolute = str(lyrics_file_path)

        runtime_config = RuntimeConfiguration()
        runtime_config[RuntimeConfiguration.DTW_ALGORITHM] = DTWAlgorithm.STRIPE
        runtime_config[RuntimeConfiguration.MFCC_MASK_NONSPEECH] = True

        # process Task
        AeneasExecuteTask(task, rconf=runtime_config).execute()

        # print produced sync map
        sync_map_params = {
            # a.k.a. keep all levels
            gc.PPN_TASK_OS_FILE_LEVELS: None,
            gc.PPN_TASK_OS_FILE_HEAD_TAIL_FORMAT: SyncMapHeadTailFormat.HIDDEN
        }
        task.sync_map.write(SyncMapFormat.JSON, targets[0], parameters=sync_map_params)

    yield {
        'actions': [(run_aeneas,)],
        'file_dep': [
            output_path / 'vocals.wav',
            lyrics_path(output_path),
            silences_path(output_path)
        ],
        'targets': [sync_map_path(output_path)],
        'verbosity': 2,
    }
