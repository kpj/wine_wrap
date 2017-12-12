import os
import io
import sys
import datetime

from types import TracebackType
from typing import Optional, List, Type

import sh

from .fs_handler import FSManager
from .utils import prefix_dir


class PrefixHandler:
    def __init__(self, prefix_path: str) -> None:
        self.fs = FSManager.get_handler(self)

        self.master_prefix = f'{prefix_dir}/master_prefix'
        self.prefix = self._get_prefix_path(prefix_path)

        self._setup()

    def __enter__(self) -> 'PrefixHandler':
        return self

    def __exit__(
        self,
        type: Optional[Type[BaseException]],
        value: Optional[Exception],
        traceback: Optional[TracebackType]
    ) -> None:
        self.fs._on_exit()

    def __repr__(self) -> str:
        return self.prefix

    def _get_prefix_path(self, prefix: str) -> str:
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

    def _setup(self) -> None:
        # check for master-prefix
        if not os.path.exists(self.master_prefix):
            print('Master-prefix does not exist. Creating...')
            self.fs.create_master_prefix(self.master_prefix)
        else:
            print('Using existing master-prefix...')

        # create actual prefix if needed
        if not os.path.exists(self.prefix):
            print('Creating new wine-prefix from master...')
            self.fs.create_prefix_from_master(self.master_prefix, self.prefix)
        else:
            print('Using existing wine-prefix...')

    def _commit(self, msg: str = '', cwd: Optional[str] = None) -> None:
        date_str = datetime.datetime.now()

        # commit changes to current wine-prefix
        self._git('add', '.', cwd=cwd)
        self._git('commit', '-a', m=f'[{date_str}] {msg}', cwd=cwd)

    def _git(
        self,
        *args: str, cwd: Optional[str] = None, **kwargs: str
    ) -> None:
        sh.git(*args, **kwargs, _cwd=cwd or self.prefix)

    def _wine(
        self,
        *args: str, cwd: Optional[str] = None, **kwargs: str
    ) -> None:
        cmd_env = os.environ.copy()
        cmd_env.update({
            'WINEPREFIX': cwd or self.prefix
        })

        sh.wine(
            *args, **kwargs,
            _env=cmd_env, _out=sys.stdout, _err=sys.stderr)

    def _find(self, pattern: str) -> List[str]:
        # TODO: implement in native Python
        reader = io.StringIO()
        sh.find(self.prefix, '-name', pattern, _out=reader)
        result = reader.getvalue()
        return result.split('\n')

    def configure(self, msg: str = '') -> None:
        self._wine('winecfg')

        if msg:
            msg = f' ({msg})'
        self._commit(msg='Configure'+msg)

    def delete(self) -> None:
        self.fs.delete_prefix(self.prefix)

    def scan_for_executables(self) -> List[str]:
        file_list = self._find(r'*.exe')
        cur_pref = f'{self.prefix}/drive_c/'
        return [f[len(cur_pref):] for f in file_list
                if f and not f.startswith(f'{cur_pref}windows')]
