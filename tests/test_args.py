# tests for lcomand line argumants
import pytest
import sys
from util_functions import check_test_output
from run_container import main

def test_verbose(capfd, monkeypatch):
    monkeypatch.setattr("sys.argv", ["--verbose","run","TestContainer","cowsay","It Works"])
    main()
    out = capfd.readouterr().out
    check_test_output("tests/good_outputs/test_verbose.txt",out)

