# tests for lcomand line argumants
import pytest
import sys
import os
from bede_containers.run_container import main, format_command,CMD_FormatError 
from bede_containers.run_container import check_container_config
from bede_containers.util_functions import get_toolkit_home
from pathlib import Path
import subprocess
DATA_DIR = Path(__file__).parent / "test_configs"
@pytest.fixture(scope='module')
def build_test_container():
    # cleanup any potential old test containers
    toolkit_home = get_toolkit_home()
    if Path(f'{toolkit_home}/Images/TestContainer.sif').exists():
        os.remove(f'{toolkit_home}/Images/TestContainer.sif')

    apptainer_command = f"apptainer build {toolkit_home}/Images/TestContainer.sif docker://alpine:latest"
    proc = subprocess.run(apptainer_command, shell=True)
#start tests
    yield
#cleanup afterwards
    os.remove(f'{toolkit_home}/Images/TestContainer.sif')
    return

@pytest.fixture(scope='module')
def build_test_container_2():
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

def test_list(capfd, monkeypatch):
    ''' 
    listing just test container group
    '''
    # run main program subbing in new cmd arguments
    prog = sys.argv[0]
    monkeypatch.setattr("sys.argv", [prog, "list","--group","Test"])
    return_code = main()
    out = capfd.readouterr().out
    # only check up to the end of the list header as the actual 
    # contents does not matter and can vary    
    # check_test_output("tests/good_outputs/test_list.txt",out,9)
    assert return_code == 0

def test_list_all(capfd, monkeypatch):
    '''
    listing all containers
    '''
    # run main program subbing in new cmd arguments
    prog = sys.argv[0]
    monkeypatch.setattr("sys.argv", [prog,"list"])
    return_code = main()
    out = capfd.readouterr().out
    # only check up to the end of the list header as the actual 
    # contents does not matter and can vary
    # check_test_output("tests/good_outputs/test_list.txt",out,nlines=9)
    assert return_code == 0

def test_debug_flag(capfd, monkeypatch,build_test_container):
    '''
    check debug flag works
    '''
    # run main program subbing in new cmd arguments
    prog = sys.argv[0]
    monkeypatch.setattr("sys.argv", [prog,"--debug", "run", "TestContainer","hostname"])
    return_code = main()
    out = capfd.readouterr().out
    #check_test_output("tests/good_outputs/test_debug.txt",out)
    assert return_code == 0
    
def test_build_and_run(monkeypatch):
    '''
    check build and run flags work 
    with a simple ubuntu container.
    '''
    toolkit_home = get_toolkit_home()
    prog = sys.argv[0]
    # first build container
    monkeypatch.setattr("sys.argv", [prog,"build", "TestContainer2"])
    return_code = main()
    assert return_code == 0
    # now run continer
    monkeypatch.setattr("sys.argv", [prog,"run", "TestContainer2","hostname"])
    return_code = main()
    os.remove(f"{toolkit_home}/Images/TestContainer2.sif")
    assert return_code == 0

def test_unknown_operation():
# check for that we raise an error if operation is unknown
    
    containers = check_container_config([f"{DATA_DIR}/valid.yaml"])
    with pytest.raises(CMD_FormatError):
        cmd = {}
        format_command("unknown","test",containers['Example_Model1'],cmd)

def test_config_file_flag(monkeypatch,build_test_container_2):
    '''
    check config_file flag works with single file
    '''
    # run main program subbing in new cmd arguments
    prog = sys.argv[0]
    conf_file = f"{DATA_DIR}/valid.yaml"
    monkeypatch.setattr("sys.argv", [prog,f"--config_file={conf_file}", "run", "Example_Model1","hostname"])
    return_code = main()
    assert return_code == 0

def test_config_file_flag_dir(monkeypatch,build_test_container_2):
    '''
    check config_file flag works with a directory
    '''
    # run main program subbing in new cmd arguments
    prog = sys.argv[0]
    conf_file = f"{DATA_DIR}/multiple_files_test/"
# use model denied in valid.yaml
    monkeypatch.setattr("sys.argv", [prog,f"--config_file={conf_file}", "run", "Example_Model1","hostname"])
    return_code = main()
    assert return_code == 0
# now try different model defined in valid2.yaml
    monkeypatch.setattr("sys.argv", [prog,f"--config_file={conf_file}", "run", "Example_Model2","hostname"])
    return_code = main()
    assert return_code == 0   

def test_model_name_flag(monkeypatch):
    '''
    check that giving a model_name that is not in the config raises a ValueError
    '''
    # run main program subbing in new cmd arguments
    prog = sys.argv[0]
    conf_file = f"{DATA_DIR}/valid.yaml"
    monkeypatch.setattr("sys.argv", [prog,f"--config_file={conf_file}", "run", "Test","hostname"])
    with pytest.raises(ValueError):
        return_code = main()