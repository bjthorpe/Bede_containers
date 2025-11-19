import pytest

@pytest.hookimpl()
def pytest_addoption(parser):
    parser.addoption("--no_GPU", action="store_true",
                     help="skip GPU tests, marked with marker @no_GPU")
@pytest.hookimpl()
def pytest_runtest_setup(item):
    if 'GPU' in item.keywords and item.config.getoption("--no_GPU"):
        pytest.skip("test GPU tests skipped due to no_GPU flag")

@pytest.hookimpl()
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "GPU: mark test as requiring a working GPU"
    )