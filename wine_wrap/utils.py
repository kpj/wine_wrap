import os
import json

from typing import Dict

from appdirs import AppDirs


def _ensure_dir(fname: str) -> str:
    dir_ = os.path.dirname(fname)
    if not os.path.isdir(dir_):
        os.makedirs(dir_)
    return fname

adirs = AppDirs('wine_wrap', 'kpj')
state_file = f'{adirs.user_data_dir}/state.csv'
prefix_dir = _ensure_dir(f'{adirs.user_data_dir}/prefixes/')

def get_state() -> Dict[str, Dict[str, str]]:
    if os.path.exists(state_file):
        with open(state_file) as fd:
            return json.load(fd)
    else:
        return {}

def dump_state(data: Dict[str, Dict[str, str]]) -> None:
    with open(state_file, 'w') as fd:
        json.dump(data, fd)

def get_prefix_name_from_path(path: str) -> str:
    """ Assume prefix-name to the last non-empty string after splitting along '/'
    """
    parts = path.split('/')
    for p in reversed(parts):
        if p:
            return p
