from pathlib import Path

from bespokeoke.server.server import SERVER_LOCATION, create_application


application = create_application(serve_static_files=False)
application.config['UPLOAD_FOLDER'] = Path(SERVER_LOCATION / 'songs')
application.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
