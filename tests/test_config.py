# tests for loading config file ect..
import pytest
import sys
from dacite import exceptions
from bede_containers.check_yaml import DuplicateKeyError
from bede_containers.run_container import format_command
from bede_containers.util_functions import get_toolkit_home
from pathlib import Path
import subprocess
import os

sys.path.append("../")
from bede_containers.run_container import load_container_config_file, check_container_config

@pytest.fixture(scope="module")
def build_test_container():
    toolkit_home = get_toolkit_home()
    test_containers = ['Example_Model1.sif','Example_Model2.sif']
    # cleanup any potential old test containers
    for cont in test_containers:
        if Path(f'{toolkit_home}/Images/{cont}').exists():
            os.rmdir(f'{toolkit_home}/Images/{cont}')
        apptainer_command = f"apptainer \
        build {toolkit_home}/Images/{cont} docker://alpine:latest"
        proc = subprocess.run(apptainer_command, shell=True)
#start tests
    yield
#cleanup afterwards
    for cont in test_containers:
        os.remove(f'{toolkit_home}/Images/{cont}')
    return

def generate_fake_cmd_opts(operation:str):
    '''
    generate a fake default cmd_Options dict based on provided operation
    '''

    match operation:
        case 'run':
            fake_CMD_options={
                'operation':'run','model_name':'test','cmd':["hostname"],
                'interactive':False,'writable':False,
                'config_file':None,'debug':False,'version':'1.0.4'
                }
        case 'build':
            fake_CMD_options={
                'operation':f'{operation}','model_name':'test',
                'writable':False,
                'config_file':None,'debug':False,
                'version':'1.0.4'
                }
        case 'load':
            fake_CMD_options={
                'operation':f'{operation}','model_name':'test',
                'writable':False,
                'config_file':None,'debug':False,
                'version':'1.0.4'
                }
        case 'list':
            fake_CMD_options={
                'operation':'list','group':'',
                'config_file':None,'debug':False,
                'version':'1.0.4'
                }
        case 'start':
            fake_CMD_options={
                'operation':'start','model_name':'test',
                'port':None,'timeout':10,'num_retry':5,'num_servers':1,
                'config_file':None,'debug':False,'version':'1.0.4'
                }            
        case 'stop':
            fake_CMD_options={
                'operation':'stop','model_name':'test',
                'config_file':None,'debug':False,
                'version':'1.0.4'
                }
        case _:
            print(f" error: {operation} is not a valid operation")
            sys.exit(11)

    return fake_CMD_options
        
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
    toolkit_home = get_toolkit_home()
    Containers = load_container_config_file("tests/test_configs/test2.yaml")
    for key in Containers:
        assert Containers[key].image_file == f"{toolkit_home}/Images/{key}.sif"

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
    with pytest.raises(ValueError):
        load_container_config_file("tests/test_configs/test4b.yaml")

def test_multi_definition_1():
    load_container_config_file("tests/test_configs/test5.yaml")

def test_invalid_option():
    # check that we raise error if we provide an invalid option
    with pytest.raises(ValueError):
        load_container_config_file("tests/test_configs/test10a.yaml")

def test_case_insenstive():
    load_container_config_file("tests/test_configs/test10b.yaml")

def test_multi_definition_2():
    # chekc that we raise error if model names are repeated in the same config file
    with pytest.raises(DuplicateKeyError):
        load_container_config_file("tests/test_configs/test6.yaml")

def test_multi_definition_3():
# check for that we raise an error if model names are repeated 
# across multiple config files
    with pytest.raises(DuplicateKeyError):
        containers = check_container_config(["tests/test_configs/valid.yaml","tests/test_configs/valid.yaml"])

def test_format_command(build_test_container):
    '''
    test to check function that creates Apptainer commands
    '''
    toolkit_home=get_toolkit_home()
    
    valid_commands = [
        f"apptainer exec --bind {toolkit_home}  --nv {toolkit_home}/Images/Example_Model1.sif hostname",
        f"apptainer build --build-arg toolkit_home={toolkit_home} --nv {toolkit_home}/Images/Example_Model1.sif docker://alpine:latest",
        f"apptainer instance start --bind {toolkit_home}  --nv {toolkit_home}/Images/Example_Model1.sif Test",
        f"apptainer instance stop Test"
    ]

    Containers = load_container_config_file("tests/test_configs/valid.yaml")
    for I,operation in enumerate(['run','build','start','stop']):
        fake_CMD_options = generate_fake_cmd_opts(operation)
        Apptainer_command = format_command(operation,"Test",Containers['Example_Model1'],fake_CMD_options)
        assert Apptainer_command in valid_commands

def test_run_with_no_image():
    # this checks that running with an image file that does not exist raises a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        Containers = load_container_config_file("tests/test_configs/test8.yaml")
        fake_CMD_options = generate_fake_cmd_opts('run')
        format_command('run',"Test",Containers['Example_Model1'],fake_CMD_options)
