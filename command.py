# SPDX-License-Identifier: LGPL-2.1-or-later

import subprocess
from typing import List, Tuple, Union


class Command:
    """Execute a shell command and capture its output

    Arguments:
      args: A string, or a sequence of program arguments
      shell: If true, then command is executed within shell
    """

    def __init__(self, args: Union[str, List[str]], shell: bool = True) -> None:
        self.args = args
        self.shell = shell

    def run(self, **kwargs) -> Tuple[str, str]:
        """Run the command and return its stdout."""
        process = subprocess.Popen(
            self.args,
            shell=self.shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **kwargs,
        )
        out, err = process.communicate()

        out = out.decode("utf-8")
        err = err.decode("utf-8")

        return out, err
