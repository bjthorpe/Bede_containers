# tests for loading config file ect..
import pytest
import sys
from dacite import exceptions
from check_yaml import DuplicateKeyError

sys.path.append('../')
from main import load_config_file

def test_config_not_exist():
    with pytest.raises(FileNotFoundError):
        load_config_file('I_dont_exist.yaml')

def test_config_not_yaml():
    with pytest.raises(ValueError):
        load_config_file('tests/test_configs/test1.txt')
        
def test_no_description():
    with pytest.raises(exceptions.MissingValueError):
        load_config_file('tests/test_configs/test1.yaml')
        
def test_no_image_or_repo_1():
    with pytest.raises(ValueError):
        load_config_file('tests/test_configs/test2.yaml')

def test_no_image_or_repo_2():
    with pytest.raises(ValueError):
        load_config_file('tests/test_configs/test3.yaml')

def test_no_shared_dir():
    with pytest.raises(ValueError):
        load_config_file('tests/test_configs/test4.yaml')
    
def test_multi_defintion_1():
        load_config_file('tests/test_configs/test5.yaml')
        
def test_multi_defintion_2():
    with pytest.raises(DuplicateKeyError):
        load_config_file('tests/test_configs/test6.yaml')