import os
from configparser import ConfigParser

import dnf
from dnfpluginscore import logger

from sbom4rpms import main as sbom4rpms


@dnf.plugin.register_command
class SBOMCommand(dnf.cli.Command):
    aliases = ("sbom",)
    summary = "Command for generating an SBOM for an RPM"

    @staticmethod
    def set_argparser(parser):
        sbom4rpms.setup_argparser(parser)

    def run(self):

        sbom4rpms.run(
            self.opts.packages,
            self.opts.local_rpm_repo,
            self.opts.sbom_dir,
            self.opts.sbom_format,
            self.opts.git_dir,
            self.opts.collect_dependencies,
            self.opts.explore_depth,
        )


def parse_config(config_file):
    conf = ConfigParser()
    conf.read(config_file)
    main = {"enabled": 0}

    if not conf.has_section("main"):
        raise KeyError("Missing section 'main'")
    if conf.has_option("main", "enabled"):
        main["enabled"] = conf.get("main", "enabled") == "true"

    return main


class SBOMCollector(dnf.Plugin):

    def __init__(self, base, cli):
        super(SBOMCollector, self).__init__(base, cli)
        self.base = base
        self.logger = logger
        self.conf = {}

    def pre_config(self):
        config_path = self.base.conf.pluginconfpath[0]
        default_config_file = os.path.join(config_path, "sbom.conf")

        if not os.path.isfile(default_config_file):
            return

        self.conf = parse_config(default_config_file)

    def resolved(self):
        if not self.conf["enabled"]:
            return

        for pkg in list(self.base.transaction.install_set):
            self.logger.info(f"{pkg}")
