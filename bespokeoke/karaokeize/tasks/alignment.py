#!/usr/bin/env python3

from aeneas.exacttiming import TimeValue
from aeneas.executetask import ExecuteTask as AeneasExecuteTask
from aeneas.language import Language
from aeneas.syncmap import SyncMapFormat
from aeneas.task import Task as AeneasTask
from aeneas.task import TaskConfiguration
from aeneas.textfile import TextFileFormat
from aeneas.syncmap.headtailformat import SyncMapHeadTailFormat
import aeneas.globalconstants as gc

from .utils import make_task, lyrics_path, sync_map_path, silences_path


@make_task
def task_run_aligner(output_path):

    def run_aeneas(targets):
        audio_file_path = output_path / 'vocals.wav'
        lyrics_file_path = lyrics_path(output_path)
        silences_file_path = silences_path(output_path)

        # create (aeneas) Task object
        config = TaskConfiguration()
        config[gc.PPN_TASK_LANGUAGE] = Language.ENG
        config[gc.PPN_TASK_IS_TEXT_FILE_FORMAT] = TextFileFormat.MPLAIN
        config[gc.PPN_TASK_OS_FILE_FORMAT] = SyncMapFormat.JSON
        # config[gc.PPN_TASK_IS_AUDIO_FILE_HEAD_LENGTH] = first_silence_end
        # config[gc.PPN_TASK_IS_AUDIO_FILE_TAIL_LENGTH] = last_silence_beginning
        task = AeneasTask()
        task.configuration = config
        task.audio_file_path_absolute = str(audio_file_path)
        task.text_file_path_absolute = str(lyrics_file_path)

        # process Task
        AeneasExecuteTask(task).execute()

        # print produced sync map
        sync_map_params = {
            # a.k.a. keep all levels
            gc.PPN_TASK_OS_FILE_LEVELS: None,
            gc.PPN_TASK_OS_FILE_HEAD_TAIL_FORMAT: SyncMapHeadTailFormat.HIDDEN
        }
        task.sync_map.write(SyncMapFormat.JSON, targets[0], parameters=sync_map_params)

    return {
        'actions': [(run_aeneas,)],
        'file_dep': [
            output_path / 'vocals.wav',
            lyrics_path(output_path),
            silences_path(output_path)
        ],
        'targets': [sync_map_path(output_path)],
        'verbosity': 2,
    }
