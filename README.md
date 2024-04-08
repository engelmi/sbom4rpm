# SBOM for RPM

`SBOM4RPM` uses existing `rpm` and `dnf` features to resolve all dependencies of one or multiple RPM packages and generates an SBOM for each `.rpm`. 

## Usage

Start a container for building the custom RPM project and mount its directory into it. For example:
```bash
podman run -it -v <path-to-project>:/var/<your-project> <build-container> /bin/bash
```

Proceed by building the custom RPM project and create a repomd (xml-based rpm metadata) repository for your output directory:
```bash
# assuming all rpms have been put into '/tmp/custom-artifacts'
createrepo_c /tmp/custom-artifacts
```

Then run `SBOM4RPM`:

```bash
python rpm2sbom.py --rpm-dir=/tmp/custom-artifacts/ --collect-dependencies --sbom-format=spdx --sbom-dir=sboms
```
