# SBOM for RPMs example

[BlueChi](https://github.com/eclipse-bluechi/bluechi/) will be used as an example project for which SBOMs are generated. 

First, lets start the BlueChi build container and use `/var` as root directory for the following commands:
```bash
podman run -it quay.io/bluechi/build-base:latest /bin/bash
cd /var
```

Inside the container, clone the BlueChi and SBOM4RPMs repo:
```bash
git clone https://github.com/engelmi/sbom4rpm.git
git clone https://github.com/eclipse-bluechi/bluechi.git --recurse-submodules
```

Build the BlueChi RPMs, use that directory as dnf repo and install the built RPMs:
```bash
cd bluechi
make rpm
createrepo_c artifacts/rpms-<datetime>

# required by bluechi
dnf install python3-dasbus -y
dnf install --repo bluechi-rpms \
        --repofrompath bluechi-rpms,file:///var/bluechi/artifacts/rpms-<time>/ \
        --nogpgcheck \
        --nodocs \
        bluechi-controller \
        bluechi-agent \
        bluechi-ctl \
        bluechi-selinux \
        python3-bluechi \
        -y
```

Move to the SBOM4RPMs repo and generate the SBOMs:
```bash
cd ../sbom4rpm
pip3 install -r requirements.txt

# ! This will take quite a while !
# SBOM4RPMs will use all root rpms in
#   /var/bluechi/artifacts/rpms-<datetime>
# and save the collected RPM data in
#   /var/sbom-for-rpms/sboms/raw
# and generate the SBOM data in SPDX format in
#   /var/sbom-for-rpms/sboms/sboms 
python3 rpm2sbom.py \
    --rpm-dir=../bluechi/artifacts/rpms-<datetime>/ \
    --collect-dependencies \
    --sbom-format=spdx \
    --sbom-dir=bluechi-sboms \
```
