import pathlib
from dataclasses import dataclass
from typing import DefaultDict, Iterable, Optional, Sequence

import dacite
from pysen import process_utils
from pysen.command import CommandBase, check_command_installed
from pysen.component import ComponentBase, LintComponentBase, RunOptions
from pysen.error_lines import parse_error_diffs
from pysen.exceptions import UnexpectedErrorFormat
from pysen.lint_command import LintCommandBase
from pysen.path import PathLikeType, change_dir
from pysen.plugin import PluginBase
from pysen.pyproject_model import Config, PluginConfig
from pysen.reporter import Reporter
from pysen.runner_options import PathContext
from pysen.setting import SettingBase, SettingFile
from pysen.source import PythonFileFilter, Source


class AutoflakeCommand(LintCommandBase):
    def __init__(
        self,
        name: str,
        paths: PathContext,
        source: Source,
        setting: "AutoflakeSetting",
        in_place: bool,
    ) -> None:
        super().__init__(paths.base_dir, source)
        self._name = name
        self._setting = setting
        self._in_place = in_place

    @property
    def name(self) -> str:
        return self._name

    def __call__(self, reporter: Reporter) -> int:
        sources = self._get_sources(reporter, PythonFileFilter)
        reporter.logger.info(f"Checking {len(sources)} files")
        return self._run(reporter, self.base_dir, self._setting, sources)

    def _run(
        self,
        reporter: Reporter,
        base_dir: pathlib.Path,
        setting: "AutoflakeSetting",
        sources: Iterable[pathlib.Path],
    ) -> int:
        check_command_installed("autoflake", "--version")

        targets = [str(d) for d in sources]
        if len(targets) == 0:
            return 0

        cmd = ["autoflake"]
        if self._in_place:
            cmd += ["--in-place"]

        if setting.imports:
            cmd += ["--imports", ",".join(setting.imports)]

        if setting.expand_star_imports:
            cmd += ["--expand-star-imports"]

        if setting.remove_unused_variables:
            cmd += ["--remove-unused-variables"]

        if setting.ignore_init_module_imports:
            cmd += ["--ignore-init-module-imports"]

        if setting.remove_duplicate_keys:
            cmd += ["--remove-duplicate-keys"]

        if setting.remove_all_unused_imports:
            cmd += ["--remove-all-unused-imports"]

        cmd += targets

        with change_dir(base_dir):
            ret, stdout, _ = process_utils.run(cmd, reporter)

        diagnostics = parse_error_diffs(stdout, self._parse_file_path, logger=reporter.logger)
        reporter.report_diagnostics(list(diagnostics))
        return ret

    def _parse_file_path(self, file_path: str) -> pathlib.Path:
        before_prefix = "original/"
        after_prefix = "fixed/"
        if file_path.startswith(before_prefix):
            return pathlib.Path(pathlib.Path(file_path.replace(before_prefix, "")))
        elif file_path.startswith(after_prefix):
            return pathlib.Path(pathlib.Path(file_path.replace(after_prefix, "")))
        else:
            raise UnexpectedErrorFormat(file_path)


class Autoflake(LintComponentBase):
    def __init__(
        self,
        name: str = "autoflake",
        setting: Optional["AutoflakeSetting"] = None,
        source: Optional[Source] = None,
    ) -> None:
        super().__init__(name, source)
        self._setting = setting or AutoflakeSetting.default()

    @property
    def name(self) -> str:
        return self._name

    @property
    def setting(self) -> "AutoflakeSetting":
        return self._setting

    @setting.setter
    def setting(self, value: "AutoflakeSetting") -> None:
        self._setting = value

    def export_setting(
        self,
        paths: PathContext,
        files: DefaultDict[str, SettingFile],
    ) -> None:
        print(f"Called export_setting at {self._name}: do nothing")

    @property
    def targets(self) -> Sequence[str]:
        return ["lint", "format"]

    def create_command(self, target: str, paths: PathContext, options: RunOptions) -> CommandBase:
        if target == "lint":
            return AutoflakeCommand(self.name, paths, self.source, self.setting, False)
        elif target == "format":
            return AutoflakeCommand(self.name, paths, self.source, self.setting, True)

        raise AssertionError(f"unknown {target}")


@dataclass
class AutoflakeSetting(SettingBase):
    includes: Optional[Sequence[PathLikeType]] = None
    excludes: Optional[Sequence[PathLikeType]] = None
    include_globs: Optional[Sequence[PathLikeType]] = None
    exclude_globs: Optional[Sequence[PathLikeType]] = None
    imports: Optional[Sequence[str]] = None
    expand_star_imports: bool = False
    remove_unused_variables: bool = False
    ignore_init_module_imports: bool = False
    remove_duplicate_keys: bool = False
    remove_all_unused_imports: bool = False

    @staticmethod
    def default() -> "AutoflakeSetting":
        return AutoflakeSetting()


class AutoflakePlugin(PluginBase):
    def load(
        self, file_path: pathlib.Path, config_data: PluginConfig, root: Config
    ) -> Sequence[ComponentBase]:
        assert config_data.config is not None, f"{config_data.location}.config must be not None"
        config = dacite.from_dict(AutoflakeSetting, config_data.config, dacite.Config(strict=True))
        source = Source(
            config.includes, config.excludes, config.include_globs, config.exclude_globs
        )
        return [Autoflake(setting=config, source=source)]


# NOTE(igarashi): This is the entry point of a plugin method
def plugin() -> PluginBase:
    return AutoflakePlugin()
