# Setup

This page contains information to setup your development environment for
the `recscreener` application.

## Installation and Updates

Following instructions are for `macOS UNIX`:

1. Install required tools

    ```shell
    brew install python3
    brew install pipx
    pipx ensurepath
    pipx install pylint
    pipx install pytest
    pipx install poetry
    # notice that the poetry-plugin-shell needs to be injected
    pipx inject poetry poetry-plugin-shell
    pipx install "fastapi[standard]"
    # to install any new application dependencies
    # poetry add mcp
    # to install any new development dependencies
    # poetry add --dev httpx
    ```

2. Update dependencies

    ```shell
    poetry self update
    poetry self add poetry-plugin-up
    poetry update -vvv
    poetry up --only=dev --latest
    poetry up --latest
    poetry lock --regenerate -vv
    ```

## Python Virtual Environment

As per [PEP 668](https://peps.python.org/pep-0668/) starting with Python 3.12,
non-brew-packaged Python package should only be installed in virtual
environments.

1. Configure `poetry` venv location and install packages defined in the
   `pyproject.toml` dependencies:

    ```shell
    # configure poetry to create virtual environment under <project>/.venv
    poetry config virtualenvs.in-project true
    poetry lock --regenerate -vv
    poetry build
    poetry install
    # display information about virtual environment 
    poetry env info
    ```

2. Open a shell within virtual environment using `poetry`:

    ```shell
    # Ensure at the top of the project root folder
    # NOTE: this assumes you have cloned this project from a Git repo
    cd $(git rev-parse --show-toplevel) || exit
    poetry shell
    ```

3. Install AI tools within virtual environment using `poetry`:

    ```shell
    poetry shell
    npm install -g @anthropic-ai/claude-code
    ```

## Linting and Unit Testing

   ```shell
   cd $(git rev-parse --show-toplevel) || exit
   poetry run pylint rescreener || {
     printf "failed pylint.\n" >&2
     sleep 60
     exit
   }
   # run pytest with coverage
   poetry run python -m coverage run -m pytest tests/ || {
     printf "failed unit testing.\n" >&2
     sleep 10
     exit
   }
   # generate coverage report
   poetry run python -m coverage report -m
   ```

## Clean Shell Environment

- To complete clean any files and folders from this project untracked by git,
  including venv (virtual enviroments) run:

    ```shell
    git clean -fXd
    ```

- To remove only the virtual environment delete the `.venv` folder:

    ```shell
    # Ensure at the top of the project root folder
    # NOTE: this assumes you have cloned this project from a Git repo
    cd $(git rev-parse --show-toplevel) || exit
    rm -fr .venv/
    ```

## Running the main program

- To display the program version:

    ```shell
    PYTHONPATH="$(git rev-parse --show-toplevel)"
    export PYTHONPATH
    python3 ghmcp/main.py
    ```

## PyCharm IDE Development Environment

- First, ensure to follow all the previous steps to "Setting Up Shell
  Development Environment"

1. Open the project `rescreener` folder using `PyCharm`
2. Follow instructions
   to [Create a Poetry environment](https://www.jetbrains.com/help/pycharm/poetry.html#poetry-env)
    - Click on the Python Interpreter Selector to "Add New Interpreter"
    - Select "Add Local Interpreter..."
    - Select "Poetry Environment"
    - Ensure "Base interpreter" is `/opt/homebrew/bin/python3` or
      `/usr/local/bin/python3` (macOS/Linux only)
    - Ensure "Poetry executable" (e.g., ${HOME}/.local/bin/poetry)
    - Click the OK button
3. Go to `PyCharm` > `Settings`
    - Enter `Python Integrated Tools`
    - Under `Testing` > `Default test runner` select `pytest`
4. Open `PyCharm` > `Terminal` to go to venv prompt
    - Ensure .venv correct settings:

    ```shell
    poetry env info
    ```

