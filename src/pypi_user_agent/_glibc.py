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

import os
import sys


def glibc_version_string_confstr() -> str | None:
    """
    Primary implementation of glibc_version_string using os.confstr.
    """
    # os.confstr is quite a bit faster than ctypes.DLL. It's also less likely
    # to be broken or missing. This strategy is used in the standard library
    # platform module:
    # https://github.com/python/cpython/blob/fcf1d003bf4f0100c9d0921ff3d70e1127ca1b71/Lib/platform.py#L175-L183
    if sys.platform == "win32":
        return None
    try:
        # os.confstr("CS_GNU_LIBC_VERSION") returns a string like "glibc 2.17":
        version_str = os.confstr("CS_GNU_LIBC_VERSION")
        if version_str is None:
            return None
        _, version = version_str.split()
    except (AttributeError, OSError, ValueError):
        # os.confstr() or CS_GNU_LIBC_VERSION not available (or a bad value)...
        return None
    return version


def glibc_version_string_ctypes() -> str | None:
    """
    Fallback implementation of glibc_version_string using ctypes.
    """

    try:
        import ctypes
    except ImportError:
        return None

    # ctypes.CDLL(None) internally calls dlopen(NULL), and as the dlopen
    # manpage says, "If filename is NULL, then the returned handle is for the
    # main program". This way we can let the linker do the work to figure out
    # which libc our process is actually using.
    process_namespace = ctypes.CDLL(None)
    try:
        gnu_get_libc_version = process_namespace.gnu_get_libc_version
    except AttributeError:
        # Symbol doesn't exist -> therefore, we are not linked to
        # glibc.
        return None

    # Call gnu_get_libc_version, which returns a string like "2.5"
    gnu_get_libc_version.restype = ctypes.c_char_p
    version_str: str = gnu_get_libc_version()

    return version_str


def glibc_version_string() -> str | None:
    """
    Returns glibc version string, or None if not using glibc.
    """
    return glibc_version_string_confstr() or glibc_version_string_ctypes()


# platform.libc_ver regularly returns completely nonsensical glibc
# versions. E.g. on my computer, platform says:
#
#   ~$ python2.7 -c 'import platform; print(platform.libc_ver())'
#   ('glibc', '2.7')
#   ~$ python3.5 -c 'import platform; print(platform.libc_ver())'
#   ('glibc', '2.9')
#
# But the truth is:
#
#   ~$ ldd --version
#   ldd (Debian GLIBC 2.22-11) 2.22
#
# This is unfortunate, because it means that the linehaul data on libc
# versions that was generated by pip 8.1.2 and earlier is useless and
# misleading. Solution: instead of using platform, use our code that actually
# works.
def libc_ver() -> tuple[str, str]:
    """
    Try to determine the glibc version

    Returns a tuple of strings (lib, version) which default to empty strings
    in case the lookup fails.
    """
    glibc_version = glibc_version_string()
    if glibc_version is None:
        return ("", "")
    else:
        return ("glibc", glibc_version)
