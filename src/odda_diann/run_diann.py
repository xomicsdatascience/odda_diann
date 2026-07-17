# DIA-NN MCP Server
#
# Provides MCP tools for running DIA-NN proteomics software via Apptainer
# containers and listing available DIA-NN versions.

from odda_utils.async_exec import execute_process
from odda_diann import diann_instance_format
from typing import Optional, List, Dict, Any, Union
import asyncio
import contextlib
import os
import re
from mcp.server.fastmcp import FastMCP

apptainer_diann_command = "apptainer run " + diann_instance_format

app = FastMCP("diann_multiversion")


def _version_sort_key(version: str):
    """
    Build a sort key for a dotted numeric version string.

    Parameters
    ----------
    version : str
        Version string such as "2.6.1".

    Returns
    -------
    tuple
        Tuple of integer components; unparseable versions sort lowest.
    """
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return (-1,)


async def _resolve_version(version: Optional[str]) -> Dict[str, Any]:
    """
    Resolve the DIA-NN version to run, discovering it dynamically if not given.

    Parameters
    ----------
    version : Optional[str]
        Explicit bare version string (e.g. "2.6.1"), or None to auto-discover
        the newest running instance via ``list_diann_versions``.

    Returns
    -------
    Dict[str, Any]
        ``{"ok": True, "version": <str>}`` on success, otherwise
        ``{"ok": False, "error": <str>}``.
    """
    if version:
        return {"ok": True, "version": version}
    listing = await list_diann_versions()
    versions = listing.get("versions") or []
    if not versions:
        return {
            "ok": False,
            "error": (
                "No DIA-NN version specified and none could be discovered from "
                "running Apptainer instances. Start an instance (e.g. diann_v2.6.1) "
                "or pass an explicit version string."
            ),
        }
    return {"ok": True, "version": max(versions, key=_version_sort_key)}


@app.tool()
async def run_diann(env: Optional[dict] = None,
              version: Optional[str] = None,
              timeout_sec: Optional[int] = None,
              args: Optional[List[str]] = None):
    """
    Run the specified version of DIA-NN using the specified arguments. DIA-NN is run via an Apptainer instance.
    Parameters
    ----------
    env : dict
        Environment variables to set; overrides current environment.
    version : str, optional
        Bare version of DIA-NN to run (e.g. "2.6.1"). If omitted (None), the
        newest version among running Apptainer instances is auto-discovered via
        ``list_diann_versions``.
    timeout_sec : int
        Time in seconds before killing the process.
    args : list
        List of arguments to pass to DIA-NN.

    Returns
    -------

    """
    exec_env = os.environ.copy()
    if env:
        exec_env.update({str(k): str(v) for k, v in env.items()})
    resolved = await _resolve_version(version)
    if not resolved["ok"]:
        return resolved
    cmd = apptainer_diann_command.format(version=resolved["version"]).split(" ")
    if args:
        cmd.extend(args)
    return await execute_process(cmd,
                           env=exec_env,
                           timeout_sec=timeout_sec)


@app.tool()
async def list_diann_versions(
    timeout_sec: Optional[float] = 10.0,
) -> Dict[str, Any]:
    """
    List available DIA-NN versions by examining running Apptainer instances.

    Queries the list of running Apptainer/Singularity instances and extracts
    version information from instances with names matching the pattern "diann_v*".
    For example, an instance named "diann_v1.8.1" would return version "1.8.1".

    Parameters
    ----------
    timeout_sec : Optional[float]
        Timeout in seconds for the instance list command. Default is 10.0.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing:
        - ok (bool): Whether the operation succeeded.
        - versions (List[str]): List of available DIA-NN version strings.
        - instance_names (List[str]): Full instance names matching diann_v* pattern.
        - container_runtime (str): Which runtime was used (apptainer/singularity).
        - error (str, optional): Error message if the operation failed.
    """
    diann_pattern = re.compile(r"^diann_v(.+)$")

    for container_cmd in ["apptainer", "singularity"]:
        cmd = [container_cmd, "instance", "list"]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_b, stderr_b = (
                    await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
                    if timeout_sec
                    else await proc.communicate()
                )
            except asyncio.TimeoutError:
                with contextlib.suppress(ProcessLookupError):
                    proc.kill()
                continue

            if proc.returncode != 0:
                continue

            stdout_str = stdout_b.decode(errors="replace")
            versions: List[str] = []
            instance_names: List[str] = []

            for line in stdout_str.strip().split("\n"):
                if not line.strip() or line.startswith("INSTANCE NAME"):
                    continue

                parts = line.split()
                if not parts:
                    continue

                instance_name = parts[0]
                match = diann_pattern.match(instance_name)
                if match:
                    version = match.group(1)
                    versions.append(version)
                    instance_names.append(instance_name)

            return {
                "ok": True,
                "versions": versions,
                "instance_names": instance_names,
                "container_runtime": container_cmd,
            }

        except FileNotFoundError:
            continue

    return {
        "ok": False,
        "versions": [],
        "instance_names": [],
        "error": (
            "Failed to list container instances. "
            "Ensure 'apptainer' or 'singularity' is installed and accessible."
        ),
    }

@app.tool()
async def get_diann_argument_info(arg: Optional[Union[str, List[str]]] = None):
    """
    Provides a description of the arguments available for DIA-NN. If the function is called without arguments, the full
    list of parameters is returned. If called with a single argument, this function returns a description of the
    specified argument. If called with a list of arguments, the function returns a description for each argument.
    Parameters
    ----------
    arg : Optional[Union[str, List[str]]]
        The argument or list of arguments for which information is requested.

    Returns
    -------
    str
        Description string of the requested argument(s).
    """
    if arg is None or len(arg) == 0:
        from odda_diann import diann_all_arguments
        return diann_all_arguments
    else:
        from odda_diann import diann_argument_dict
        if isinstance(arg, str):
            arg = [arg]
        l = ""
        not_found = []
        for a in arg:
            if a not in diann_argument_dict:
                not_found.append(a)
                continue
            l += diann_argument_dict[a] + "\n"
        if not_found:
            n = "\n"
            l += f"\n\nThe following arguments were not found: {n.join(not_found)}"
        return l


def main():
    app.run()

if __name__ == "__main__":
    main()
