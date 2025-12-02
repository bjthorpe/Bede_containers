import os
from pathlib import Path
import pytest

def check_test_output(golden_file,pytest_output):
    '''
    Function to check that the stdout and stderr captured 
    by pytest matches some known good output.

    '''
    # env variable to control if we want to use current output as new benchmark

    UPDATE_TESTS = os.getenv("UPDATE_TESTS")
    golden_file = Path(golden_file)

    if UPDATE_TESTS:
        golden_file.write_text(pytest_output)
        pytest.skip("Updated golden file")

    expected_output = golden_file.read_text()
    assert pytest_output == expected_output
