# SPDX-License-Identifier: LGPL-2.1-or-later

from os.path import join
from typing import List, Dict
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader

from command import Command
from consts import SUPPORTED_SBOM_FORMATS,  DIRECTORY_SBOM_TEMPLATE_DIR, FILE_SBOM_TEMPLATE_ROOT, DIRECTORY_SBOM_DATA
from model import RPMPackage
from sbom.spdx.model import to_template_data


class SBOMGenerator():

    def __init__(self,
                 root_rpms: List[RPMPackage],
                 required_rpms: Dict[str, List[str]],
                 recommended_by_rpms: Dict[str, List[str]],
                 all_rpms: Dict[str, RPMPackage],) -> None:
        self.root_rpms = root_rpms
        self.required_rpms = required_rpms
        self.recommended_by_rpms = recommended_by_rpms
        self.all_rpms = all_rpms

    def generate(self, output_dir: str) -> None:
        raise Exception("Not implemented!")


class SPDXGenerator(SBOMGenerator):

    def __init__(self, root_rpms: List[RPMPackage], required_rpms: Dict[str, List[str]], recommended_by_rpms: Dict[str, List[str]], all_rpms: Dict[str, RPMPackage]) -> None:
        super().__init__(root_rpms, required_rpms, recommended_by_rpms, all_rpms)

    def generate(self, output_dir: str) -> None:
        tmpl = Environment(
            loader=FileSystemLoader(f"{DIRECTORY_SBOM_TEMPLATE_DIR}/spdx/")
        ).get_template(FILE_SBOM_TEMPLATE_ROOT)

        output_dir = join(output_dir, DIRECTORY_SBOM_DATA)
        Command(f"mkdir -p {output_dir}").run()

        for root_rpm in self.root_rpms:
            data = to_template_data(root_rpm, self.all_rpms, self.required_rpms, self.recommended_by_rpms)
            with open(join(output_dir, quote(root_rpm.Name)+".spdx"), "w") as f:
                f.write(tmpl.render(data))


class CycloneDXGenerator(SBOMGenerator):

    def __init__(self, root_rpms: List[RPMPackage], required_rpms: Dict[str, List[str]], recommended_by_rpms: Dict[str, List[str]], all_rpms: Dict[str, RPMPackage]) -> None:
        super().__init__(root_rpms, required_rpms, recommended_by_rpms, all_rpms)

    def generate(self, output_dir: str) -> None:
        raise Exception("Not implemented!")


def create_sbom_generator(sbom_format: str, root_rpms: List[RPMPackage], required_rpms: Dict[str, List[str]], recommended_by_rpms: Dict[str, List[str]], all_rpms: Dict[str, RPMPackage]) -> SBOMGenerator:
    if sbom_format == SUPPORTED_SBOM_FORMATS[0]:
        return SPDXGenerator(root_rpms, required_rpms, recommended_by_rpms, all_rpms)
    elif sbom_format == SUPPORTED_SBOM_FORMATS[1]:
        return CycloneDXGenerator(root_rpms, required_rpms, recommended_by_rpms, all_rpms)

    raise Exception(f"Unknown SBOM format: {sbom_format}")
