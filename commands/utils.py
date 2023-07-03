import os
from invoke import Exit


def assert_repo_root_directory():
    root_directory = os.getcwd()
    activation_file = os.path.join(root_directory, "activate.sh")
    if not os.path.exists(activation_file):  # apparently we're not executing from root directory
        raise Exit("Command should be run from repository root")
