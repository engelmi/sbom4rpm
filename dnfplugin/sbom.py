import dnf

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
