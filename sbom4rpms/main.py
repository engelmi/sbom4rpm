#!/usr/bin/python3
# SPDX-License-Identifier: LGPL-2.1-or-later

import argparse
from typing import List

from sbom4rpms.consts import SUPPORTED_SBOM_FORMATS
from sbom4rpms.gitinspect import collect_git_submodules, read_submodule_data
from sbom4rpms.rpminspect import collect_rpm_data, read_rpm_data
from sbom4rpms.sbom.generator import create_sbom_generator


def collect_rpm_dependencies(
    packages: List[str], output_dir: str, explore_depth: int, local_rpm_repo: str
) -> None:
    """
    Collect all RPMs required by the RPMs.
    """
    collect_rpm_data(
        packages=packages,
        out_dir=output_dir,
        explore_depth=explore_depth,
        local_rpm_repo=local_rpm_repo,
    )


def generate_sboms_of_rpms(sbom_dir: str, sbom_format: str) -> None:
    """
    Read all RPMs raw data and transform to SBOM
    """
    root_rpms, required_rpms, recommended_by_rpms, all_rpms = read_rpm_data(sbom_dir)
    git_submodules = read_submodule_data(sbom_dir)

    generator = create_sbom_generator(
        sbom_format,
        root_rpms,
        required_rpms,
        recommended_by_rpms,
        all_rpms,
        git_submodules,
    )
    generator.generate(sbom_dir)


def run(
    packages: List[str],
    local_rpm_repo: str,
    sbom_dir: str,
    sbom_format: str,
    git_dir: str,
    collect_dependencies: bool,
    explore_depth: str,
) -> None:
    if collect_dependencies:
        collect_rpm_dependencies(packages, sbom_dir, explore_depth, local_rpm_repo)
    if git_dir != "":
        collect_git_submodules(git_dir, sbom_dir)
    generate_sboms_of_rpms(sbom_dir, sbom_format)


def arg_parse_check_number(value):
    return int(value)


def setup_argparser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "packages",
        nargs="+",
        help="List of packages to generate an SBOM for",
    )
    parser.add_argument(
        "--local-rpm-repo",
        default="",
        help="Directory containing locally installed RPMs. Useful if a package in 'packages' has a dependency on an RPM in the local repo.",
    )

    parser.add_argument(
        "--sbom-dir",
        required=True,
        help="Base directory for all SBOM file outputs. Collected RPM dependencies are saved here.",
    )
    parser.add_argument(
        "--sbom-format",
        choices=SUPPORTED_SBOM_FORMATS,
        default="spdx",
        help="Desired format of the generated SBOM.",
    )

    parser.add_argument(
        "--git-dir",
        default="",
        help="Directory of the cloned project repository. If set, additional inspections, e.g. for submodules, will be made.",
    )

    parser.add_argument(
        "--collect-dependencies",
        action=argparse.BooleanOptionalAction,
        help="Flag to indicate if dependencies of RPMs in 'rpm-dir' are resolved.",
    )
    parser.add_argument(
        "--explore-depth",
        default=0,
        type=arg_parse_check_number,
        help="The depth of indirect dependencies to explore of the RPMs",
    )


def main():
    parser = argparse.ArgumentParser(description="RPM to SBOM Generator")

    setup_argparser(parser)
    args = parser.parse_args()

    run(
        args.packages,
        args.local_rpm_repo,
        args.sbom_dir,
        args.sbom_format,
        args.git_dir,
        args.collect_dependencies,
        args.explore_depth,
    )


if __name__ == "__main__":
    main()
