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

def create_input_files(model_name:str,path:str,task:str=''):
    import shutil
    search_text = "{MODEL_NAME}"
    search_text2 = "{TASK}"
    # add -t option if requested
    if task!='':
        task = f'-T {task}'
    print(f"writing new input files for {model_name}")
    # cell file does not change so just create a copy
    shutil.copy(f'{path}/Si_master.cell', f'{path}/Si_{model_name}.cell')
    # update param file with model_name
    with open(f'{path}/Si_master.param', 'r') as infile:
        data = infile.read()
        data = data.replace(search_text, model_name)
        data = data.replace(search_text2, task)

    with open(f'{path}/Si_{model_name}.param', 'w') as outfile:
        outfile.write(data)
    return

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

def cleanup_output_files(model_name,folder_path,fileprefix='Si_'):
    import glob
    import os

    # Files you want to KEEP (full paths recommended)
    keep_files = {
        os.path.join(folder_path, f"{fileprefix}{model_name}.param"),
        os.path.join(folder_path, f"{fileprefix}{model_name}.cell"),
    }

    # Get all files in the folder
    all_files = glob.glob(os.path.join(folder_path, f"{fileprefix}{model_name}*"))

    for file_path in all_files:
        if os.path.isfile(file_path) and file_path not in keep_files:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        else:
            print(f"Kept: {file_path}")
    return

@pytest.mark.CASTEP
@pytest.mark.skip
def test_FileMethod(request):
    """
    Test to check the CASTEP File Method is working correctly with a given ml model.
    By running a simple Si bandstructure calculation. 
    
    Notes: 
    1)  You will need a working version of CASTEP installed and available on the 
        system PATH.
    2)  The code does not know or care if the output is accurate, or even correct. 
        All it cares about is that CASTEP does not crash.
    """
    model_names = request.config.getoption("--model_names")
    DATA_DIR = str(Path(__file__).parent / "File-method")
    for model in model_names:
        cleanup_container = build_test_container(model)
        # get task option if needed
        task = get_task(model)
        create_input_files(model,f"{DATA_DIR}/Input_files",task)
        apptainer_command = f"castep.serial {DATA_DIR}/Input_files/Si_{model}"
        proc = subprocess.run(apptainer_command, shell=True)
        try:
            proc.check_returncode()
        except subprocess.CalledProcessError as e:
            print(f"An error occurred. Container exited with the exit code {e.returncode}:")
            print(e)
            raise e
            assert proc.returncode == 0
        finally:
            # always cleanup but only the container if we built it during the test
            if cleanup_container:
                cleanup_test_container(model)
            cleanup_output_files(model,f"{DATA_DIR}/Input_files")
        assert proc.returncode==0    
    return

@pytest.mark.CASTEP
def test_ServerMethod(request):
    """
    Test to check the CASTEP server Method is working correctly with a given ml model.
    By running a graphene bandstructure calculation. 
    
    Notes: 
    1)  You will need a working version of CASTEP26 installed and available on the 
        system PATH.
    2)  The code does not know or care if the output is accurate, or even correct. 
        All it cares about is that CASTEP does not crash.
    """
    model_names = request.config.getoption("--model_names")
    DATA_DIR = str(Path(__file__).parent / "Server-method")
    os.chdir(DATA_DIR)
    for model in model_names:
        cleanup_container = build_test_container(model)
        # get task option if needed
        task = get_task(model)
        # reformat task for input into sever method, if needed
        if task!='':
            task=f'--task={task}'
        #start python server
        apptainer_command = f"ml-toolkit start {model} {task}"
        proc = subprocess.run(apptainer_command, shell=True)
        try:
            proc.check_returncode()
        except subprocess.CalledProcessError as e:
            print(f"An error occurred. Container exited with the exit code {e.returncode}:")
            print(e)
            raise e
        assert proc.returncode==0
        # run castep
        apptainer_command = f"castep.serial Input_files/graphene"
        proc = subprocess.run(apptainer_command, shell=True)
        try:
            proc.check_returncode()
        except subprocess.CalledProcessError as e:
            print(f"An error occurred. Container exited with the exit code {e.returncode}:")
            print(e)
            raise e
        finally:
            # always cleanup but only the container if we built it during the test
            if cleanup_container:
                cleanup_test_container(model)
            #cleanup_output_files(model,f"{DATA_DIR}/Input_files",fileprefix='graphene_')
            # also always stop the server
            apptainer_command = f"ml-toolkit stop {model}"
            proc = subprocess.run(apptainer_command, shell=True)
        assert proc.returncode==0
    return