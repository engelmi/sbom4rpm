# SPDX-License-Identifier: LGPL-2.1-or-later
from urllib.parse import quote
from datetime import datetime
from typing import Dict, Any, List

from model import RPMPackage


def rpms_to_template_data(root_rpms: List[RPMPackage], all_rpms: Dict[str, RPMPackage], required_rpms: Dict[str, List[str]]) -> Dict[str, Any]:

    seen = set()
    packages = []
    to_explore = [rpm for rpm in root_rpms]
    while to_explore:
        elem = to_explore.pop()
        if elem.Name in seen:
            continue

        contains = []
        if elem.Name in required_rpms:
            for rpm in required_rpms[elem.Name]:
                # workaround:
                # current data has package name instead of uuid in required files
                for uuid, pkg in all_rpms.items():
                    if rpm == pkg.Name:
                        to_explore = [all_rpms[uuid]] + to_explore
                        contains.append(uuid)

        # purl based on: https://github.com/hexpm/specifications/blob/main/package-url.md
        purl = "pkg:supplier"
        if elem.Vendor != "":
            purl = f"{purl}/{elem.Vendor}"
        purl = f"{purl}/{elem.Name}@{elem.Version}"

        pkg = {
            "name": elem.Name,
            "uuid": elem.UUID,
            "version": elem.Version,
            "licenses": elem.License,
            "homepage": elem.URL,
            "purl": quote(purl),
            "is_root": elem.UUID in [rpm.UUID for rpm in root_rpms],
            "contains": contains,
        }
        packages.append(pkg)
        seen.add(elem.Name)

    data = {
        "sbom_author": "Eclipse Committer",
        "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "project": {
            "name": quote("Eclipse BlueChi"),
            "version": "0.8.0",
            "homepage": "https://github.com/eclipse-bluechi/bluechi"
        },
        "packages": packages,
    }

    return data
