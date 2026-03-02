import os
from pathlib import Path
import pytest
import re
import logging

def cmd_output(message:str,length=80,sentinel='*',log=False,sep=" "):
    '''
    useful function for formatting logging/cmd output
    Params:

    message - string to output
    length - number of characters to output
    sentinel - character used to fill majority of line
    sep - character used to create space either side of the message
    length - max length of the outputted message
    log - flag to set if output goes to just the log or both log and stdout
    '''
    message = sep + message + sep
    result = f"{message:{sentinel}^{length}}"
    
    if log:
        logging.info(result)
    else:
        logging.info(result)
        print(result)

def check_test_output(golden_file, pytest_output,nlines=None):
    """
    Function to check that the stdout and stderr captured
    by pytest matches some known good output.

    Params:
    Golden_file - file containing known good output
    pytest_output - output from the test run
    nlines - (optional) if provided only check the first n lines 

    """
    # env variable to control if we want to use current output as new benchmark

    UPDATE_TESTS = os.getenv("UPDATE_TESTS")
    golden_file = Path(golden_file)

    if UPDATE_TESTS:
        golden_file.write_text(pytest_output)
        pytest.skip("Updated golden file")

    expected_output = golden_file.read_text()    
    if nlines == None:
        assert pytest_output == expected_output
    else:
        # only check first n lines
        OutputByLines = pytest_output.splitlines()
        ExpOutputByLines = expected_output.splitlines()
        assert OutputByLines[0:nlines] == ExpOutputByLines[0:nlines]
    
def create_build_options(options: dict) -> str:
    """
    function to create a build options string for Apptainer from a dict
    The returned string is of the form "--build-arg KEY1=VALUE1 -build-arg KEY2=VALUE2 ..."

    This is used by Apptainer with the build command to allow the use of placeholders
    using {{ variable }} syntax in the container definition files.
    (see https://apptainer.org/docs/user/main/cli/apptainer_build.html for more details).

    This allows us to use a single definition file to cover multiple pre-trained models
    from the same family and ultimately saves us using multiple definition files with
    only tiny differences.
    """
    if options:
        # check for huggingface api key
        if 'HF_AUTH' in options:
            # create a regex to check for valid API_keys 
            # (note: /w matches word characters i.e. letters, numbers and _)
            pattern = r'^\w+$'
            with open('Container_Configs/API_Keys/HF_AUTH.key', 'r') as file:
                lines = file.readlines()
                for line in lines:
                    line = line.replace("\n", "")
                    # skip comment lines
                    if line.startswith('#'):
                        continue
                    elif not re.match(pattern, line):
                        raise ValueError(f'Invalid hugging face API key: {pattern} found in {file.name}')
                    elif line=='1234ABCD':
                        cmd_output('*',sep="")
                        cmd_output("You have asked for a model that requires a HuggingFace API key to build.")
                        cmd_output(f"This needs to be provided in: {file.name}")
                        cmd_output("See the docs for more details")
                        exit(0)
                    else:
                        cmd_output(f"Found HuggingFace API key: {line}")
                        options['HF_AUTH'] = line
                    break
                
        build_args_str = "".join([f" --build-arg {k}={options[k]}" for k in options])
    else:
        build_args_str = ""
    return build_args_str


def which(program:str):
    '''
    Simple function pinched from stackoverflow https://stackoverflow.com/a/377028
    It performs the same function as the the bash command which. That is you pass 
    in the name of an executable. If it is on the system path it returns it's 
    location, otherwise it returns none.
    
    :param program: name of executable you'd like to check if it is on the system
                    path.
    '''
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ.get("PATH", "").split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None
