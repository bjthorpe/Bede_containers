from pathlib import Path
import platform
import sys
import os
import textwrap
import yaml
from urllib.request import urlretrieve

START_MARK = "# >>> ML TOOLKIT >>>"
END_MARK = "# <<< ML TOOLKIT <<<"



def cmd_output(message:str,length=80,sentinel='*',sep=" "):
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
    messages=textwrap.wrap(message,length)
    for msg in messages:
        result = f"{msg:{sentinel}^{length}}"
        print(result)

def download_Nequip(url_yaml_file,toolkit_home):
    ''' 
    script to download Nequip model checkpoints
    from yaml file containing models names and urls
    '''
    with open(f"{toolkit_home}/Scripts/{url_yaml_file}") as path:
        urls = yaml.safe_load(path)
    Path(f'{toolkit_home}/Models/Nequip').mkdir(parents=True, exist_ok=True)
    cmd_output(f"Downloading Model checkpoint files for NequIP",sentinel=' ')
    for model in urls:
        print(f"Downloading: {model}")
        urlretrieve(urls[model],f"{toolkit_home}/Models/Nequip/{model}-0.1.nequip.zip")
    cmd_output("*",sep="")
    return

def detect_shell():
    ''' simple function to detect users shell'''
    shell = os.environ.get("SHELL")

    if shell:
        return os.path.basename(shell)

    try:
        import pwd
        return os.path.basename(pwd.getpwuid(os.getuid()).pw_shell)
    except Exception:
        return None


def get_rc_file(shell):
    ''' 
    simple function to get users rc file based on 
    shell specified, supports bash, zsh and fish
    '''
    home = Path.home()

    if shell == "bash":
        
        return home / ".bashrc"

    if shell == "zsh":
        return home / ".zshrc"

    if shell == "fish":
        return home / ".config/fish/config.fish"

    return None


def generate_block(shell, ml_home):
    ''' 
    generate a block of text to insert in users .rc 
    file bookended b y start and end marks to allow 
    us to check if file has already been modified previously.
    '''
    if shell == "fish":
        body = f"set -gx ML_TOOLKIT_HOME {ml_home}"
    else:
        body = f'export ML_TOOLKIT_HOME="{ml_home}"'

    command = f"{START_MARK}\n# ML Toolkit environment\n{body}\n{END_MARK}"
    return command


def update_rc_file(rc_file, block):
    '''
    function to add export command to users .rc file based on detected shell  
    '''
    rc_file.parent.mkdir(parents=True, exist_ok=True)

    if rc_file.exists():
        content = rc_file.read_text()
    else:
        content = ""

    if START_MARK in content and END_MARK in content:
        # Replace existing block
        start = content.index(START_MARK)
        end = content.index(END_MARK) + len(END_MARK)
        new_content = content[:start] + block + content[end:]
    else:
        # Append block
        new_content = content + "\n" + block + "\n"

    rc_file.write_text(new_content)
    return
def get_user_input(msg:str,dir:str):
    while True:
        user_input = input(f'{msg} yes/no: ')

        if user_input.lower() == 'yes' or user_input.lower() == 'y':
            print(f'updating {dir}')
            return True
        elif user_input.lower() == 'no' or user_input.lower() == 'n':
            print(f'Skipping update for {dir}')
            return False
        else:
            print('Type yes or no')

