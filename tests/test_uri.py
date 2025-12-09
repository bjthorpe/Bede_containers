# tests for loading config file ect..
import pytest
from check_URI import check_container_def

def test_validation_docker():
    uri = 'docker://alpine:latest'
    test = check_container_def(uri)
    assert test == uri

def test_validation_oras():
    uri = 'oras://docker.io/davedykstra/lolcow'
    test = check_container_def(uri)
    assert test == uri

def test_validation_path_rel():
    # test for relative path
    uri = "Definitions/cowsay.def"
    test = check_container_def(uri)
    assert test == uri
   
def test_validation_default_docker():
    # test that continer defs default to dockerhub    
    uri = "alpine:latest"
    test = check_container_def(uri)
    assert test == f"docker://{uri}"

def test_validation_library():
    uri = 'library://your-name/project-dir/my-container:latest'
    test = check_container_def(uri)
    assert test == uri

def test_validation_err():
    with pytest.raises(ValueError):
        test = check_container_def("wtf is this?")

def test_docker_no_tag():
    # correct docker string but no tag
    with pytest.raises(ValueError):
        test = check_container_def('alpine')