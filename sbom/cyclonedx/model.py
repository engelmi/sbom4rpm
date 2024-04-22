# SPDX-License-Identifier: LGPL-2.1-or-later

import uuid
from datetime import datetime
from typing import Any, Dict, List, Tuple

from model import RPMPackage
from sbom.lib.purl import build_purl


def build_component(rpm: RPMPackage) -> Dict:
    return {
        "group": "",
        "name": rpm.Name,
        "version": rpm.Version,
        "purl": build_purl(rpm),
        "bom-ref": build_purl(rpm, mask_name=False),
        "properties": [],
        "type": "library",
        "scope": "required",
    }


def build_dependency(
    rpm: RPMPackage,
    all_rpms: Dict[str, RPMPackage],
    required_rpms: Dict[str, List[str]],
) -> Tuple[Dict, List[RPMPackage]]:
    dependency = {
        "ref": build_purl(rpm, mask_name=False),
        "dependsOn": [],
    }

    rpms = []
    if rpm.Name in required_rpms:
        for required_rpm_name in required_rpms[rpm.Name]:
            # workaround:
            # current data has package name instead of uuid in required files
            for rpm_uuid, pkg in all_rpms.items():
                if required_rpm_name == pkg.Name:
                    dependency["dependsOn"].append(build_purl(rpm, mask_name=False))
                    rpms.append(all_rpms[rpm_uuid])
    return dependency, rpms


def to_template_data(
    root_rpm: RPMPackage,
    all_rpms: Dict[str, RPMPackage],
    required_rpms: Dict[str, List[str]],
    recommended_by_rpms: Dict[str, List[str]],
) -> Dict[str, Any]:
    # Format based on:
    # https://cyclonedx.org/docs/1.5/json/

    result: Dict[str, Any] = dict()

    result["bomFormat"] = "CycloneDX"
    result["specVersion"] = "1.5"
    result["serialNumber"] = f"urn:uuid:{uuid.uuid4()}"
    result["version"] = "1"
    result["metadata"] = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "tools": {
            "components": [
                {
                    "group": "@sbom4rpms",
                    "name": "sbom4rpms",
                    "version": "0.0.1",
                    "type": "applicastion",
                    "author": "SBOM4RPMS",
                    "publisher": "SBOM4RPMS",
                },
            ]
        },
        "authors": [
            {
                "name": "SBOM4RPMS",
            },
        ],
        "lifecycles": [
            {
                "phase": "runtime",
            }
        ],
        "component": {
            "group": "",
            "name": root_rpm.Name,
            "version": root_rpm.Version,
            "purl": build_purl(root_rpm),
            "bom-ref": build_purl(root_rpm, mask_name=False),
            "properties": [],
            "type": "application",
        },
    }
    result["components"] = []
    result["dependencies"] = []

    seen = set()
    to_explore = [root_rpm]
    while to_explore:
        elem = to_explore.pop()
        if elem.Name in seen:
            continue

        result["components"].append(build_component(elem))

        dependency, req_rpms = build_dependency(elem, all_rpms, required_rpms)
        result["dependencies"].append(dependency)

        to_explore = to_explore + req_rpms
        seen.add(elem.Name)

    return result
