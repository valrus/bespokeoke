import asyncio
import hashlib
import multiprocessing
from argparse import ArgumentParser, Namespace
from doit.reporter import ZeroReporter
from functools import partial
from pathlib import Path

import taglib

from quart import Quart, send_from_directory, request, jsonify, make_response
from werkzeug.utils import secure_filename

from bespokeoke.karaokeize.karaokeizer import build_and_run_tasks
from .sse import ServerSentEvent


SERVER_LOCATION = Path(__file__).resolve().parent
ALLOWED_EXTENSIONS = {'mp3'}

app = Quart(
    __name__,
    static_folder=str(SERVER_LOCATION / 'karaokedoke' / 'static'),
    root_path=str(SERVER_LOCATION)
)
app.clients = set()
app.process_queue = asyncio.Queue()


# # for if the reporter needs to be a class
# def process_reporter_init(self, target, *args):
#     super().__init__(*args)
#     self.target = target
#
# def alpha_hash(s):
#     '''Convert a string into a hash suitable for appending to a Python class name.'''
#     table = str.maketrans('1234567890', 'ghijklmnop')
#     return hashlib.blake2b(s.encode('utf-8'), digest_size=10).hexdigest().translate(table)
#
# song_id_hash = alpha_hash(song_id)
# song_reporter = type(
#     f'ProcessQueueReporter_{song_id_hash}',
#     (ProcessQueueReporter,),
#     {'target': song_id}
# )


class ProcessQueueReporter(ZeroReporter):
    def __init__(self, queue, target, options):
        super().__init__(queue, options)
        self.target = target

    def write(self, data):
        for queue in app.clients:
            queue.put_nowait(data)

    # get_status = execute_task = add_failure = add_success \
    #     = skip_uptodate = skip_ignore = teardown_task = complete_run \
    #     = _just_pass

    def execute_task(self, task):
        self.write({'event': 'start', 'task': task.title(), 'songId': self.target})

    def add_success(self, task):
        self.write({'event': 'step', 'task': task.title(), 'songId': self.target})

    def complete_run(self):
        self.write({'event': 'success', 'songId': self.target })


def song_file_tag(mp3, tag):
    if mp3:
        return mp3.tags.get(tag, [''])[0].strip()
    return None


def song_name(song_file_path, taglib_file=None):
    """Get the name of a song at a given path.

    If the name can be retrieved from mp3 tags, return that. Otherwise
    clean up and return the file name.
    """
    name_from_tags = song_file_tag(taglib_file, 'TITLE')
    if name_from_tags:
        return name_from_tags
    return song_file_path.stem.replace('_', ' ').capwords


def song_artist(taglib_file=None):
    return song_file_tag(taglib_file, 'ARTIST') or 'Unknown Artist'


def has_output_file(song_file_path, output_file_name):
    output_dir = song_file_path.parent / f'{song_file_path.stem}.out'
    if not output_dir.is_dir():
        return False
    return (output_dir / output_file_name).is_file()


@app.route('/')
def elm_app():
    return send_from_directory(str(SERVER_LOCATION / 'karaokedoke'), 'index.html')


def song_file(song_id):
    return app.config['UPLOAD_FOLDER'] / f'{song_id}.mp3'


def song_data_for_file(song_file_path):
    try:
        taglib_file = taglib.File(str(song_file_path))
    except OSError:
        taglib_file = None
    return {
        'name': song_name(song_file_path, taglib_file),
        'artist': song_artist(taglib_file),
        'prepared': all([
            has_output_file(song_file_path, 'accompaniment.wav'),
            has_output_file(song_file_path, 'vocals.wav'),
            has_output_file(song_file_path, 'sync_map.json')
        ])
    }


def songs_json_from_files(song_file_paths):
    return {
        'songs': {
            f.stem: song_data_for_file(f)
            for f in song_file_paths if f.is_file() and any(f.suffix.endswith(ext) for ext in ALLOWED_EXTENSIONS)
        }
    }


@app.route('/songs')
def list_songs():
    return songs_json_from_files(app.config['UPLOAD_FOLDER'].iterdir())


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_song(song_path):
    song_id = song_path.stem
    run_tasks_to_event_stream = partial(
        build_and_run_tasks,
        doit_config={'reporter': ProcessQueueReporter(app.process_queue, song_id, {})}
    )
    asyncio.get_running_loop().run_in_executor(
        None,
        run_tasks_to_event_stream,
        Namespace(input_path=song_path, output_path=None),
        ['task_run_aligner'],
    )


@app.route('/songs', methods=['POST'])
async def upload_songs():
    files = await(request.files)
    # check if the post request has the file part
    if 'song[]' not in files:
        return {}
    song_uploads = files.getlist('song[]')
    # if user does not select file, browser also
    # submit an empty part without filename
    saved_songs = []
    for song in song_uploads:
        if song.filename == '':
            continue
        if song and allowed_file(song.filename):
            filename = secure_filename(song.filename)
            song_path = app.config['UPLOAD_FOLDER'] / filename
            song.save(str(song_path))
            saved_songs.append(song_path)
            process_song(song_path)
    return songs_json_from_files(saved_songs)


@app.route('/song/<song_id>/process')
async def process_upload(song_id):
    process_song(song_id)
    return jsonify(True)


@app.route('/progress')
async def progress_events():
    queue = asyncio.Queue()
    app.clients.add(queue)
    async def send_events():
        while True:
            try:
                data = await queue.get()
                event = ServerSentEvent(data)
                yield event.encode()
            except asyncio.CancelledError as error:
                app.clients.remove(queue)

    response = await make_response(
        send_events(),
        {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Transfer-Encoding': 'chunked',
        },
    )
    response.timeout = None
    return response


def main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--song_dir', type=Path, default=Path(SERVER_LOCATION / 'songs'))
    args = parser.parse_args()

    app.config['UPLOAD_FOLDER'] = args.song_dir
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
    app.run(
        host='localhost',
        port=8080,
        debug=True
    )


if __name__ == '__main__':
    main()
