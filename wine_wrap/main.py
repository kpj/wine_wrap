import os
import json
import shutil
import datetime
import collections

from typing import Dict, Optional

import click

from .wine_wrapper import WineWrapper
from .utils import prefix_dir, state_file, get_state, dump_state


@click.group()
def main() -> None:
    pass

def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()

@main.command(help='Show current setup.')
@click.option(
    '--print-path', is_flag=True,
    help='Also print location of each prefix.')
def show(print_path: bool) -> None:
    state_dict = get_state()

    tmp_dict = collections.defaultdict(list)
    for script_name, data in sorted(state_dict.items()):
        tmp_dict[data['prefix']].append(script_name)

    for prefix, scripts in tmp_dict.items():
        prefix_name = prefix.split('/')[-2]
        print(f'--- {prefix_name} ---')

        if print_path:
            print(f'Path: "{prefix}"')

        for s in scripts:
            print(f' > {s}')

@main.command(help='Associate script with given wine-prefix.')
@click.argument('script', type=click.Path(exists=True), metavar='<script path>')
@click.argument('prefix', type=click.Path(exists=False), metavar='<prefix path>')
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
@click.option(
    '--delete-prefixes', is_flag=True,
    help='Also delete all prefixes (including master).')
def clear(delete_prefixes: bool) -> None:
    # delete state file
    print(f'Deleting {state_file}...')
    if os.path.exists(state_file):
        os.remove(state_file)

    # delete prefixes if wanted
    if delete_prefixes:
        print(f'Deleting prefixes...')
        for entry in os.scandir(prefix_dir):
            print(f' > {entry.name}')
            shutil.rmtree(entry.path)

@main.command(help='Execute given script in wine-prefix.')
@click.argument('script', type=click.Path(exists=True), metavar='<script path>')
@click.option(
    '-p', '--prefix', default=None, type=click.Path(exists=False),
    help='Force WINEPREFIX to use.')
def run(script: str, prefix: Optional[str]) -> None:
    ww = WineWrapper(script, prefix)
    ww.execute()

if __name__ == '__main__':
    main()
