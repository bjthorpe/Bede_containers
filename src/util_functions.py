import os
from pathlib import Path
import pytest

def check_test_output(golden_file, pytest_output,nlines=None):
    """
    Function to check that the stdout and stderr captured
    by pytest matches some known good output.

    Params:
    Golden_file - file containing known good output
    pytest_output - output from the test run
    nlines - (optional) if provided only check the first n lines 

    """
    # env variable to control if we want to use current output as new benchmark

    UPDATE_TESTS = os.getenv("UPDATE_TESTS")
    golden_file = Path(golden_file)

    if UPDATE_TESTS:
        golden_file.write_text(pytest_output)
        pytest.skip("Updated golden file")

    expected_output = golden_file.read_text()    
    if nlines == None:
        assert pytest_output == expected_output
    else:
        # only check first n lines
        OutputByLines = pytest_output.splitlines()
        ExpOutputByLines = expected_output.splitlines()
        assert OutputByLines[0:nlines] == ExpOutputByLines[0:nlines]
    
def create_build_options(options: dict) -> str:
    """
    function to create a build options string for Apptainer from a dict
    The returned string is of the form "--build-arg KEY1=VALUE1 -build-arg KEY2=VALUE2 ..."

    This is used by Apptainer with the build command to allow the use of placeholders
    using {{ variable }} syntax in the container definition files.
    (see https://apptainer.org/docs/user/main/cli/apptainer_build.html for more details).

    This allows us to use a single definition file to cover multiple pre-trained models
    from the same family and ultimately saves us using multiple definition files with
    only tiny differences.
    """
    if options:
        build_args_str = "".join([f" --build-arg {k}={options[k]}" for k in options])
    else:
        build_args_str = ""
    return build_args_str