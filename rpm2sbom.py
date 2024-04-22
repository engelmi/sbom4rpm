#!/usr/bin/python3
# SPDX-License-Identifier: LGPL-2.1-or-later

import argparse

from consts import SUPPORTED_SBOM_FORMATS
from rpminspect import collect_rpm_data, read_rpm_data
from sbom.generator import create_sbom_generator


def collect_rpm_dependencies(rpm_dir: str, output_dir: str) -> None:
    """
    Collect all RPMs required by the RPMs in root_path (direct and indirect).
    """
    collect_rpm_data(rpm_dir=rpm_dir, out_dir=output_dir)


def generate_sboms_of_rpms(sbom_dir: str, sbom_format: str) -> None:
    """
    Read all RPMs raw data and transform to SBOM
    """
    root_rpms, required_rpms, recommended_by_rpms, all_rpms = read_rpm_data(sbom_dir)
    generator = create_sbom_generator(
        sbom_format, root_rpms, required_rpms, recommended_by_rpms, all_rpms
    )
    generator.generate(sbom_dir)


def run(
    rpm_dir: str, sbom_dir: str, sbom_format: str, collect_dependencies: bool
) -> None:
    if collect_dependencies:
        collect_rpm_dependencies(rpm_dir, sbom_dir)
    generate_sboms_of_rpms(sbom_dir, sbom_format)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RPM to SBOM Generator")
    parser.add_argument(
        "--rpm-dir",
        default="artifacts",
        help="Root directory containing RPMs to inspect.",
    )
    parser.add_argument(
        "--sbom-dir",
        default="sboms",
        help="Base directory for all SBOM file outputs. Collected RPM dependencies are saved here.",
    )
    parser.add_argument(
        "--sbom-format",
        choices=SUPPORTED_SBOM_FORMATS,
        default="spdx",
        help="Desired format of the generated SBOM.",
    )
    parser.add_argument(
        "--collect-dependencies",
        action=argparse.BooleanOptionalAction,
        help="Flag to indicate if dependencies of RPMs in 'rpm-dir' are resolved.",
    )

    args = parser.parse_args()
    run(args.rpm_dir, args.sbom_dir, args.sbom_format, args.collect_dependencies)
