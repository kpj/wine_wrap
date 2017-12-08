import os
import shutil
import datetime

from typing import Optional

import sh

from .utils import prefix_dir


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

        print(' > Committing changes')
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
