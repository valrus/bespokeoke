#!/usr/bin/env python3

import sys

from doit.reporter import ConsoleReporter, ZeroReporter


# nb try to get this to produce output actually
class ProcessQueueReporter(ConsoleReporter):
    def __init__(self, queue, target, options):
        super().__init__(queue, options)
        self.target = target

    def write(self, data):
        sys.stdout.write(str(data))
        open('doit.out', 'a').write(f'{str(data)}\n')
        self.outstream.put_nowait(data)

    # get_status = execute_task = add_failure = add_success \
    #     = skip_uptodate = skip_ignore = teardown_task = complete_run \
    #     = _just_pass

    def execute_task(self, task):
        super().execute_task(task)
        self.write({'event': 'start', 'task': task.title(), 'songId': self.target})

    def add_success(self, task):
        super().add_success(task)
        self.write({'event': 'step', 'task': task.title(), 'songId': self.target})

    def complete_run(self):
        super().complete_run()
        self.write({'event': 'success', 'songId': self.target })
