# SPDX-License-Identifier: LGPL-2.1-or-later

from urllib.parse import quote_plus

from model import RPMPackage


def build_purl(rpm: RPMPackage, mask_name=True):
    # purl based on: https://github.com/package-url/purl-spec/blob/master/PURL-TYPES.rst#rpm
    purl = "pkg:rpm"

    vendor_and_name = ""
    if rpm.Vendor != "":
        vendor_and_name = f"{rpm.Vendor.lower()}/{rpm.Name}"
    else:
        vendor_and_name = rpm.Name

    if mask_name:
        vendor_and_name = quote_plus(vendor_and_name)

    return (
        f"{purl}/{vendor_and_name}@{rpm.Version}-{rpm.Release}?arch={rpm.Architecture}"
    )
