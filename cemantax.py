#!/usr/bin/env python3

import sys
import os
import time
import inspect

import requests
from gensim.models import KeyedVectors


DEBUG = bool(os.environ.get("DEBUG", False))
HERE = os.path.dirname(os.path.realpath(inspect.getsourcefile(lambda: 0)))

MODEL_PATH = os.path.join(
    HERE,
    "frWiki_no_lem_no_postag_no_phrase_1000_skip_cut100.bin"
)
DIC_PATH = os.path.join(
    HERE,
    "liste_francais_ascii_bis.txt"
)

URL = "https://cemantix.herokuapp.com/score"


# UTILS
def warn(*args):
    print("Warning: ", end="", file=sys.stderr)
    print(*args, file=sys.stderr)


# REQUESTS
def _post(url, data=None):
    res = None
    for _ in range(10):
        try:
            res = requests.post(url, data=data)
            if res.status_code != 200:
                raise requests.RequestException
        except requests.RequestException:
            warn("request failed for url:", url)
            time.sleep(1)
        else:
            break
    return res


def post_word(word):
    res = _post(URL, {"word": word})
    if res is None:
        return None
    try:
        return res.json()
    except ValueError:
        warn("json decode failed - content:", res.content.decode())
        return None


# WORD2VEC
def load_dic(dic_path):
    with open(dic_path) as f:
        return [line.rstrip() for line in f]


def load_model(model_path):
    # TODO: download models?
    return KeyedVectors.load_word2vec_format(
        model_path,
        binary=True,
        unicode_errors="ignore"
    )


if __name__ == "__main__":
    voc = load_dic(DIC_PATH)
    model = load_model(MODEL_PATH)

    voc_dic = {}
    for w in voc:
        try:
            voc_dic[w] = model.most_similar(w)
        except KeyError:
            warn(f"could find word '{w}' in model")
