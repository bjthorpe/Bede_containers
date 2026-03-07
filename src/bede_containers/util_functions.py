import re
import logging
import os
from pathlib import Path
import sys

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
            toolkit_home=get_toolkit_home()
            with open(f'{toolkit_home}/Container_Configs/API_Keys/HF_AUTH.key', 'r') as file:
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
    It performs the same function as the bash command which. That is, you pass 
    in the name of an executable. If it is on the system path it returns it's 
    location, otherwise it returns none.
    
    :param program: name of executable you'd like to check if it is on the system
                    path.
    '''
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

def create_toolkit_home():
    '''
    function to setup the working directory for ML_toolkit
    This is ~/ML_toolkit by default  
    '''
    import argparse
    import shutil
    import yaml
    parser = argparse.ArgumentParser(
                    prog='setup-Ml_Toolkit',
                    description='Setup function to perform final install steps for ML_Toolkit')
    help_msg = f'Installation directory for ML_Toolkit, if not provided this defaults to {Path.home()}/ML_Toolkit'
    parser.add_argument('toolkit_home',nargs='?',default=f'{Path.home()}/ML_Toolkit',help=help_msg)
    parser.add_argument('-f', '--overwrite', action='store_true', help="force overwrite if directory exists")
    
    cmd_output("*",sep="",log=False)
    args = parser.parse_args()
    toolkit_home = args.toolkit_home
    if Path(toolkit_home).exists() and not args.overwrite:
        cmd_output(f'Installation path {toolkit_home} already exists',log=False)
        cmd_output('to avoid data loss please provide a different path. Or',log=False)
        cmd_output('use -f flag to force overwrite if you are sure it\'s safe.',log=False)
        cmd_output("*",sep="",log=False)
        return
    elif Path(toolkit_home).exists() and args.overwrite:        
        cmd_output(f'Overwriting existing directory {toolkit_home}',log=False)
        cmd_output("*",sep="",log=False)
        
        shutil.rmtree(toolkit_home)
    # create main directory

    cmd_output(f'creating ML_Toolkit home in {toolkit_home}',log=False)
    Path(toolkit_home).mkdir(parents=True, exist_ok=True)
    # create logs and images dirs
    Path(f'{toolkit_home}/logs').mkdir(parents=True, exist_ok=True)
    Path(f'{toolkit_home}/Images').mkdir(parents=True, exist_ok=True)

    # create symlinks to Container_Config, Definitions and scripts
    venv_root = Path(sys.prefix)
    dirs =['Container_Configs','Definitions','scripts']
    for dir in dirs:
        try:
            shutil.copytree(f'{venv_root}/{dir}', f'{toolkit_home}/{dir}')
        except Exception as e:
            cmd_output(f"An Error occurred while copying data: {e}")
        
    cmd_output("*",sep="",log=False)
    # add path to user config
    import yaml
    user_cfg={'ML_Toolkit_HOME': f'{toolkit_home}'} 
    with open(f"{venv_root}/user_config.yaml", "w") as f:
        yaml.dump(user_cfg,f)
    
    return

def get_toolkit_home():
    import yaml
    #get toolkit home from usr_config
    venv_root = Path(sys.prefix)
    with open(f"{venv_root}/user_config.yaml", "r") as f:
        usr_cfg = yaml.safe_load(f)
    
    toolkit_home = usr_cfg['ML_Toolkit_HOME']
    
    if toolkit_home == '':
        raise ValueError('could not find ML_Toolkit_HOME please ensure you have run init_ml-toolkit')
    
    return toolkit_home