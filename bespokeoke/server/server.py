from argparse import ArgumentParser
from pathlib import Path
import taglib

# from bottle import Bottle, ConfigDict, template, static_file
from quart import Quart, send_from_directory, request
from werkzeug.utils import secure_filename

SERVER_LOCATION = Path(__file__).resolve().parent
UPLOAD_FOLDER = '/path/to/the/uploads'
ALLOWED_EXTENSIONS = {'mp3'}

app = Quart(
    __name__,
    static_folder=str(SERVER_LOCATION / 'karaokedoke' / 'static')
)

# app = Bottle()


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


# @app.route('/static/<filepath:path>')
# def server_static(filepath):
#     return static_file(filepath, root=str(SERVER_LOCATION / 'karaokedoke' / 'static'))


@app.route('/')
def elm_app():
    # return static_file('index.html', root=str(SERVER_LOCATION / 'karaokedoke'))
    return send_from_directory('karaokedoke', 'index.html')


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
    return songs_json_from_files(saved_songs)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('song_dir', type=Path)
    args = parser.parse_args()

    # app_config = ConfigDict()
    # app_config.update(song_dir=args.song_dir)
    # app.config = app_config

    app.config['UPLOAD_FOLDER'] = args.song_dir
    app.run(
        host='localhost',
        port=8080,
        debug=True
    )
