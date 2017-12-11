import os
import io
import shutil
import getpass
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

import sh

if TYPE_CHECKING:
    from .prefix_handler import PrefixHandler

from .utils import prefix_dir, get_prefix_name_from_path


BTRFS_COMMANDS = ['btrfs', 'mkfs.btrfs', 'truncate', 'losetup']

class BaseHandler(ABC):
    def __init__(self, prefix_handler: 'PrefixHandler') -> None:
        self.prefix_handler = prefix_handler

    @abstractmethod
    def _on_exit(self) -> None:
        pass

    @abstractmethod
    def create_master_prefix(self, master_prefix_path: str) -> None:
        pass

    @abstractmethod
    def create_prefix_from_master(
        self, master_prefix: str, prefix: str
    ) -> None:
        pass

    @abstractmethod
    def delete_prefix(self, prefix: str) -> None:
        pass

class RAWFS_Handler(BaseHandler):
    def _on_exit(self) -> None:
        pass

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

    def delete_prefix(self, prefix: str) -> None:
        shutil.rmtree(prefix)

class BTRFS_Handler(BaseHandler):
    # TODO: handle permissions correctly

    def __init__(self, prefix_handler: 'PrefixHandler') -> None:
        BaseHandler.__init__(self, prefix_handler)

        self.prefix_image_path = f'{prefix_dir}/../prefix_data.img'
        self._setup_image_file(self.prefix_image_path)

        # mount image file
        print(' > Mount image')
        with sh.contrib.sudo:
            sh.mount(self.prefix_image_path, prefix_dir)

    def _on_exit(self) -> None:
        print(' > Unmounting prefix-directory')
        with sh.contrib.sudo:
            sh.umount(prefix_dir)

    def _setup_image_file(self, prefix_image_path: str) -> None:
        if not os.path.exists(prefix_image_path):
            print('Creating BTRFS-image...')

            # create image file
            print(' > Create image-file')
            sh.truncate(prefix_image_path, s='10G')

            # install BTRFS
            print(' > Install BTRFS')
            reader = io.StringIO()
            with sh.contrib.sudo:
                sh.losetup('--show', '--find', prefix_image_path, _out=reader)

            device = reader.getvalue().strip()
            print(f'  > Using device "{device}"')
            with sh.contrib.sudo:
                sh.Command('mkfs.btrfs')(f=device)
        else:
            print('Use existing BTRFS-image...')

    def create_master_prefix(self, master_prefix_path: str) -> None:
        # create master-prefix subvolume
        if not os.path.exists(master_prefix_path):
            print(' > Create master-prefix subvolume')
            master_prefix_name = os.path.basename(master_prefix_path)
            with sh.contrib.sudo:
                sh.btrfs.subvolume.create(master_prefix_name, _cwd=prefix_dir)
            assert os.path.exists(master_prefix_path), \
                f'"{master_prefix_path}" does not exist'
        else:
            print(' > Use existing master-prefix subvolume')

        print(' > Set owner to current user')
        with sh.contrib.sudo:
            sh.chown(f'{getpass.getuser()}:users', master_prefix_path)

        # boot wine in master-prefix subvolume
        print(' > Initializing git repository')
        self.prefix_handler._git('init', cwd=master_prefix_path)

        print(' > Booting wine')
        self.prefix_handler._wine('wineboot', cwd=master_prefix_path)

        print(' > Committing changes')
        self.prefix_handler._commit('Initial commit', cwd=master_prefix_path)

    def create_prefix_from_master(
        self, master_prefix: str, prefix: str
    ) -> None:
        master_prefix_name = get_prefix_name_from_path(master_prefix)
        prefix_name = get_prefix_name_from_path(prefix)

        print(' > Creating prefix snapshot')
        with sh.contrib.sudo:
            sh.btrfs.subvolume.snapshot(
                master_prefix_name, prefix_name, _cwd=prefix_dir)

        assert os.path.exists(prefix), \
            f'"{prefix}" does not exist'

        print(' > Set owner to current user')
        with sh.contrib.sudo:
            sh.chown(f'{getpass.getuser()}:users', prefix)

    def delete_prefix(self, prefix: str) -> None:
        prefix_name = get_prefix_name_from_path(prefix)
        with sh.contrib.sudo:
            sh.btrfs.subvolume.delete(prefix_name, _cwd=prefix_dir)

class FSManager:
    @staticmethod
    def _can_use_btrfs() -> bool:
        print('Checking for BTRFS support...')

        missing = False
        for cmd in BTRFS_COMMANDS:
            try:
                sh.Command(cmd)
            except sh.CommandNotFound:
                missing = True
                print(f' > Missing: "{cmd}"')

        return not missing

    @staticmethod
    def get_handler(prefix_handler: 'PrefixHandler'):
        if FSManager._can_use_btrfs():
            print('>>> Using BTRFS image to store prefixes <<<')
            return BTRFS_Handler(prefix_handler)
        else:
            print('>>> Storing prefixes normally <<<')
            return RAWFS_Handler(prefix_handler)
