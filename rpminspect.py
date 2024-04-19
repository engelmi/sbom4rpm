# SPDX-License-Identifier: LGPL-2.1-or-later

import json
import os
import re
from typing import Dict, List, Set, Tuple, Union

from command import Command
from consts import (
    FILE_PATH_ALL_RPMS,
    FILE_PATH_REQUIRED_BY_RPMS,
    FILE_PATH_REQUIRED_RPMS,
    FILE_PATH_RECOMMENDED_BY_RPMS,
    FILE_PATH_ROOT_RPMS,
    DIRECTORY_RAW_DATA,
)
from model import RPMPackage, get_init_data_structures


def collect_rpm_data(rpm_dir: str, out_dir: str) -> None:
    root_rpms, required_rpms, required_by_rpms, recommended_by_rpms, all_rpms = get_init_data_structures()

    def list_rpms(rpm_dir: str) -> List[str]:
        root_rpm_names: List[str] = []
        for entry in os.listdir(rpm_dir):
            if entry.endswith(".src.rpm"):
                # get build dependencies
                pass
            elif entry.endswith(".rpm") and "debug" not in entry:
                root_rpm_names.append(os.path.join(rpm_dir, entry))
        return root_rpm_names

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

    def whatprovides_package(required_package: str) -> Union[RPMPackage, None]:
        output, _ = Command(f'dnf repoquery --whatprovides "{required_package}"').run()
        lines = output.split("\n")
        if len(lines) <= 0:
            return None

        if lines[0] == "":
            # fallback to local repo and check if it is a dependency between
            # the inspected root rpms
            output, _ = Command(
                f'dnf repoquery --whatprovides "{required_package}" --repo local-rpms --repofrompath local-rpms,file://{rpm_dir}').run()
            lines = output.split("\n")
            if len(lines) <= 0:
                return None

        pkg_name = "-".join(lines[0].split(":")[0].split("-")[:-1])

        if pkg_name not in all_rpms:
            all_rpms[pkg_name] = get_package_info(pkg_name)

        return all_rpms[pkg_name]

    def get_required_packages(dependent_package: str) -> List[RPMPackage]:
        output, _ = Command(f"rpm -qR {dependent_package}").run()

        required_packages: List[RPMPackage] = []
        for line in output.split("\n"):
            if line == "" or line.startswith("/") or line.startswith("rpmlib"):
                continue

            pkg = whatprovides_package(line)

            if pkg is not None and isinstance(pkg, RPMPackage):
                if dependent_package not in required_rpms:
                    required_rpms[dependent_package] = []
                if pkg.Name not in required_rpms[dependent_package]:
                    required_rpms[dependent_package].append(pkg.Name)

                if pkg.Name not in required_by_rpms:
                    required_by_rpms[pkg.Name] = []
                if dependent_package not in required_by_rpms[pkg.Name]:
                    required_by_rpms[pkg.Name].append(dependent_package)

            required_packages.append(pkg)

        return required_packages

    def get_recommended_packages(dependent_package: str) -> List[RPMPackage]:
        output, _ = Command(f"rpm -q --recommends {dependent_package}").run()

        recommended_packages: List[RPMPackage] = []
        for line in output.split("\n"):
            if line == "" or line.startswith("/") or line.startswith("rpmlib"):
                continue

            pkg = whatprovides_package(line)

            if pkg is not None and isinstance(pkg, RPMPackage):
                if pkg.Name not in recommended_by_rpms:
                    recommended_by_rpms[pkg.Name] = []
                if dependent_package not in recommended_by_rpms[pkg.Name]:
                    recommended_by_rpms[pkg.Name].append(dependent_package)

            recommended_packages.append(pkg)

        return recommended_packages

    def output(output_dir: str):
        Command(f"mkdir -p {os.path.join(output_dir, DIRECTORY_RAW_DATA)}").run()

        required_rpms_path = os.path.join(output_dir, FILE_PATH_REQUIRED_RPMS)
        with open(required_rpms_path, "w") as f:
            f.write(json.dumps(required_rpms, indent=2))
            f.flush()

        required_by_rpms_path = os.path.join(output_dir, FILE_PATH_REQUIRED_BY_RPMS)
        with open(required_by_rpms_path, "w") as f:
            f.write(json.dumps(required_by_rpms, indent=2))
            f.flush()

        recommended_by_rpms_path = os.path.join(output_dir, FILE_PATH_RECOMMENDED_BY_RPMS)
        with open(recommended_by_rpms_path, "w") as f:
            f.write(json.dumps(recommended_by_rpms, indent=2))
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

    root_rpm_names = list_rpms(rpm_dir)

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
        for pkg in get_recommended_packages(elem.Name):
            to_explore.append(pkg)

    output(out_dir)


def read_rpm_data(sbom_dir: str) -> Tuple[
    List[RPMPackage],
    Dict[str, List[str]],
    Dict[str, List[str]],
    Dict[str, RPMPackage],
]:
    """
    returns:
    Empty data structures for:
    - root_rpms,
    - required_rpms,
    - recommended_by_rpms,
    - all_rpms
    """
    root_rpms, required_rpms, _, recommended_by_rpms, all_rpms = get_init_data_structures()

    all_rpms_file = os.path.join(sbom_dir, FILE_PATH_ALL_RPMS)
    with open(all_rpms_file, "r") as f:
        content = f.read()

        # split rpm blocks, skip last (empty) block
        rpms = content.split("\n\n")[:-1]

        for rpm in rpms:
            pkg: RPMPackage = RPMPackage.from_string(rpm)
            if pkg.Name == "":
                print(f"Package without name found {pkg.UUID}, skipping...")
                continue
            all_rpms[pkg.UUID] = pkg

        required_rpms_file = os.path.join(sbom_dir, FILE_PATH_REQUIRED_RPMS)
        with open(required_rpms_file, "r") as f:
            content = f.read()
            required_rpms: Dict[str, List[str]] = json.loads(content)

        recommended_by_rpms_file = os.path.join(sbom_dir, FILE_PATH_RECOMMENDED_BY_RPMS)
        with open(recommended_by_rpms_file, "r") as f:
            content = f.read()
            recommended_by_rpms: Dict[str, List[str]] = json.loads(content)

        # required_by_rpms currently not used
        # required_by_rpms_file = os.path.join(sbom_dir, FILE_PATH_REQUIRED_BY_RPMS)
        # with open(required_by_rpms_file, "r") as f:
        #     content = f.read()
        #     required_by_rpms: Dict[str, List[str]] = json.loads(content)

        root_rpms_file = os.path.join(sbom_dir, FILE_PATH_ROOT_RPMS)
        with open(root_rpms_file, "r") as f:
            content = f.read()
            rpms = content.split(", ")
            for rpm in rpms:
                root_rpms.append(all_rpms[rpm.strip()])

    return root_rpms, required_rpms, recommended_by_rpms, all_rpms
