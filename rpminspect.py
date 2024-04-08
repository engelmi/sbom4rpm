# SPDX-License-Identifier: LGPL-2.1-or-later

import json
import os
import re
from typing import List, Set, Tuple, Union

from command import Command
from consts import (
    FILE_PATH_ALL_RPMS,
    FILE_PATH_REQUIRED_BY_RPMS,
    FILE_PATH_REQUIRED_RPMS,
    FILE_PATH_ROOT_RPMS,
)
from model import RPMPackage, get_init_data_structures


def collect_rpm_data(root_rpm_names: List[str], out_dir: str):
    root_rpms, required_rpms, required_by_rpms, all_rpms = get_init_data_structures()

    def get_builddep_of_srpm(srpm_path: str) -> List[Tuple[str, str]]:
        output, _ = Command(f"dnf builddep --assumeno {srpm_path}").run()

        # We need the package to be already installed in order to query
        # package information later on
        pattern_already_installed = re.compile(
            "(Package )(.+)( is already installed.)", re.MULTILINE | re.UNICODE
        )

        pattern_get_released = re.compile("(\-[0-9\.\-]+\..+\.)", re.UNICODE)

        def extract_name_and_arch(package: str) -> Tuple[str, str]:
            match = pattern_get_released.search(package)
            if match is None:
                return None
            start, end = match.span()
            return (package[:start], package[end:])

        def extract_already_installed(input: str):
            packages = []
            match = pattern_already_installed.search(input)
            while match is not None:
                packages.append(extract_name_and_arch(match.groups()[1].strip()))
                match = pattern_already_installed.search(input, pos=match.span()[1])
            return packages

        return extract_already_installed(output)

    def get_package_info(package: str) -> RPMPackage:
        output, _ = Command(f"rpm -qi {package}").run()
        return RPMPackage.from_string(output)

    def get_required_packages(dependent_package: str) -> List[RPMPackage]:

        def resolve_required_package(pkg: str) -> Union[RPMPackage, None]:
            output, _ = Command(f'dnf repoquery --whatprovides "{pkg}"').run()
            lines = output.split("\n")
            if len(lines) <= 0:
                return None
            pkg_name = "-".join(lines[0].split(":")[0].split("-")[:-1])

            if pkg_name not in all_rpms:
                all_rpms[pkg_name] = get_package_info(pkg_name)

            if dependent_package not in required_rpms:
                required_rpms[dependent_package] = []
            if pkg_name not in required_rpms[dependent_package]:
                required_rpms[dependent_package].append(pkg_name)

            if pkg_name not in required_by_rpms:
                required_by_rpms[pkg_name] = []
            if dependent_package not in required_by_rpms[pkg_name]:
                required_by_rpms[pkg_name].append(dependent_package)

            return all_rpms[pkg_name]

        output, _ = Command(f"rpm -qR {dependent_package}").run()

        required_packages: List[RPMPackage] = []
        for line in output.split("\n"):
            if line == "" or line.startswith("/") or line.startswith("rpmlib"):
                continue

            pkg = resolve_required_package(line)
            required_packages.append(pkg)

        return required_packages

    def output(output_dir: str):
        Command(f"mkdir -p {output_dir}").run()

        required_rpms_path = os.path.join(output_dir, FILE_PATH_REQUIRED_RPMS)
        with open(required_rpms_path, "w") as f:
            f.write(json.dumps(required_rpms, indent=2))
            f.flush()

        required_by_rpms_path = os.path.join(output_dir, FILE_PATH_REQUIRED_BY_RPMS)
        with open(required_by_rpms_path, "w") as f:
            f.write(json.dumps(required_by_rpms, indent=2))
            f.flush()

        root_rpms_path = os.path.join(output_dir, FILE_PATH_ROOT_RPMS)
        with open(root_rpms_path, "w") as f:
            f.write(", ".join([str(root_rpm.UUID) for root_rpm in root_rpms]))
            f.flush()

        all_rpms_path = os.path.join(output_dir, FILE_PATH_ALL_RPMS)
        with open(all_rpms_path, "w") as f:
            for _, rpm in all_rpms.items():
                f.write(rpm.serialize())
                f.write("\n\n")
            f.flush()

    for root_rpm_name in root_rpm_names:
        p = get_package_info(root_rpm_name)
        all_rpms[p.Name] = p
        root_rpms.append(p)

    already_explored: Set = set()
    to_explore = [rpm for rpm in root_rpms]
    while to_explore:
        elem = to_explore.pop()

        if elem.Name in already_explored:
            print(f"{elem.Name} already explored, skipping...")
            continue
        already_explored.add(elem.Name)
        print(f"exploring {elem.Name}...")

        for pkg in get_required_packages(elem.Name):
            to_explore.append(pkg)

    output(out_dir)
