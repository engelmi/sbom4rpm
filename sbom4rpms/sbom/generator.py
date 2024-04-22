# SPDX-License-Identifier: LGPL-2.1-or-later

import json
import os
from os.path import join
from typing import Dict, List
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader

from sbom4rpms.command import Command
from sbom4rpms.consts import (
    DIRECTORY_SBOM_DATA,
    FILE_SBOM_TEMPLATE_ROOT,
    SUPPORTED_SBOM_FORMATS,
)
from sbom4rpms.model import GitSubmodule, RPMPackage
from sbom4rpms.sbom.cyclonedx.model import to_template_data as cyclonedx_data
from sbom4rpms.sbom.spdx.model import to_template_data as spdx_data


class SBOMGenerator:

    def __init__(
        self,
        root_rpms: List[RPMPackage],
        required_rpms: Dict[str, List[str]],
        recommended_by_rpms: Dict[str, List[str]],
        all_rpms: Dict[str, RPMPackage],
        git_submodules: List[GitSubmodule],
    ) -> None:
        self.root_rpms = root_rpms
        self.required_rpms = required_rpms
        self.recommended_by_rpms = recommended_by_rpms
        self.all_rpms = all_rpms
        self.git_submodules = git_submodules

    def generate(self, output_dir: str) -> None:
        Command(f"mkdir -p {output_dir}").run()


class SPDXGenerator(SBOMGenerator):

    def __init__(
        self,
        root_rpms: List[RPMPackage],
        required_rpms: Dict[str, List[str]],
        recommended_by_rpms: Dict[str, List[str]],
        all_rpms: Dict[str, RPMPackage],
        git_submodules: List[GitSubmodule],
    ) -> None:
        super().__init__(
            root_rpms, required_rpms, recommended_by_rpms, all_rpms, git_submodules
        )

    def generate(self, output_dir: str) -> None:
        output_dir = join(output_dir, DIRECTORY_SBOM_DATA)
        super().generate(output_dir)

        tmpl = Environment(
            loader=FileSystemLoader(f"{os.path.dirname(__file__)}/spdx/")
        ).get_template(FILE_SBOM_TEMPLATE_ROOT)

        for root_rpm in self.root_rpms:
            data = spdx_data(
                root_rpm,
                self.all_rpms,
                self.required_rpms,
                self.recommended_by_rpms,
                self.git_submodules,
            )
            with open(join(output_dir, quote(root_rpm.Name) + ".spdx"), "w") as f:
                f.write(tmpl.render(data))


class CycloneDXGenerator(SBOMGenerator):

    def __init__(
        self,
        root_rpms: List[RPMPackage],
        required_rpms: Dict[str, List[str]],
        recommended_by_rpms: Dict[str, List[str]],
        all_rpms: Dict[str, RPMPackage],
        git_submodules: List[GitSubmodule],
    ) -> None:
        super().__init__(
            root_rpms, required_rpms, recommended_by_rpms, all_rpms, git_submodules
        )

    def generate(self, output_dir: str) -> None:
        output_dir = join(output_dir, DIRECTORY_SBOM_DATA)
        super().generate(output_dir)

        for root_rpm in self.root_rpms:
            data = cyclonedx_data(
                root_rpm,
                self.all_rpms,
                self.required_rpms,
                self.recommended_by_rpms,
                self.git_submodules,
            )
            with open(
                join(output_dir, quote(root_rpm.Name) + ".cyclonedx.json"), "w"
            ) as f:
                f.write(json.dumps(data, indent=2))


def create_sbom_generator(
    sbom_format: str,
    root_rpms: List[RPMPackage],
    required_rpms: Dict[str, List[str]],
    recommended_by_rpms: Dict[str, List[str]],
    all_rpms: Dict[str, RPMPackage],
    git_submodules: List[GitSubmodule],
) -> SBOMGenerator:
    if sbom_format == SUPPORTED_SBOM_FORMATS[0]:
        return SPDXGenerator(
            root_rpms, required_rpms, recommended_by_rpms, all_rpms, git_submodules
        )
    elif sbom_format == SUPPORTED_SBOM_FORMATS[1]:
        return CycloneDXGenerator(
            root_rpms,
            required_rpms,
            recommended_by_rpms,
            all_rpms,
            git_submodules,
        )

    raise Exception(f"Unknown SBOM format: {sbom_format}")
