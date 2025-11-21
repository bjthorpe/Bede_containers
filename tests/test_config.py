# tests for loading config file ect..
import pytest
import sys
from dacite import exceptions
from check_yaml import DuplicateKeyError

sys.path.append("../")
from main import load_container_config_file
from main import load_user_config_file


def test_config_not_exist():
    with pytest.raises(FileNotFoundError):
        load_container_config_file("I_dont_exist.yaml")


def test_user_config_not_exist():
    with pytest.raises(FileNotFoundError):
        load_user_config_file("I_dont_exist.yaml")


def test_config_not_yaml():
    with pytest.raises(ValueError):
        load_container_config_file("tests/test_configs/test1.txt")


def test_user_config_not_yaml():
    with pytest.raises(ValueError):
        load_user_config_file("tests/test_configs/test1.txt")


def test_no_description():
    with pytest.raises(exceptions.MissingValueError):
        load_container_config_file("tests/test_configs/test1.yaml")


def test_no_image():
    Containers = load_container_config_file("tests/test_configs/test2.yaml")
    for key in Containers:
        assert Containers[key].image_file == f"Images/{key}.sif"


def test_no_shared_dir():
    with pytest.raises(ValueError):
        load_user_config_file("tests/test_configs/test4.yaml")


def test_multi_defintion_1():
    load_container_config_file("tests/test_configs/test5.yaml")


def test_multi_defintion_2():
    with pytest.raises(DuplicateKeyError):
        load_container_config_file("tests/test_configs/test6.yaml")
