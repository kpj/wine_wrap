import os
import shutil

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .prefix_handler import PrefixHandler


class FSHandler:
    def __init__(self, prefix_handler: 'PrefixHandler') -> None:
        self.prefix_handler = prefix_handler

    def create_master_prefix(self, master_prefix_path: str) -> None:
        os.makedirs(master_prefix_path)

        # initialize new wine-prefix
        print(' > Initializing git repository')
        self.prefix_handler._git('init', cwd=master_prefix_path)

        print(' > Booting wine')
        self.prefix_handler._wine('wineboot', cwd=master_prefix_path)

        print(' > Committing changes')
        self.prefix_handler._commit('Initial commit', cwd=master_prefix_path)

    def create_prefix_from_master(
        self, master_prefix: str, prefix: str
    ) -> None:
        shutil.copytree(master_prefix, prefix, symlinks=True)
