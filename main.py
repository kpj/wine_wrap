import os
import json
import datetime

from typing import Dict, Optional

import sh
import click
from appdirs import AppDirs


def _ensure_dir(fname: str) -> str:
    dir_ = os.path.dirname(fname)
    if not os.path.isdir(dir_):
        os.makedirs(dir_)
    return fname

def get_state() -> Dict[str, Dict[str, str]]:
    if os.path.exists(state_file):
        with open(state_file) as fd:
            return json.load(fd)
    else:
        return {}

def dump_state(data: Dict[str, Dict[str, str]]) -> None:
    with open(state_file, 'w') as fd:
        json.dump(data, fd)

adirs = AppDirs('wine_wrap', 'kpj')
state_file = f'{adirs.user_data_dir}/state.csv'
prefix_dir = _ensure_dir(f'{adirs.user_data_dir}/prefixes/')

class WineWrapper:
    def __init__(
        self,
        script_path: str, prefix: Optional[str] = None
    ) -> None:
        self.script_path = os.path.abspath(script_path)
        script_name = os.path.basename(self.script_path)
        print(f'Initializing wine-wrapper for "{script_name}"')

        if prefix is None:
            state_dict = get_state()
            if script_name in state_dict:
                self.prefix = state_dict[script_name]['prefix']
                print(' > Using existing script-prefix association...')
            else:
                self.prefix = f'{prefix_dir}/WINEPREFIX__{script_name}/'
                print(' > Creating new script-prefix association...')

                state_dict[script_name] = {
                    'prefix': self.prefix
                }
                dump_state(state_dict)
        else:
            self.prefix = os.path.abspath(prefix)
            print(f' > Using forced prefix...')

        self._setup()

    def configure(self) -> None:
        self._wine('winecfg')
        self._commit('Configured')

    def execute(self) -> None:
        print(f'Executing {self.script_path}')
        self._wine(self.script_path)

    def _setup(self) -> None:
        if not os.path.exists(self.prefix):
            print(' > Creating new wine-prefix...')
            os.makedirs(self.prefix)

            # initialize new wine-prefix
            self._git('init')
            self._wine('wineboot')
            self._commit('Initial commit')
        else:
            print(' > Using existing wine-prefix...')

    def _commit(self, msg: str = '') -> None:
        date_str = datetime.datetime.now()

        # commit changes to current wine-prefix
        self._git('add', '.')
        self._git('commit', '-a', m=f'[{date_str}] {msg}')

    def _git(self, *arg: str, **kwargs: str) -> None:
        sh.git(*arg, **kwargs, _cwd=self.prefix)

    def _wine(self, *arg: str, **kwargs: str) -> None:
        cmd_env = {
            'WINEPREFIX': self.prefix
        }
        sh.wine(*arg, **kwargs, _env=cmd_env)

@click.group()
def main() -> None:
    pass

@main.command(help='Show current setup.')
def show() -> None:
    state_dict = get_state()

    for script_name, data in sorted(state_dict.items()):
        print(f'--- {script_name} ---')
        for k, v in sorted(data.items()):
            print(f' > {k}: {v}')

@main.command(help='Execute given script in wine-prefix.')
@click.argument('script', type=click.Path(exists=True))
@click.option(
    '-p', '--prefix', default=None, type=click.Path(exists=False),
    help='Force WINEPREFIX to use.')
def run(script: str, prefix: Optional[str]) -> None:
    ww = WineWrapper(script, prefix)
    ww.execute()

if __name__ == '__main__':
    main()
