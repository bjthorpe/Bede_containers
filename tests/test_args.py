# tests for lcomand line argumants
import pytest
import sys
from util_functions import check_test_output
from run_container import main, format_command,CMD_FormatError 
from run_container import check_container_config

def test_list(capfd, monkeypatch):
    ''' 
    listing just test container group
    '''
    # run main program subbing in new cmd arguments
    prog = sys.argv[0]
    monkeypatch.setattr("sys.argv", [prog, "list","--group","Test"])
    main()
    out = capfd.readouterr().out
    check_test_output("tests/good_outputs/test_list_all.txt",out)

def test_list_all(capfd, monkeypatch):
    '''
    listing all containers
    '''
    # run main program subbing in new cmd arguments
    prog = sys.argv[0]
    monkeypatch.setattr("sys.argv", [prog,"list"])
    return_code = main()
    out = capfd.readouterr().out
    check_test_output("tests/good_outputs/test_list.txt",out)

def test_debug_flag(capfd, monkeypatch):
    '''
    check debug flag works
    '''
    # run main program subbing in new cmd arguments
    prog = sys.argv[0]
    monkeypatch.setattr("sys.argv", [prog,"--debug", "run", "TestContainer","hostname"])
    return_code = main()
    out = capfd.readouterr().out
    check_test_output("tests/good_outputs/test_debug.txt",out)
    assert return_code == 0
    
def test_build_and_run(monkeypatch):
    '''
    check build and run flags work 
    with a simple ubuntu container.
    '''
    
    prog = sys.argv[0]
    # first build container
    monkeypatch.setattr("sys.argv", [prog,"build", "TestContainer2"])
    return_code = main()
    assert return_code == 0
    # now run continer
    monkeypatch.setattr("sys.argv", [prog,"run", "TestContainer2","hostname"])
    return_code = main()
    assert return_code == 0

def test_unknown_operation():
# check for that we raise an error if operation is unknown
    containers = check_container_config(["tests/test_configs/valid.yaml"])
    with pytest.raises(CMD_FormatError):
        format_command("unknown","test",containers['Example_Model1'])

def test_config_file_flag(monkeypatch):
    '''
    check config_file flag works
    '''
    # run main program subbing in new cmd arguments
    prog = sys.argv[0]
    conf_file = "tests/test_configs/valid.yaml"
    monkeypatch.setattr("sys.argv", [prog,f"--config_file={conf_file}", "run", "Example_Model1","hostname"])
    return_code = main()
    assert return_code == 0