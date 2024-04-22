# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import re
from typing import List

from command import Command
from consts import DIRECTORY_RAW_DATA, FILE_PATH_GIT_SUBMODULES
from model import GitSubmodule

MESON_FILE_NAME = "meson.build"


def is_meson_project(submodule_dir: str) -> bool:
    return os.path.isfile(os.path.join(submodule_dir, MESON_FILE_NAME))


def parse_license(submodule_dir: str) -> str:
    if is_meson_project(submodule_dir):
        meson_file = os.path.join(submodule_dir, MESON_FILE_NAME)
        license_pattern = re.compile(".*(license).*['\"](.+)['\"]")
        with open(meson_file, "r") as f:
            meson_content = f.read()
            match = license_pattern.search(meson_content)
            if match is not None:
                return match.groups()[1].strip()

    return ""


def collect_git_submodules(git_dir: str, sbom_dir: str) -> None:

    def collect_submodule_data(project_git_dir: str) -> List[GitSubmodule]:
        submodule_pattern = re.compile("([a-z0-9]+)\s(.+)\s\((.+)\)")
        remote_pattern = re.compile("(origin)[\s]+(.+)[\s]+(\(fetch\))")
        project_name_pattern = re.compile("(.+)\/(.+)\.git")

        submodules: List[GitSubmodule] = []

        output, _ = Command(f"git -C {project_git_dir} submodule").run()
        for line in output.split("\n"):
            match = submodule_pattern.search(line)
            if match is None:
                continue
            m = GitSubmodule()
            m.Git_Hash = match.groups()[0].strip()
            m.Directory = match.groups()[1].strip()
            m.Git_Branch = match.groups()[2].strip()
            submodules.append(m)

        for submodule in submodules:
            module_dir = os.path.join(project_git_dir, submodule.Directory)
            output, _ = Command(f"git -C {module_dir} remote -v").run()
            for line in output.split("\n"):
                match = remote_pattern.search(line)
                if match is not None:
                    submodule.Remote_URL = match.groups()[1].strip()
                    break

            match = project_name_pattern.search(submodule.Remote_URL)
            if match is not None:
                submodule.Name = match.groups()[1].strip()

            submodule.License = parse_license(
                os.path.join(project_git_dir, submodule.Directory)
            )

        return submodules

    def output(output_dir: str, submodules: List[GitSubmodule]):
        Command(f"mkdir -p {os.path.join(output_dir, DIRECTORY_RAW_DATA)}").run()

        submodule_path = os.path.join(output_dir, FILE_PATH_GIT_SUBMODULES)
        with open(submodule_path, "w") as f:
            for submodule in submodules:
                f.write(submodule.serialize())
                f.write("\n\n")
            f.flush()

    submodules = collect_submodule_data(git_dir)
    output(sbom_dir, submodules)


def read_submodule_data(sbom_dir: str) -> List[GitSubmodule]:
    submodule_file = os.path.join(sbom_dir, FILE_PATH_GIT_SUBMODULES)
    if not os.path.isfile(submodule_file):
        return []

    submodules = []
    with open(submodule_file, "r") as f:
        content = f.read()

        # split git submodule blocks, skip last (empty) block
        submodule_blocks = content.split("\n\n")[:-1]

        for submodule_block in submodule_blocks:
            submodules.append(GitSubmodule.from_string(submodule_block))
    return submodules