def create_toolkit_home():
    '''
    function to setup the working directory for ML_toolkit
    This is ~/ML_toolkit by default  
    '''
    import argparse
    import shutil

    # check what we are running on
    system = platform.system()

    if system == "Windows":
        cmd_output("Error: Windows is not supported for this installer.",sentinel=' ')
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
                    prog='setup-Ml_Toolkit',
                    description='Setup function to perform final install steps for ML_Toolkit')
    help_msg = f'Installation directory for ML_Toolkit, if not provided this defaults to {Path.home()}/ML_Toolkit'
    parser.add_argument('-p','--toolkit_home',nargs='?',default=f'{Path.home()}/ML_Toolkit',help=help_msg)
    parser.add_argument('-f', '--overwrite', action='store_true', help="force overwrite if directory exists")
    parser.add_argument('-u', '--update', action='store_true', help="update existing installation")
    # check if using conda or venv
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        venv_root = conda_prefix
    else:
        venv_root = Path(sys.prefix)

    cmd_output("*",sep="")
    args = parser.parse_args()
    toolkit_home = args.toolkit_home
    dirs =['Container_Configs','Definitions','Scripts','API_Keys']
    if not args.update:
        if Path(toolkit_home).exists() and not args.overwrite:
            cmd_output(f'Installation path {toolkit_home} already exists',sentinel=' ')
            cmd_output('to avoid data loss please provide a different path. Or',sentinel=' ')
            cmd_output('use -f flag to force overwrite if you are sure it\'s safe.',sentinel=' ')
            cmd_output("*",sep="")
            return
        elif Path(toolkit_home).exists() and args.overwrite:        
            cmd_output(f'Overwriting existing directory {toolkit_home}',sentinel=' ')
            cmd_output("*",sep="")
            shutil.rmtree(toolkit_home)
    
        # create main directory

        cmd_output(f'creating ML_Toolkit home in {toolkit_home}',sentinel=' ')
        Path(toolkit_home).mkdir(parents=True, exist_ok=True)
        # create logs and images dirs
        Path(f'{toolkit_home}/logs').mkdir(parents=True, exist_ok=True)
        Path(f'{toolkit_home}/Images').mkdir(parents=True, exist_ok=True)
        Path(f'{toolkit_home}/Models').mkdir(parents=True, exist_ok=True)
        # copy files into Container_Config, Definitions and Scripts
        for dir in dirs:
            try:
                shutil.copytree(f'{venv_root}/{dir}', f'{toolkit_home}/{dir}',dirs_exist_ok=True)
            except Exception as e:
                cmd_output(f"An Error occurred while copying data: \n {e}",sentinel=' ')
                sys.exit(1)
    else:
        toolkit_home = os.environ.get("ML_TOOLKIT_HOME",'')
        if toolkit_home == '':
            cmd_output(f'Can not find existing installation of ml-toolkit to update',sentinel=' ')
            cmd_output(f'please set the ML_TOOLKIT_HOME environment variable',sentinel=' ')
            sys.exit(1)
        cmd_output(f'updating existing ML_Toolkit found in {toolkit_home}',sentinel=' ')

        for dir in dirs:
            overwrite=True
            try:
                overwrite = get_user_input(f"Update {dir}?",dir)
                if overwrite:
                    shutil.copytree(f'{venv_root}/{dir}', f'{toolkit_home}/{dir}',dirs_exist_ok=True)
            except Exception as e:
                cmd_output(f"An Error occurred while copying data: \n {e}",sentinel=' ')
                sys.exit(1)
        
    cmd_output("*",sep="")

    download_Nequip("Nequip_urls.yaml",toolkit_home)
    
    shell = detect_shell()

    if not shell:
        cmd_output(f"Could not automatically detect user shell.",sentinel=' ')
        cmd_output(f"WARNING: You will need to set the environment variable ML_TOOLKIT_HOME={toolkit_home} each time you use ML_toolkit",sentinel=' ')
        return
    
    cmd_output(f"User shell automatically detected as {shell}",sentinel=' ')

    rc_file = get_rc_file(shell)

    if not rc_file:
        cmd_output(f"Unsupported shell: {shell}",sentinel=' ')
        cmd_output(f"WARNING: You will need to set the environment variable ML_TOOLKIT_HOME={toolkit_home} each time you use ML_toolkit",sentinel=' ')
        return

    block = generate_block(shell, toolkit_home)

    update_rc_file(rc_file, block)

    cmd_output(f"ML_TOOLKIT_HOME configured in {rc_file}",sentinel=' ')
    cmd_output("*",sep="")    
    cmd_output("Please restart your terminal or run:",sentinel=' ')
    
    if shell == "fish":
        cmd_output(f"source {rc_file}",sentinel=' ')
    else:
        cmd_output(f"source {rc_file}",sentinel=' ')
    cmd_output("*",sep="")
    return
