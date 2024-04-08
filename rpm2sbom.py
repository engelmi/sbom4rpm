#!/usr/bin/python3
# SPDX-License-Identifier: LGPL-2.1-or-later

import argparse
import os
from typing import List

from jinja2 import Environment, FileSystemLoader

from consts import DIRECTORY_NAME_SBOM_SPDX, DIRECTORY_NAME_SBOM_CYCLONEDX
from rpminspect import collect_rpm_data, read_rpm_data
from sbom.spdx.model import rpms_to_template_data

SUPPORTED_SBOM_FORMATS = [DIRECTORY_NAME_SBOM_SPDX, DIRECTORY_NAME_SBOM_CYCLONEDX]


def collect_rpm_dependencies(rpm_dir: str, output_dir: str) -> None:
    """
    Collect all RPMs required by the RPMs in root_path (direct and indirect).
    """
    root_rpm_names: List[str] = []
    for entry in os.listdir(rpm_dir):
        if entry.endswith(".src.rpm"):
            # get build dependencies
            pass
        elif entry.endswith(".rpm") and "debug" not in entry:
            root_rpm_names.append(os.path.join(rpm_dir, entry))
    collect_rpm_data(root_rpm_names=root_rpm_names, out_dir=output_dir)


def generate_sboms(sbom_dir: str, sbom_format: str) -> None:
    """
    Read all RPMs raw data and transform to SBOM
    """
    root_rpms, required_rpms, all_rpms = read_rpm_data(sbom_dir)
    data = rpms_to_template_data(root_rpms, all_rpms, required_rpms)

    tmpl = Environment(loader=FileSystemLoader(f"sbom/{sbom_format}/")).get_template(
        "document.tmpl"
    )
    with open("example", "w") as f:
        f.write(tmpl.render(data))


def run(rpm_dir: str, sbom_dir: str, sbom_format: str, collect_dependencies: bool) -> None:
    if collect_dependencies:
        collect_rpm_dependencies(rpm_dir, sbom_dir)
    generate_sboms(sbom_dir, sbom_format)


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
