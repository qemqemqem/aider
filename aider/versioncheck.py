import os
import sys
import time
from pathlib import Path

import packaging.version

import aider
from aider import utils
from aider.dump import dump  # noqa: F401

VERSION_CHECK_FNAME = Path.home() / ".aider" / "caches" / "versioncheck"


def install_from_main_branch(io):
    """
    Install the latest version of aider from the main branch of the GitHub repository.
    """
    # Commented out automatic installation
    # return utils.check_pip_install_extra(
    #     io,
    #     None,
    #     "Install the development version of aider from the main branch?",
    #     ["git+https://github.com/qemqemqem/aider-advanced.git"],
    #     self_update=True,
    # )
    
    io.tool_warning("To update Aider Advanced, run: git pull")
    return False


def install_upgrade(io, latest_version=None):
    """
    Install the latest version of aider from PyPI.
    """
    # Display update message but don't attempt automatic update
    if latest_version:
        io.tool_warning(f"An updated version of Aider Advanced (v{latest_version}) is available.")
    
    io.tool_warning("To update, run: git pull and git merge in your aider-advanced directory.")
    return False


def check_version(io, just_check=False, verbose=False):
    if not just_check and VERSION_CHECK_FNAME.exists():
        day = 60 * 60 * 24
        since = time.time() - os.path.getmtime(VERSION_CHECK_FNAME)
        if 0 < since < day:
            if verbose:
                hours = since / 60 / 60
                io.tool_output(f"Too soon to check version: {hours:.1f} hours")
            return

    # Always touch the version check file to prevent frequent checks
    VERSION_CHECK_FNAME.parent.mkdir(parents=True, exist_ok=True)
    VERSION_CHECK_FNAME.touch()
    
    # For development purposes, just show the current version
    if verbose:
        current_version = aider.__version__
        io.tool_output(f"Current version: {current_version}")
        io.tool_output("Version checking with PyPI is disabled for Aider Advanced")
    
    # Uncomment this to simulate an update being available for testing
    # is_update_available = True
    # if is_update_available:
    #     io.tool_warning("An updated version of Aider Advanced is available.")
    #     io.tool_warning("To update, run: git pull and git merge in your aider-advanced directory.")
    
    return False
