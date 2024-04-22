# SPDX-License-Identifier: LGPL-2.1-or-later

import re
import uuid
from typing import Dict, List, Tuple


class UniqueModule:

    def __init__(self) -> None:
        self.UUID = uuid.uuid4()

    def serialize(self) -> str:
        raise Exception("Not implemented!")


class RPMPackage(UniqueModule):

    def __init__(self) -> None:
        super().__init__()

        self.Name = ""
        self.Version = ""
        self.Release = ""
        self.Architecture = ""
        self.Install_Date = ""
        self.Group = ""
        self.Size = ""
        self.License = ""
        self.Signature = ""
        self.Source_RPM = ""
        self.Build_Date = ""
        self.Build_Host = ""
        self.Packager = ""
        self.Vendor = ""
        self.Summary = ""
        self.URL = ""
        self.Description = ""

    def get_field_names(self) -> List[str]:
        return [k for k in self.__dict__.keys()]

    def serialize(self) -> str:
        return f"""UUID: {self.UUID}
Name: {self.Name}
Version: {self.Version}
Release: {self.Release}
Architecture: {self.Architecture}
Install_Date: {self.Install_Date}
Group: {self.Group}
Size: {self.Size}
License: {self.License}
Signature: {self.Signature}
Source_RPM: {self.Source_RPM}
Build_Date: {self.Build_Date}
Build_Host: {self.Build_Host}
Packager: {self.Packager}
Vendor: {self.Vendor}
Summary: {self.Summary}
URL: {self.URL}
Description: {self.Description}"""

    def from_string(input: str) -> "RPMPackage":
        p = RPMPackage()
        for name in p.get_field_names():
            output_name = name.replace("_", " ")

            # TODO: regex doesn't work for multiline values, e.g. for Description
            pattern = re.compile(f"({output_name}\s*:\s)(.+)")
            match = pattern.search(input)
            if match is not None:
                p.__setattr__(name, match.groups()[1])

        return p


def get_init_data_structures() -> Tuple[
    List[RPMPackage],
    Dict[str, List[str]],
    Dict[str, List[str]],
    Dict[str, List[str]],
    Dict[str, RPMPackage],
]:
    """
    returns:
    Empty data structures for:
    - root_rpms,
    - required_rpms,
    - required_by_rpms,
    - recommended_by_rpms,
    - all_rpms
    """
    # List of RPMs in artifact directory triggering the inspection process
    root_rpms: List[RPMPackage] = []
    # Key: Name of RPM Package, Value: List of package names directly required by key package
    required_rpms: Dict[str, List[str]] = dict()
    # Key: Name of RPM Package, Value: List of package names directly requiring key package
    required_by_rpms: Dict[str, List[str]] = dict()
    # Key: Name of RPM Package, Value: List of package names directly recommending key package
    recommended_by_rpms: Dict[str, List[str]] = dict()
    # Key: Name of RPM Package, Value: RPMPackage instance
    all_rpms: Dict[str, RPMPackage] = dict()

    return root_rpms, required_rpms, required_by_rpms, recommended_by_rpms, all_rpms


class GitSubmodule(UniqueModule):

    def __init__(self) -> None:
        super().__init__()

        self.Name = ""
        self.Directory = ""
        self.Remote_URL = ""
        self.Git_Hash = ""
        self.Git_Branch = ""
        self.License = ""

    def get_field_names(self) -> List[str]:
        return [k for k in self.__dict__.keys()]

    def serialize(self) -> str:
        return f"""UUID: {self.UUID}
Name: {self.Name}
Directory: {self.Directory}
Remote URL: {self.Remote_URL}
Git Hash: {self.Git_Hash}
Git Branch: {self.Git_Branch}
License: {self.License}
"""

    def from_string(input: str) -> "GitSubmodule":
        p = GitSubmodule()
        for name in p.get_field_names():
            output_name = name.replace("_", " ")

            # TODO: regex doesn't work for multiline values, e.g. for Description
            pattern = re.compile(f"({output_name}\s*:\s)(.+)")
            match = pattern.search(input)
            if match is not None:
                p.__setattr__(name, match.groups()[1])

        return p
