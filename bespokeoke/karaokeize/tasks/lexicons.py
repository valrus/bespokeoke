#!/usr/bin/env python3

from .utils import make_task

LIBRISPEECH_LEXICON_URL = 'http://www.openslr.org/resources/11/librispeech-lexicon.txt'
PROSODYLAB_LEXICON_URL = 'https://github.com/prosodylab/Prosodylab-Aligner/blob/master/eng.dict?raw=true'


@make_task
def task_download_prosodylab_lexicon():
    return {
        'actions': [f'wget {PROSODYLAB_LEXICON_URL} -O {{targets}}'],
        'targets': ['prosodylab_lexicon.txt'],
        'uptodate': [True],
        'verbosity': 2
    }


@make_task
def task_download_librispeech_lexicon():
    return {
        'actions': [f'wget {LIBRISPEECH_LEXICON_URL} -O {{targets}}'],
        'targets': ['librispeech_lexicon.txt'],
        'uptodate': [True],
        'verbosity': 2
    }


def _read_lexicon(lexicon_file):
    for line in lexicon_file:
        word, _, orthography = line.partition(' ')
        yield word, orthography


@make_task
def task_combine_lexicons():
    def combine_lexicons(targets):
        with open('prosodylab_lexicon.txt', encoding='utf-8') as prosodylab_lexicon:
            lexicon = dict(_read_lexicon(prosodylab_lexicon))
        with open('librispeech_lexicon.txt', encoding='utf-8') as librispeech_lexicon:
            for word, orthography in _read_lexicon(librispeech_lexicon):
                lexicon.setdefault(word, orthography)
        with open(targets[0], 'w', encoding='utf-8') as combined_lexicon:
            for word, orthography in sorted(lexicon.items()):
                print(word, orthography, file=combined_lexicon)

    return {
        'actions': [(combine_lexicons,)],
        'file_dep': ['prosodylab_lexicon.txt', 'librispeech_lexicon.txt'],
        'targets': ['combined_lexicon.txt'],
        'uptodate': [True],
        'verbosity': 2
    }
