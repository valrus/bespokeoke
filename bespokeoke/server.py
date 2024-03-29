import hashlib
import json
import logging
import multiprocessing
import os
import shutil
import time
from argparse import ArgumentParser, Namespace
from functools import partial
from pathlib import Path

from flask import Flask, Response, send_from_directory, request, jsonify
from werkzeug.utils import secure_filename

from karaokeizer.karaokeizer import build_and_run_tasks
from .process_queue_reporter import ProcessQueueReporter
from .song_data import SongData
from .sse import ServerSentEvent


SERVER_LOCATION = Path(__file__).resolve().parent
ALLOWED_EXTENSIONS = {'mp3'}
DEFAULT_SONG_DIR = Path(SERVER_LOCATION / 'songs')


def songs_json_from_files(song_file_paths):
    return {
        'songs': dict(
            SongData.from_file(f).id_json_pair()
            for f in song_file_paths
            if f.is_file() and any(f.suffix.endswith(ext) for ext in ALLOWED_EXTENSIONS)
        )
    }


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_application(serve_static_files=True, song_dir=DEFAULT_SONG_DIR):
    application = Flask(
        __name__,
        static_folder=str(SERVER_LOCATION / 'karaokedoke' / 'static'),
        root_path=str(SERVER_LOCATION)
    )
    application.clients = set()
    application.process_pool = multiprocessing.Pool()
    application.process_queue = multiprocessing.Manager().Queue()
    application.config['UPLOAD_FOLDER'] = song_dir
    application.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
    song_dir.mkdir(parents=True, exist_ok=True)

    def output_dir(song_id):
        return application.config['UPLOAD_FOLDER'] / f'{song_id}.out'

    def song_file(song_id):
        return application.config['UPLOAD_FOLDER'] / f'{song_id}.mp3'

    def delete_song_files(song_id):
        shutil.rmtree(output_dir(song_id), ignore_errors=True)
        song_file(song_id).unlink()
        return True

    def song_data_for_id(song_id):
        return SongData.from_file(application.config['UPLOAD_FOLDER'] / f'{song_id}.mp3').to_json()

    @application.route('/api/songs')
    def list_songs():
        return songs_json_from_files(application.config['UPLOAD_FOLDER'].iterdir())

    @application.route('/api/songs/<song_id>')
    def get_song(song_id):
        return send_from_directory(application.config['UPLOAD_FOLDER'], f'{song_id}.mp3')

    @application.route('/api/songs/<song_id>', methods=["DELETE"])
    def delete_song(song_id):
        return {'success': delete_song_files(song_id)}

    @application.route('/api/song_data/<song_id>')
    def get_song_data(song_id):
        return song_data_for_id(song_id)

    def handle_process_result(song_id, result):
        '''Queue a message regarding the result of a process.

        Possible result codes, per the doit docs:
        0 => all tasks executed successfully
        1 => task failed
        2 => error executing task
        3 => error before task execution starts (in this case the reporter is not used)

        TODO: more granularity?
        '''
        if result == 0:
            event = {'event': 'success', 'task': 'processing', 'songId': song_id}
        elif result == 1:
            event = {'event': 'error 1', 'task': 'processing', 'songId': song_id}
        elif result == 2:
            event = {'event': 'error 2', 'task': 'processing', 'songId': song_id}
        elif result == 3:
            event = {'event': 'error 3', 'task': 'processing', 'songId': song_id}

        application.process_queue.put_nowait(event)

    def handle_process_error(song_id, exception):
        logging.error(exception)
        application.process_queue.put_nowait({'event': 'error', 'task': 'processing', 'songId': song_id})

    def multiprocess_song(song_data, youtube_url=None):
        # application.process_queue.put_nowait({'event': 'start', 'task': 'processing', 'songId': song_id})
        return application.process_pool.apply_async(
            build_and_run_tasks,
            (
                Namespace(
                    input_path=song_data.file_path,
                    output_path=None,
                    youtube_url=youtube_url,
                    title=song_data.name,
                    artist=song_data.artist
                ),
                ['task_karaokedokeize']
            ),
            {
                'doit_config': {
                    'reporter': ProcessQueueReporter(application.process_queue, song_data.song_id(), {}),
                    'verbosity': 2,
                },
            },
            callback=partial(handle_process_result, song_data.song_id()),
            error_callback=partial(handle_process_error, song_data.song_id())
        )

    @application.route('/api/songs', methods=['POST'])
    def upload_songs():
        files = request.files
        # check if the post request has the file part
        if 'song[]' not in files:
            return {}
        song_uploads = files.getlist('song[]')
        # if user does not select file, browser also
        # submit an empty part without filename
        saved_songs = []
        process_things = []
        for song in song_uploads:
            if song.filename == '':
                continue
            if song and allowed_file(song.filename):
                song_path = application.config['UPLOAD_FOLDER'] / secure_filename(song.filename)
                song.save(str(song_path))
                song_data = SongData.from_file(song_path)
                saved_songs.append(song_data)
                process_things.append(multiprocess_song(song_data))
        return {'songs': dict([song_data.id_json_pair() for song_data in saved_songs])}

    def valid_youtube_url(url):
        # TODO expand on this to be safer
        return 'youtube.com' in url or 'youtu.be' in url

    @application.route('/api/songs/youtube', methods=['POST'])
    def scrape_youtube_song():
        import ipdb; ipdb.set_trace()
        youtube_data = request.json
        song_data = SongData(
            name=youtube_data['song'],
            artist=youtube_data['artist'],
            prepared=False,
            file_path=application.config['UPLOAD_FOLDER']
        )
        process_things = []
        if song_data.file_path and valid_youtube_url(youtube_data['url']):
            process_things.append(multiprocess_song(song_data, youtube_url=youtube_data['url']))
        return {'songs': dict([song_data.id_json_pair()])}

    @application.route('/api/progress')
    def progress_events():
        def send_events():
            while True:
                data = application.process_queue.get()
                event = ServerSentEvent(json.dumps(data))
                if application.debug:
                    print(event.encode())
                yield event.encode()
                # don't send messages too fast
                time.sleep(0.1)

        response = Response(
            send_events(),
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                # chunking seems to cause firefox disconnects
                # 'Transfer-Encoding': 'chunked',
            },
        )
        response.timeout = None
        return response

    @application.route('/api/lyrics/<song_id>', methods=['PUT'])
    def update_lyrics(song_id):
        with open(os.path.join(output_dir(song_id), 'sync_map.json'), 'w') as sync_map_file:
            json.dump(request.json['syncMap'], sync_map_file, indent=1)
        return json.dumps(True)

    if serve_static_files:
        @application.route('/images/<file_name>')
        def static_image(file_name):
            return send_from_directory(str(Path(application.static_folder) / 'images'), file_name)

        @application.route('/fonts/<font_dir>/<file_name>')
        def static_font(font_dir, file_name):
            return send_from_directory(str(Path(application.static_folder) / 'css' / 'fonts' / font_dir), file_name)

        @application.route('/accompaniment/<song_id>')
        def accompaniment_track(song_id):
            return send_from_directory(output_dir(song_id), 'accompaniment.mp3')

        @application.route('/vocals/<song_id>')
        def vocal_track(song_id):
            return send_from_directory(output_dir(song_id), 'vocals.mp3')

        @application.route('/lyrics/<song_id>')
        def lyrics(song_id):
            return send_from_directory(output_dir(song_id), 'sync_map.json')

    @application.route('/', defaults={'path': ''})
    @application.route('/<path:path>')
    def elm_app(path):
        return send_from_directory(str(SERVER_LOCATION / 'karaokedoke'), 'index.html')

    return application


def main():
    # macos multiprocessing issue
    # https://stackoverflow.com/questions/50168647/multiprocessing-causes-python-to-crash-and-gives-an-error-may-have-been-in-progr
    os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
    parser = ArgumentParser()
    parser.add_argument('-s', '--song_dir', type=Path, default=DEFAULT_SONG_DIR)
    args = parser.parse_args()

    logging.basicConfig(filename='bespokeoke.log', level=logging.DEBUG)

    application = create_application(serve_static_files=True, song_dir=args.song_dir)
    application.run(
        host='0.0.0.0',
        debug=True
    )


if __name__ == '__main__':
    main()
