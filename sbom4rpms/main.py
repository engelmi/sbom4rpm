#!/usr/bin/python3
# SPDX-License-Identifier: LGPL-2.1-or-later

import argparse

from sbom4rpms.consts import SUPPORTED_SBOM_FORMATS
from sbom4rpms.gitinspect import collect_git_submodules, read_submodule_data
from sbom4rpms.rpminspect import collect_rpm_data, read_rpm_data
from sbom4rpms.sbom.generator import create_sbom_generator


def collect_rpm_dependencies(rpm_dir: str, output_dir: str, explore_depth: int) -> None:
    """
    Collect all RPMs required by the RPMs in root_path (direct and indirect).
    """
    collect_rpm_data(rpm_dir=rpm_dir, out_dir=output_dir, explore_depth=explore_depth)


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
    sbom_dir: str,
    sbom_format: str,
    git_dir: str,
    rpm_dir: str,
    collect_dependencies: bool,
    explore_depth: str,
) -> None:
    if collect_dependencies:
        collect_rpm_dependencies(rpm_dir, sbom_dir, explore_depth)
    if git_dir != "":
        collect_git_submodules(git_dir, sbom_dir)
    generate_sboms_of_rpms(sbom_dir, sbom_format)


def arg_parse_check_number(value):
    return int(value)


def main():
    parser = argparse.ArgumentParser(description="RPM to SBOM Generator")

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
        "--rpm-dir",
        required=True,
        help="Root directory containing RPMs to inspect.",
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

    args = parser.parse_args()
    run(
        args.sbom_dir,
        args.sbom_format,
        args.git_dir,
        args.rpm_dir,
        args.collect_dependencies,
        args.explore_depth,
    )


if __name__ == "__main__":
    main()
