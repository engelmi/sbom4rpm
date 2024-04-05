# SPDX-License-Identifier: LGPL-2.1-or-later
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

        pkg = {
            "name": elem.Name,
            "uuid": elem.UUID,
            "version": elem.Version,
            "licenses": elem.License,
            "homepage": elem.URL,
        }
        packages.append(pkg)
        seen.add(elem.Name)

        if elem.Name not in required_rpms:
            continue

        for rpm in required_rpms[elem.Name]:

            # workaround:
            # current data has package name instead of uuid in required files
            for uuid, pkg in all_rpms.items():
                if rpm == pkg.Name:
                    to_explore.append(all_rpms[uuid])

    data = {
        "sbom_author": "Eclipse Committer",
        "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "project": {
            "name": "Eclipse BlueChi",
            "version": "v0.8.0",
            "homepage": "https://github.com/eclipse-bluechi/bluechi"
        },
        "packages": packages,
    }

    return data
