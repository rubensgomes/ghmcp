"""
utility.py
----------
Provides utility functions for working with Git repositories using GitPython.

Functions:
    get_repo(path: str) -> Optional[Repo]:
        Returns a GitPython Repo object for the given path if it is a valid git repo, else None.
        - path: The filesystem path to the repository.
        - Returns: Repo object if valid, None otherwise.

Usage:
    from ghmcp.utility import get_repo
    repo = get_repo('/path/to/repo')
"""

from git import Repo
from typing import Optional
import os

def get_repo(path: str) -> Optional[Repo]:
    """
    Returns a GitPython Repo object for the given path if it is a valid git repo, else None.
    """
    if not os.path.isdir(path):
        return None
    try:
        return Repo(path)
    except Exception:
        return None
