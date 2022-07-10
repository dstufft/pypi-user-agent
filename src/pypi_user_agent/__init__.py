# Copyright (c) 2008-present Individual Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json
import os
import platform
import shutil
import subprocess
import sys
from typing import Any

from ._compat import importlib_metadata
from ._glibc import libc_ver

# These are environment variables present when running under various
# CI systems.  For each variable, some CI systems that use the variable
# are indicated.  The collection was chosen so that for each of a number
# of popular systems, at least one of the environment variables is used.
# This list is used to provide some indication of and lower bound for
# CI traffic to PyPI.  Thus, it is okay if the list is not comprehensive.
# For more background, see: https://github.com/pypa/pip/issues/5499
_CI_ENVIRONMENT_VARIABLES = (
    # Azure Pipelines
    "BUILD_BUILDID",
    # Jenkins
    "BUILD_ID",
    # AppVeyor, CircleCI, Codeship, Gitlab CI, Shippable, Travis CI
    "CI",
    # Explicit environment variable.
    "PIP_IS_CI",
)


def _looks_like_ci() -> bool:
    """
    Return whether it looks like pip is running under CI.
    """
    # We don't use the method of checking for a tty (e.g. using isatty())
    # because some CI systems mimic a tty (e.g. Travis CI).  Thus that
    # method doesn't provide definitive information in either direction.
    return any(name in os.environ for name in _CI_ENVIRONMENT_VARIABLES)


def _has_tls() -> bool:
    try:
        import _ssl  # noqa: F401  # ignore unused

        return True
    except ImportError:
        pass

    return False


def _get_version(name: str) -> str | None:
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return None


def user_agent(name: str, version: str, *, user_data: str | None = None) -> str:
    """
    Return a string representing the user agent.
    """
    data: dict[str, Any] = {
        "installer": {"name": name, "version": version},
        "python": platform.python_version(),
        "implementation": {
            "name": platform.python_implementation(),
        },
    }

    if data["implementation"]["name"] == "CPython":
        data["implementation"]["version"] = platform.python_version()
    elif data["implementation"]["name"] == "PyPy":
        pypy_version_info = sys.pypy_version_info  # type: ignore
        if pypy_version_info.releaselevel == "final":
            pypy_version_info = pypy_version_info[:3]
        data["implementation"]["version"] = ".".join(
            [str(x) for x in pypy_version_info]
        )
    elif data["implementation"]["name"] == "Jython":
        # Complete Guess
        data["implementation"]["version"] = platform.python_version()
    elif data["implementation"]["name"] == "IronPython":
        # Complete Guess
        data["implementation"]["version"] = platform.python_version()

    if sys.platform.startswith("linux"):
        import distro

        linux_distribution = distro.name(), distro.version(), distro.codename()
        distro_infos: dict[str, Any] = dict(
            filter(
                lambda x: x[1],
                zip(["name", "version", "id"], linux_distribution),
            )
        )
        libc = dict(
            filter(
                lambda x: x[1],
                zip(["lib", "version"], libc_ver()),
            )
        )
        if libc:
            distro_infos["libc"] = libc
        if distro_infos:
            data["distro"] = distro_infos

    if sys.platform.startswith("darwin") and platform.mac_ver()[0]:
        data["distro"] = {"name": "macOS", "version": platform.mac_ver()[0]}

    if platform.system():
        data.setdefault("system", {})["name"] = platform.system()

    if platform.release():
        data.setdefault("system", {})["release"] = platform.release()

    if platform.machine():
        data["cpu"] = platform.machine()

    if _has_tls():
        import _ssl as ssl

        data["openssl_version"] = ssl.OPENSSL_VERSION

    setuptools_version = _get_version("setuptools")
    if setuptools_version is not None:
        data["setuptools_version"] = setuptools_version

    if shutil.which("rustc") is not None:
        # If for any reason `rustc --version` fails, silently ignore it
        try:
            rustc_output = subprocess.check_output(
                ["rustc", "--version"], stderr=subprocess.STDOUT, timeout=0.5
            )
        except Exception:
            pass
        else:
            if rustc_output.startswith(b"rustc "):
                # The format of `rustc --version` is:
                # `b'rustc 1.52.1 (9bc8c42bb 2021-05-09)\n'`
                # We extract just the middle (1.52.1) part
                data["rustc_version"] = rustc_output.split(b" ")[1].decode()

    # Use None rather than False so as not to give the impression that
    # pip knows it is not being run under CI.  Rather, it is a null or
    # inconclusive result.  Also, we include some value rather than no
    # value to make it easier to know that the check has been run.
    data["ci"] = True if _looks_like_ci() else None

    if user_data is not None:
        data["user_data"] = user_data

    return "{data[installer][name]}/{data[installer][version]} {json}".format(
        data=data,
        json=json.dumps(data, separators=(",", ":"), sort_keys=True),
    )
