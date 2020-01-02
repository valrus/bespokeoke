#!/usr/bin/env python3

from aeneas.exacttiming import TimeValue
from aeneas.executetask import ExecuteTask as AeneasExecuteTask
from aeneas.language import Language
from aeneas.syncmap import SyncMapFormat
from aeneas.task import Task as AeneasTask
from aeneas.task import TaskConfiguration
from aeneas.textfile import TextFileFormat
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
        'file_dep': [output_path / 'vocals.wav', lyrics_path(output_path)],
        'targets': [sync_map_path(output_path)],
        'verbosity': 2,
    }
