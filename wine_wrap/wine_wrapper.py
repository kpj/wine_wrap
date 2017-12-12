import os

from types import TracebackType
from typing import Dict, Optional, Type

import sh

from .prefix_handler import PrefixHandler
from .utils import prefix_dir, get_state, dump_state


class WineWrapper:
    def __init__(
        self,
        script_path: str, prefix_spec: Dict[str, Optional[str]] = None
    ) -> None:
        script_name = os.path.basename(script_path)
        print(f'Initializing wine-wrapper for "{script_name}"...')

        prefix_path = prefix_spec['path']
        prefix_name = prefix_spec['name']

        if prefix_path is None:
            state_dict = get_state()
            if script_name in state_dict:
                prefix_path = state_dict[script_name]['prefix']

                msg_app = f' (ignoring name "{prefix_name}", clear association if you want to set a new name)' if prefix_name is not None else ''
                print(' > Using existing script-prefix association' + msg_app)
            else:
                prefix_path = f'{prefix_dir}/{prefix_name or script_name}/'
                print(' > Creating new script-prefix association')

                state_dict[script_name] = {
                    'prefix': os.path.abspath(prefix_path)
                }
                dump_state(state_dict)
        else:
            assert prefix_name is None
            print(f' > Using forced prefix')

        # setup prefix-handler
        assert prefix_path is not None
        self.prefix = PrefixHandler(prefix_path)

        # find script-path
        if os.path.exists(script_path):
            self.script_path = os.path.abspath(script_path)
        else:  # assumed to exist in wine-prefix
            print('Assuming script exists in associated wine-prefix...')
            self.script_path = f'{self.prefix.prefix}/drive_c/{script_path}'

        if not os.path.exists(self.script_path):
            raise RuntimeError(
                f'Script "{self.script_path}" could not be found...')

    def __enter__(self) -> 'WineWrapper':
        return self

    def __exit__(
        self,
        type_: Optional[Type[BaseException]],
        value: Optional[Exception],
        traceback: Optional[TracebackType]
    ) -> None:
        self.prefix.__exit__(type_, value, traceback)

    def execute(self) -> None:
        print(f'--- Executing ---')
        print(f'Prefix: "{self.prefix}"')
        print(f'Script: "{self.script_path}"')
        print('------------------')

        try:
            self.prefix._wine(self.script_path)
        except sh.ErrorReturnCode as e:
            print(f'Wine exited with {e.exit_code}')
            raise
