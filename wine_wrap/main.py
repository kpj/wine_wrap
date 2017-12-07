import os
import json
import shutil
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

class PrefixHandler:
    def __init__(self, prefix_path: str) -> None:
        self.prefix = prefix_path
        self.master_prefix = f'{prefix_dir}/master_prefix'

        self._setup()

    def __repr__(self) -> str:
        return self.prefix

    def _setup(self) -> None:
        # check for master-prefix
        if not os.path.exists(self.master_prefix):
            print('Master-prefix does not exist. Creating...')
            self._create_prefix(self.master_prefix)
        else:
            print('Using existing master-prefix...')

        # create actual prefix if needed
        if not os.path.exists(self.prefix):
            print('Creating new wine-prefix from master...')
            shutil.copytree(self.master_prefix, self.prefix, symlinks=True)
        else:
            print('Using existing wine-prefix...')

    def _create_prefix(self, path: str) -> None:
        os.makedirs(path)

        # initialize new wine-prefix
        print(' > Initializing git repository')
        self._git('init', cwd=path)

        print(' > Booting wine')
        self._wine('wineboot', cwd=path)

        print(' > Commiting changes')
        self._commit('Initial commit', cwd=path)

    def _commit(self, msg: str = '', cwd: Optional[str] = None) -> None:
        date_str = datetime.datetime.now()

        # commit changes to current wine-prefix
        self._git('add', '.', cwd=cwd)
        self._git('commit', '-a', m=f'[{date_str}] {msg}', cwd=cwd)

    def _git(
        self,
        *arg: str, cwd: Optional[str] = None, **kwargs: str
    ) -> None:
        sh.git(*arg, **kwargs, _cwd=cwd or self.prefix)

    def _wine(
        self,
        *arg: str, cwd: Optional[str] = None, **kwargs: str
    ) -> None:
        cmd_env = {
            'WINEPREFIX': cwd or self.prefix
        }
        sh.wine(*arg, **kwargs, _env=cmd_env)

class WineWrapper:
    def __init__(
        self,
        script_path: str, prefix_path: Optional[str] = None
    ) -> None:
        self.script_path = os.path.abspath(script_path)
        script_name = os.path.basename(self.script_path)
        print(f'Initializing wine-wrapper for "{script_name}"...')

        if prefix_path is None:
            state_dict = get_state()
            if script_name in state_dict:
                prefix_path = state_dict[script_name]['prefix']
                print(' > Using existing script-prefix association')
            else:
                prefix_path = f'{prefix_dir}/WINEPREFIX__{script_name}/'
                print(' > Creating new script-prefix association')

                state_dict[script_name] = {
                    'prefix': prefix_path
                }
                dump_state(state_dict)
        else:
            prefix_path = os.path.abspath(prefix_path)
            print(f' > Using forced prefix')

        self.prefix = PrefixHandler(prefix_path)

    def configure(self) -> None:
        self.prefix._wine('winecfg')
        self.prefix._commit('Configured')

    def execute(self) -> None:
        print(f'Executing {self.script_path}')
        self.prefix._wine(self.script_path)

@click.group()
def main() -> None:
    pass

def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()

@main.command(help='Show current setup.')
def show() -> None:
    state_dict = get_state()

    for script_name, data in sorted(state_dict.items()):
        print(f'--- {script_name} ---')
        for k, v in sorted(data.items()):
            print(f' > {k}: {v}')

@main.command(help='Associate script with given wine-prefix.')
@click.argument('script', type=click.Path(exists=True))
@click.argument('prefix', type=click.Path(exists=False))
def set(script: str, prefix: str) -> None:
    state_dict = get_state()

    script_name = os.path.basename(script)
    if script_name in state_dict:
        state_dict[script_name].update({
            'prefix': os.path.abspath(prefix)
        })
    else:
        state_dict[script_name] = {
            'prefix': os.path.abspath(prefix)
        }

    dump_state(state_dict)

@main.command(help='Clear all associations.')
@click.option(
    '--yes', is_flag=True, expose_value=False, callback=abort_if_false,
    prompt='Are you sure you want to clear all associations?')
def clear():
    print(f'Deleting {state_file}...')
    if os.path.exists(state_file):
        os.remove(state_file)

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
