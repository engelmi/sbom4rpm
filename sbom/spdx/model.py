# SPDX-License-Identifier: LGPL-2.1-or-later

from datetime import datetime
from typing import Any, Dict, List

from model import GitSubmodule, RPMPackage
from sbom.lib.purl import build_git_purl, build_rpm_purl


def to_template_data(
    root_rpm: RPMPackage,
    all_rpms: Dict[str, RPMPackage],
    required_rpms: Dict[str, List[str]],
    recommended_by_rpms: Dict[str, List[str]],
    git_submodules: List[GitSubmodule],
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

        recommends = []
        if elem.Name in recommended_by_rpms:
            for rpm in recommended_by_rpms[elem.Name]:
                # workaround:
                # current data has package name instead of uuid in required files
                for uuid, pkg in all_rpms.items():
                    if rpm == pkg.Name:
                        to_explore = [all_rpms[uuid]] + to_explore
                        recommends.append(uuid)

        pkg = {
            "name": elem.Name,
            "uuid": elem.UUID,
            "version": elem.Version,
            "licenses": elem.License,
            "homepage": elem.URL,
            "purl": build_rpm_purl(elem),
            "is_root": elem.UUID == root_rpm.UUID,
            "requires": requires,
            "recommended_by": recommends,
        }
        packages.append(pkg)
        seen.add(elem.Name)

    submodules = []
    for submodule in git_submodules:
        submodules.append(
            {
                "name": submodule.Name,
                "uuid": submodule.UUID,
                "version": submodule.Git_Hash,
                "licenses": submodule.License,
                "homepage": submodule.Remote_URL,
                "purl": build_git_purl(submodule),
            }
        )

    data = {
        "sbom_author": "SBOMs for RPMs",
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "project": {
            "name": root_rpm.Name,
            "version": root_rpm.Version,
            "homepage": root_rpm.URL,
        },
        "packages": packages,
        "submodules": submodules,
    }

    return data
