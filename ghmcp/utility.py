"""
utility.py
----------
Provides utility functions for working with Git repositories using GitPython.

Functions:
    get_repo(path: str) -> Optional[Repo]:
        Returns a GitPython Repo object for the given path if it is a valid git repo, else None.
        - path: The filesystem path to the repository.
        - Returns: Repo object if valid, None otherwise.
"""

import os
import logging
from typing import Optional
from git import Repo, InvalidGitRepositoryError, NoSuchPathError

# Configure logging for this module
logger = logging.getLogger(__name__)


def get_repo(path: str) -> Optional[Repo]:
    """
    Returns a GitPython Repo object for the given path if it is a valid git repo, else None.

    This function attempts to create a GitPython Repo object from the provided path.
    It handles various error conditions gracefully and provides detailed logging
    for debugging purposes.

    Args:
        path (str): The filesystem path to the repository directory.

    Returns:
        Optional[Repo]: A GitPython Repo object if the path is a valid Git repository,
                       None otherwise.

    Example:
        repo = get_repo('/Users/user/my-project')
        if repo:
            print(f"Repository found: {repo.working_dir}")
        else:
            print("Not a valid Git repository")
    """
    logger.debug(f"Attempting to get repository from path: {path}")

    # Validate input path
    if not path:
        logger.warning("Empty or None path provided to get_repo")
        return None

    if not isinstance(path, str):
        logger.error(f"Invalid path type provided to get_repo: {type(path)}. Expected str.")
        return None

    # Convert to absolute path for consistency
    abs_path = os.path.abspath(path)
    logger.debug(f"Using absolute path: {abs_path}")

    # Check if path exists
    if not os.path.exists(abs_path):
        logger.warning(f"Path does not exist: {abs_path}")
        return None

    # Check if path is a directory
    if not os.path.isdir(abs_path):
        logger.warning(f"Path is not a directory: {abs_path}")
        return None

    try:
        logger.debug(f"Creating Repo object for path: {abs_path}")
        repo = Repo(abs_path)

        # Verify repository is not bare (has a working directory)
        if repo.bare:
            logger.info(f"Repository at {abs_path} is a bare repository")
        else:
            logger.debug(f"Repository working directory: {repo.working_dir}")

        # Log basic repository information
        try:
            active_branch = repo.active_branch.name
            logger.debug(f"Active branch: {active_branch}")
        except Exception as e:
            logger.debug(f"Could not determine active branch: {e}")

        # Log remote information if available
        try:
            remotes = [remote.name for remote in repo.remotes]
            if remotes:
                logger.debug(f"Available remotes: {remotes}")
            else:
                logger.debug("No remotes configured for this repository")
        except Exception as e:
            logger.debug(f"Could not retrieve remote information: {e}")

        # Log branch information
        try:
            branches = [head.name for head in repo.heads]
            logger.debug(f"Local branches: {branches}")
        except Exception as e:
            logger.debug(f"Could not retrieve branch information: {e}")

        # Log commit count if possible
        try:
            commit_count = len(list(repo.iter_commits()))
            logger.debug(f"Total commits in repository: {commit_count}")
        except Exception as e:
            logger.debug(f"Could not count commits: {e}")

        logger.info(f"Successfully created Repo object for: {abs_path}")
        return repo

    except InvalidGitRepositoryError as e:
        logger.warning(f"Invalid Git repository at {abs_path}: {e}")
        logger.debug(f"InvalidGitRepositoryError details:", exc_info=True)
        return None

    except NoSuchPathError as e:
        logger.warning(f"Path not found when creating Repo object: {abs_path}: {e}")
        logger.debug(f"NoSuchPathError details:", exc_info=True)
        return None

    except PermissionError as e:
        logger.error(f"Permission denied accessing repository at {abs_path}: {e}")
        logger.debug(f"PermissionError details:", exc_info=True)
        return None

    except Exception as e:
        logger.error(f"Unexpected error when creating Repo object for {abs_path}: {e}")
        logger.debug(f"Unexpected error details:", exc_info=True)
        return None
