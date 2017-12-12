import os
import collections

from typing import Dict, List, Optional

import click

from .wine_wrapper import WineWrapper
from .prefix_handler import PrefixHandler
from .utils import prefix_dir, state_file, get_state, dump_state, get_prefix_name_from_path


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
@click.argument('script', type=click.Path(exists=False), metavar='<script path>')
@click.argument('prefix', type=click.Path(exists=False), metavar='<prefix>')
def set(script: str, prefix: str) -> None:
    state_dict = get_state()

    with PrefixHandler(prefix) as ph:
        prefix_path = ph.prefix

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

@main.command(help='Scan for executables in given prefix.')
@click.argument('prefix', type=click.Path(exists=False), metavar='<prefix>')
def scan(prefix: str) -> None:
    with PrefixHandler(prefix) as ph:
        exec_list = ph.scan_for_executables()

    print('Found files:')
    for fpath in exec_list:
        print(f' > "{fpath}"')

@main.command(help='Associate script with given wine-prefix.')
@click.argument('prefix', type=click.Path(exists=False), metavar='<prefix>')
@click.option(
    '-m', '--message', default='',
    help='Specify commit-message for this configuration step.')
def configure(prefix: str, message: str) -> None:
    with PrefixHandler(prefix) as ph:
        ph.configure(msg=message)

@main.command(help='Clear all associations.')
@click.option(
    '--yes', is_flag=True, expose_value=False, callback=abort_if_false,
    prompt='Are you sure you want to clear your associations?')
@click.option(
    '-p', '--prefix', multiple=True,
    help='Delete information related to this prefix.')
@click.option(
    '--delete-prefixes', is_flag=True,
    help='Also delete all prefixes (including master).')
def clear(prefix: List[str], delete_prefixes: bool) -> None:
    def get_prefix_path(p: str) -> str:
        with PrefixHandler(p) as ph:
            return ph.prefix

    state_dict = get_state()
    prefixes_to_rm = list(map(get_prefix_path, prefix)) or list(map(lambda x: x['prefix'], state_dict.values()))

    # delete associations
    print(f'Deleting associations...')
    for script_name, data in list(state_dict.items()):
        if data['prefix'] in prefixes_to_rm:
            print(f' > {script_name}:{data["prefix"]}')
            del state_dict[script_name]

    dump_state(state_dict)

    # delete prefixes if wanted
    if delete_prefixes:
        print(f'Deleting prefixes...')
        for entry in prefixes_to_rm:
            print(f' > {get_prefix_name_from_path(entry)}')

            with PrefixHandler(entry) as ph:
                ph.delete()

@main.command(help='Execute given script in wine-prefix.')
@click.argument('script', type=click.Path(exists=False), metavar='<script path>')
@click.option(
    '-p', '--prefix', default=None, type=click.Path(exists=False),
    help='Force WINEPREFIX to use.')
@click.option(
    '-n', '--name', default=None,
    help='Set prefix-name.')
@click.option(
    '-c', '--configure', is_flag=True,
    help='Run winecfg before executing command.')
def run(
    script: str, prefix: Optional[str], name: Optional[str], configure: bool
) -> None:
    if prefix is not None and name is not None:
        print('You can either specify a path or set a name, but not both.')
        exit(-1)

    prefix_spec = {
        'path': prefix,
        'name': name
    }

    with WineWrapper(script, prefix_spec) as ww:
        if configure:
            print('Running winecfg before script execution...')
            ww.prefix.configure()
        ww.execute()

if __name__ == '__main__':
    main()
