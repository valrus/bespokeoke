# Bespokeoke - karaokeize your library

Bespokeoke is a tool to make any mp3 suitable for karaoke.
It has two parts, one of which is in a prototype/pre-alpha state of usability
and the other of which is still in development. Respectively:

1. *Karaokeizer* is a Python program that pulls together a few other tools
into an easy-to-use pipeline that takes an mp3 in one end
and spits a karaoke video file, sans vocals and with time-matched lyric display,
out the other end.

2. *Karaokedoke** is an Elm webapp allowing you to manage your karaokeized songs
and tweak them where the automated tools that make up the karaokeizer
fell down on the job.

It's still very much alpha or earlier, in terms of rough edges.

## Manual installation requirements

* Install the system dependencies, `elm` and `ffmpeg`
* Get a Genius access token and export it to an environment variable: `export GENIUS_ACCESS_TOKEN=$YOUR_TOKEN`
* Compile the Elm component: `elm make bespokeoke/karaokedoke/static/js/elm/Karaokedoke.elm --output=bespokeoke/karaokedoke/static/js/elm.js`

## Running the server

From this directory, either:
`python -m bespokeoke.server`
`pip install -e .` and then `karaokedoke`.
If you do the latter you need to `pip install -e .` for every change.

## Credits

Bespokeoke is mostly an assemblage of other tools.
It depends heavily on:
* [spleeter] for audio separation
* [aeneas] for lyric/audio alignment
* [lyricsgenius] for downloading lyrics

[spleeter]: https://github.com/deezer/spleeter
[aeneas]: https://github.com/readbeyond/aeneas
[lyricsgenius]: https://github.com/johnwmillr/lyricsgenius
