import os
import datetime

from typing import Optional

import sh

from .fs_handler import FSHandler
from .utils import prefix_dir


class PrefixHandler:
    def __init__(self, prefix_path: str) -> None:
        self.prefix = prefix_path
        self.master_prefix = f'{prefix_dir}/master_prefix'

        self.fs = FSHandler(self)
        self._setup()

    def __repr__(self) -> str:
        return self.prefix

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

        sh.wine(*args, **kwargs, _env=cmd_env)

    def configure(self, msg: str = '') -> None:
        self._wine('winecfg')

        if msg:
            msg = f' ({msg})'
        self._commit(msg='Configure'+msg)
