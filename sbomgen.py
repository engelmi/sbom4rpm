from os.path import join
from typing import List, Dict
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader

from command import Command
from consts import DIRECTORY_SBOM_TEMPLATE_DIR, FILE_SBOM_TEMPLATE_ROOT, DIRECTORY_SBOM_DATA
from model import RPMPackage
from sbom.spdx.model import to_template_data


def generate_sboms(
    sbom_dir: str,
    sbom_format: str,
    root_rpms: List[RPMPackage],
    required_rpms: Dict[str, List[str]],
    recommended_rpms: Dict[str, List[str]],
    all_rpms: Dict[str, RPMPackage],
) -> None:
    tmpl = Environment(
        loader=FileSystemLoader(f"{DIRECTORY_SBOM_TEMPLATE_DIR}/{sbom_format}/")
    ).get_template(FILE_SBOM_TEMPLATE_ROOT)

    output_dir = join(sbom_dir, DIRECTORY_SBOM_DATA)
    Command(f"mkdir -p {output_dir}").run()

    for root_rpm in root_rpms:
        data = to_template_data(root_rpm, all_rpms, required_rpms, recommended_rpms)
        with open(join(output_dir, quote(root_rpm.Name)), "w") as f:
            f.write(tmpl.render(data))
