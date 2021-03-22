from setuptools import setup, find_namespace_packages

setup(
    name='bespokeoke',
    version='1.0',
    packages=find_namespace_packages(),
    entry_points={
        'console_scripts': [
            'karaokedoke = bespokeoke.server.server:main',
            'karaokeize = bespokeoke.karaokeize.karaokeizer:main',
        ],
    },
    install_requires=[
        'aeneas',
        'doit',
        'lyricsgenius',
        'moviepy',
        'mutagen',
        'pydub',
        'spleeter',
    ]
)
