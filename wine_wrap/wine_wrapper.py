import os

from typing import Optional

from .prefix_handler import PrefixHandler
from .utils import prefix_dir, get_state, dump_state, get_prefix_path


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
            prefix_path = get_prefix_path(prefix_path)
            print(f' > Using forced prefix')

        assert prefix_path is not None
        self.prefix = PrefixHandler(prefix_path)

    def configure(self) -> None:
        self.prefix._wine('winecfg')
        self.prefix._commit('Configured')

    def execute(self) -> None:
        print(f'--- Executing ---')
        print(f'Prefix: "{self.script_path}"')
        print(f'Script: "{self.prefix}"')
        print('------------------')

        self.prefix._wine(self.script_path)
