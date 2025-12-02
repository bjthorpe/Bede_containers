# tests for lcomand line argumants
import pytest
import sys
from util_functions import check_test_output
from run_container import main

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
    main()
    out = capfd.readouterr().out
    check_test_output("tests/good_outputs/test_list.txt",out)
