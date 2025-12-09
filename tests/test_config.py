# tests for loading config file ect..
import pytest
import sys
from dacite import exceptions
from check_yaml import DuplicateKeyError
from run_container import format_command

sys.path.append("../")
from run_container import load_container_config_file, check_container_config


def test_config_not_exist():
    with pytest.raises(FileNotFoundError):
        load_container_config_file("I_dont_exist.yaml")

def test_config_not_yaml():
    with pytest.raises(ValueError):
        load_container_config_file("tests/test_configs/test1.txt")

def test_no_description():
    with pytest.raises(exceptions.MissingValueError):
        load_container_config_file("tests/test_configs/test1.yaml")

def test_no_image():
    Containers = load_container_config_file("tests/test_configs/test2.yaml")
    for key in Containers:
        assert Containers[key].image_file == f"Images/{key}.sif"

def test_invalid_image():
    # tests loading an image that does not end in .sif
    with pytest.raises(ValueError):
       load_container_config_file("tests/test_configs/test9.yaml")


def test_invaild_model_name():
    with pytest.raises(ValueError):
        load_container_config_file("tests/test_configs/test7.yaml")

def test_no_shared_dir():
    with pytest.raises(FileNotFoundError):
        load_container_config_file("tests/test_configs/test4.yaml")

def test_shared_dir_is_file():
    with pytest.raises(FileNotFoundError):
        load_container_config_file("tests/test_configs/test4b.yaml")

def test_multi_definition_1():
    load_container_config_file("tests/test_configs/test5.yaml")


def test_multi_definition_2():
    # chekc that we raise error if model names are repeated in the same config file
    with pytest.raises(DuplicateKeyError):
        load_container_config_file("tests/test_configs/test6.yaml")

def test_multi_definition_3():
# check for that we raise an error if model names are repeated 
# across multiple config files
    with pytest.raises(DuplicateKeyError):
        containers = check_container_config(["tests/test_configs/valid.yaml","tests/test_configs/valid.yaml"])

def test_format_command():
    '''
    test to check function that creates Apptainer commands
    '''
    valid_commands = [
        "apptainer exec Images/Example_Model1.sif hostname",
        "apptainer build Images/Example_Model1.sif docker://alpine:latest",
        "apptainer instance start Images/Example_Model1.sif Test",
        "apptainer instance stop Test"
    ]

    Containers = load_container_config_file("tests/test_configs/valid.yaml")
    for I,operation in enumerate(['run','build','start','stop']):
        Apptainer_command = format_command(operation,"Test",Containers['Example_Model1'],["hostname"])
        assert Apptainer_command in valid_commands

def test_run_with_no_image():
    # this checks that running with an image file that does not exist raises a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        Containers = load_container_config_file("tests/test_configs/test8.yaml")
        format_command('run',"Test",Containers['Example_Model1'],["hostname"])
