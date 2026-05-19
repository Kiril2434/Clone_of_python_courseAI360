from __future__ import annotations

from pydantic import Field
from pathlib import Path
import re

from checker.plugins import PluginABC, PluginOutput
from checker.exceptions import PluginExecutionFailed
from checker.plugins.scripts import RunScriptPlugin


class RunPytestModulePlugin(RunScriptPlugin):
    """Plugin for running pytest."""

    name = "run_pytest_module"

    class Args(PluginABC.Args):
        origin: str
        target: str
        timeout: int | None = None
        isolate: bool = False
        env_whitelist: list[str] = Field(default_factory=lambda: ["PATH"])

        coverage: bool | int | None = None
        allow_failures: bool = False

    def _run(self, args: Args, *, verbose: bool = False) -> PluginOutput:

        tests_cmd = ["uv", "pip", "install", "-e", str(args.target), "--force-reinstall"]

        script_cmd = " ".join(tests_cmd)

        run_script_args = RunScriptPlugin.Args(
            origin=args.origin,
            script=script_cmd,
            timeout=args.timeout,
            isolate=args.isolate,
            env_whitelist=args.env_whitelist,
        )
        result = super()._run(run_script_args, verbose=verbose)

        return result
