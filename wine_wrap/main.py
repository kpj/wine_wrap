import os
import json
import shutil
import datetime
import collections

from typing import Dict, Optional

import click

from .wine_wrapper import WineWrapper
from .utils import prefix_dir, state_file, get_state, dump_state, get_prefix_path, get_prefix_name_from_path


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
        prefix_name = get_prefix_name_from_path(data['prefix'])
        tmp_dict[prefix_name].append(script_name)

    for prefix_name, scripts in tmp_dict.items():
        print(f'--- {prefix_name} ---')

        if print_path:
            print(f'Path: "{prefix}"')

        for s in sorted(scripts):
            print(f' > {s}')

@main.command(help='Associate script with given wine-prefix.')
@click.argument('script', type=click.Path(exists=True), metavar='<script path>')
@click.argument('prefix', type=click.Path(exists=False), metavar='<prefix path>')
def set(script: str, prefix: str) -> None:
    state_dict = get_state()

    prefix_path = get_prefix_path(prefix)
    script_name = os.path.basename(script)
    if script_name in state_dict:
        state_dict[script_name].update({
            'prefix': prefix_path
        })
    else:
        state_dict[script_name] = {
            'prefix': prefix_path
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
