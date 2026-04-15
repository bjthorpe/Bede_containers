import pytest

@pytest.hookimpl()
def pytest_addoption(parser):
    parser.addoption("--no_GPU", action="store_true",
                     help="skip GPU tests, marked with marker @no_GPU")
    parser.addoption("--model_names", nargs="*",default=['MatterSim_V1_5M'],
                     help="List to Specify which model(s) to use when testing CASTEP. " \
                     "If not specified the default is to sequentially test one model from each model family.")
@pytest.hookimpl()
def pytest_runtest_setup(item):
    if 'GPU' in item.keywords and item.config.getoption("--no_GPU"):
        pytest.skip("test GPU tests skipped due to no_GPU flag")