from pathlib import Path

from bespokeoke.server.server import DEFAULT_SONG_DIR, create_application


application = create_application(serve_static_files=True, song_dir=DEFAULT_SONG_DIR)
