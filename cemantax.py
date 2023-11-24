#!/usr/bin/env python3

import sys
import os
import time
import inspect
import random

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
    # "liste_francais_ascii_bis.txt"
    "superdic.txt"
)

URL = "https://cemantix.certitudes.org/score"


# REQUESTS
def _post(url, data=None):
    res = None
    for _ in range(10):
        try:
            res = requests.post(url, data=data, headers={
                "Origin": "https://cemantix.certitudes.org"
            })
            if res.status_code != 200:
                raise requests.RequestException
        except requests.RequestException:
            print("Warning: request failed for url:", url)
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
        print("Warning: json decode failed - content:", res.content.decode())
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


# SOLVER
def get_word(prev_word, score, dic, score_dic):
    sorted_w = sorted(score_dic, key=lambda x: score_dic[x], reverse=True)
    pos = [w for w in sorted_w if score_dic[w] > 0.2][:12]
    neg = [w for w in sorted_w[::-1] if score_dic[w] < 0.1][:12]
    if not pos and not neg:
        if score > 0:
            pos.append(prev_word)
        else:
            neg.append(prev_word)

    words = model.most_similar(
        positive=pos,
        negative=neg,
        topn=len(dic)
    )

    # print("words:", words[:3])      # DEBUG
    for w, s in words:
        if w in dic and w not in score_dic.keys():
            return w
    raise Exception("prout")


def solve(model, dic):
    score_dic = {}

    # first try at random:
    random.shuffle(dic)
    w = dic[0]

    while 42:
        print("w:", w)      # DEBUG
        req = post_word(w)
        print(req)      # DEBUG
        score = req["score"]
        score_dic[w] = score
        if score == 1:
            break

        # sorted_w = sorted(score_dic, key=lambda x: score_dic[x], reverse=True)
        # best, worst = sorted_w[0], sorted_w[-1]
        # if score < 0.2 and score_dic[best] < 0.3 and score_dic[worst] < 0:
        #     w = worst
        #     print("* using previous WORST *")
        # elif score_dic[best] > 0.3:
        #     w = best
        #     print("* using previous BEST *")
        w = get_word(w, score, dic, score_dic)

        time.sleep(0.1)

    print(f"YAY! '{w}' found in {len(score_dic)} tries")
    return score_dic


if __name__ == "__main__":
    dic = load_dic(DIC_PATH)
    model = load_model(MODEL_PATH)

    solve(model, dic)
