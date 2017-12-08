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

def get_prefix_path(prefix: str) -> str:
    """ Interpret prefix as name if it exists in default directory,
        otherwise as path
    """
    prefix_in_default_location = os.path.abspath(f'{prefix_dir}/{prefix}')
    if os.path.exists(prefix_in_default_location):
        print(
            f'Interpreting "{prefix}" as prefix-name '
            f'(points to "{prefix_in_default_location}")')
        return prefix_in_default_location
    else:
        abs_prefix = os.path.abspath(prefix)
        print(
            f'Interpreting "{prefix}" as path '
            f'(points to "{abs_prefix}")')
        return abs_prefix
