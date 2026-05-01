# tests for Apptainer installation
import pytest
import subprocess
from bede_containers.run_container import main
from bede_containers.util_functions import get_toolkit_home
from pathlib import Path
import os
import sys
import glob
import re

def build_test_container(model):
    toolkit_home = get_toolkit_home()
    sif_file = glob.glob(f'{toolkit_home}/Images/*/{model}.sif')
    if sif_file == []:
        # sif file does not exists so build it
        apptainer_command = f"ml-toolkit build {model}"
        print(apptainer_command)
        proc = subprocess.run(apptainer_command, shell=True)
        try:
            proc.check_returncode()
        except subprocess.CalledProcessError as e:
            print(f"An error occurred. Container exited with the exit code {e.returncode}:")
            raise e
        cleanup = True
    elif len(sif_file) > 1:
        print(f"found {len(sif_file)} models with the same name {model}")
        for file in sif_file:
            print(file)
        print("to be on the safe side the test will not continue")
        sys.exit(1)
    else:
        # sif file already exists so just use that and don't cleanup
        cleanup = False
    return cleanup

def cleanup_test_container(model_name):
    toolkit_home = get_toolkit_home()
    sif_file = glob.glob(f'{toolkit_home}/Images/*/{model_name}.sif')
    os.remove(sif_file[0])


def get_task(model_name):
    
    # models from Meta that require task
    Meta_UMA = ["uma-s-1p1","uma-s-1","uma-m-1p1"]
    # multi dataset models from 7net that require task
    SEVENNET_multi = ['sevennet-omni','sevennet-omni-i8',
                      'sevennet-omni-i12','sevennet-mf-ompa']
    
    if model_name.lower() in  Meta_UMA:
        task = 'omat'
    elif model_name.lower() in SEVENNET_multi:
        task = 'omat24'
    else:
        task = ''
    return task

def test_ASE(request):
    """
    Test to check ASe is working correctly with a given ml model.
    By calculating the potential of a H2 molecule. 
    
    Notes: 
    1)  The code does not know or care if the output is accurate, or even correct. 
        All it cares about is that ASE does not crash.
    """
    model_names = request.config.getoption("--model_names")
    toolkit_home=get_toolkit_home()
    for model in model_names:
        cleanup = build_test_container(model)
        # get task option if needed
        task = get_task(model)
        # reformat task for input into sever method, if needed
        if task!='':
            task=f'--task={task}'
        #start python server
        apptainer_command = f"ml-toolkit run {model} python {toolkit_home}/Scripts/test_ASE.py {model} {task}"
        
        try:
            proc = subprocess.run(apptainer_command, shell=True,check=True)
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Container start failed with error: {e}")
        finally:
            if cleanup:
                cleanup_test_container(model)
    return