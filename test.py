# SPDX-License-Identifier: LGPL-2.1-or-later

import json
import os
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader

from consts import (
    FILE_PATH_ALL_RPMS,
    FILE_PATH_REQUIRED_BY_RPMS,
    FILE_PATH_REQUIRED_RPMS,
    FILE_PATH_ROOT_RPMS,
)
from model import RPMPackage, get_init_data_structures
from rpminspect import collect_rpm_data
from sbom.spdx.model import rpms_to_template_data

rpm_path = "artifacts/rpms-202404041102/"
base_out_dir = "./sboms"

# Collect all RPMs required by the RPMs in root_path (direct and indirect)
# ------------------------------------------------------------------------
#
# root_rpm_names: List[str] = []
# for entry in os.listdir(rpm_path):
#     if entry.endswith(".src.rpm"):
#         # get build dependencies
#         pass
#     elif entry.endswith(".rpm") and "debug" not in entry:
#         root_rpm_names.append(os.path.join(rpm_path, entry))
# collect_rpm_data(root_rpm_names=root_rpm_names, out_dir=raw_data_out_dir)


# Read all RPMs raw data and transform to SBOM
# ------------------------------------------------------------------------
#

root_rpms, required_rpms, required_by_rpms, all_rpms = get_init_data_structures()

all_rpms_file = os.path.join(base_out_dir, FILE_PATH_ALL_RPMS)
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

required_rpms_file = os.path.join(base_out_dir, FILE_PATH_REQUIRED_RPMS)
with open(required_rpms_file, "r") as f:
    content = f.read()
    required_rpms: Dict[str, List[str]] = json.loads(content)

required_by_rpms_file = os.path.join(base_out_dir, FILE_PATH_REQUIRED_BY_RPMS)
with open(required_by_rpms_file, "r") as f:
    content = f.read()
    required_by_rpms: Dict[str, List[str]] = json.loads(content)

root_rpms_file = os.path.join(base_out_dir, FILE_PATH_ROOT_RPMS)
with open(root_rpms_file, "r") as f:
    content = f.read()
    rpms = content.split(", ")
    for rpm in rpms:
        root_rpms.append(all_rpms[rpm.strip()])

data = rpms_to_template_data(root_rpms, all_rpms, required_rpms)

tmpl = Environment(loader=FileSystemLoader("sbom/spdx/")).get_template("document.tmpl")
with open("example", "w") as f:
    f.write(tmpl.render(data))
