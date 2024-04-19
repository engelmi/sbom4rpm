# SPDX-License-Identifier: LGPL-2.1-or-later
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import quote

from model import RPMPackage


def to_template_data(
    root_rpm: RPMPackage,
    all_rpms: Dict[str, RPMPackage],
    required_rpms: Dict[str, List[str]],
) -> Dict[str, Any]:

    seen = set()
    packages = []
    to_explore = [root_rpm]
    while to_explore:
        elem = to_explore.pop()
        if elem.Name in seen:
            continue

        requires = []
        if elem.Name in required_rpms:
            for rpm in required_rpms[elem.Name]:
                # workaround:
                # current data has package name instead of uuid in required files
                for uuid, pkg in all_rpms.items():
                    if rpm == pkg.Name:
                        to_explore = [all_rpms[uuid]] + to_explore
                        requires.append(uuid)

        # purl based on: https://github.com/hexpm/specifications/blob/main/package-url.md
        purl = "pkg:supplier"
        if elem.Vendor != "":
            purl = f"{purl}/{quote(elem.Vendor).lower()}"
        purl = f"{purl}/{elem.Name.lower()}@{elem.Version}"

        pkg = {
            "name": elem.Name,
            "uuid": elem.UUID,
            "version": elem.Version,
            "licenses": elem.License,
            "homepage": elem.URL,
            "purl": purl,
            "is_root": elem.UUID == root_rpm.UUID,
            "requires": requires,
        }
        packages.append(pkg)
        seen.add(elem.Name)

    data = {
        "sbom_author": "SBOMs for RPMs",
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "project": {
            "name": root_rpm.Name,
            "version": root_rpm.Version,
            "homepage": root_rpm.URL,
        },
        "packages": packages,
    }

    return data
