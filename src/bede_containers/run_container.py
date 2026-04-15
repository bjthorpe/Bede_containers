import argparse
from pathlib import Path
import subprocess, sys, yaml
from dataclasses import dataclass, field
from typing import List
from dacite import from_dict
from .check_yaml import DuplicateKeyDetector, DuplicateKeyError
from .check_yaml import is_valid_name
from .check_URI import check_container_def
from .util_functions import create_build_options, cmd_output, which, get_toolkit_home,check_model_implemented
from .version import __version__
import logging
import sys
import socket
import time

def is_server_ready(host, port, message="ping", timeout=2):
    ''' 
    Function to send special health check message 
    to server to check that it is indeed ready to go.
    '''
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
        # byte string in hex used for health check
        # For health checking we send the string CHECK
        # to the TCP server and expects the (string) response ALIVE.
        # N.B. 05000000 is 5 in an unsigned integer in little enidian 
        # specifying length of sent message and 434845434B is CHECK in hex.
            magic_string = bytes.fromhex('05000000434845434B')
            sock.sendall(magic_string)
            sock.settimeout(timeout)
            response = sock.recv(1024)
            return len(response) > 0
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def wait_for_server(host, port, retries=5, delay=10):
    '''
    The python server can be annoyingly slow to start up.
    This function waits for it to start and retries a 
    fixed number of times before simply giving up.
    '''
    print(f"waiting for python server to start")
    time.sleep(delay)
    for attempt in range(1, retries + 1):
        if is_server_ready(host, port+1, message="CHECK", timeout=2):
            print(f"Python Server is ready on {port}")
            return True
        else:
            print(f"Attempt {attempt} of {retries}: Python Server not ready")
            print(f"waiting for {delay} seconds before retry")
            time.sleep(delay)

    return False

def is_writable(file):
    '''
    check that given file has write permission
    '''
    import os
    try:
        with open(file, 'w') as f:
            pass
        os.remove(file)
        return True
    except OSError:
        return False

toolkit_home = get_toolkit_home()

logging.basicConfig(
    level=logging.INFO,
    filename=f"{toolkit_home}/logs/log.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

@dataclass
class ContainerConfig:
    description: str
    image_file: str = field(default="")
    container_definition: str = field(default="")
    encryption_key: str = field(default="")
    shared_directories: List[str] = field(default_factory=list)
    dont_mount: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    encrypted: bool = field(default=False)
    device: str = field(default='cuda')
    build_options: dict = field(default_factory=dict)
    CASTEP: bool = field(default=False)
    output_file: str = field(default=str(Path.cwd()))
    available_tasks: List[str] = field(default_factory=list)
    
class CMD_FormatError(Exception):
    """
    Custom Exception to be raised when using an operation that
    is not valid or that has not been implemented. This should
    not normally be raised as its handled in the command line
    options but this is here in case someone adds an option
    in the future but forgets to handle it in format_command.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def check_config_options(container:dict,name:str,filename:str):
    '''
    Take in dict of parameters defined in the yaml file and 
    check to see if they are valid class members for ContainerConfig.

    '''
    #create a blank default config to extract a list of valid members 
    blank_config = ContainerConfig(description='test')
    valid_options = list(blank_config.__dict__.keys())
    
    container_options = list(container.keys())
    for option in container_options:
        if option in valid_options:
            # logging.info(f"{option}: {container[option]}")
            continue
        # check for case sensitivity and fix if necessary
        elif option.lower() in valid_options:
            logging.warning(f"Option: {option} is not valid in config of Contatiner {name}. Assuming you meant: {option.lower()}")
            new_key = option.lower()
            container[new_key] = container[option]
            container.pop(option)
            #logging.info(f"{new_key}: {container[new_key]}")
            continue
        else:
            raise ValueError(
                    f"Error in config of Model name {name} in {filename}:\n\
                        Option:{option} is not recognised this must be one of:\n\
                        {valid_options}"
                )
    return container
    
def list_valid_config_options() -> List:
    '''
    Function to create a blank default config,
    extract a list of members then return a list.

    '''
    #create a blank default config to extract a list of valid members 
    blank_config = ContainerConfig(description='test')
    valid_options = list(blank_config.__dict__.keys())
    return valid_options

def check_container_config(config_files: list):
    """
    Function to load configs from list of yaml files, check for errors
    and create dict of all container configs with names as keys.
    """
    Containers = {}
    toolkit_home = get_toolkit_home()
    cmd_output("Checking config files.",only_log=True,sentinel=" ")
    for conf_file in config_files:
        with open(conf_file, "r") as file:
            cmd_output(f"Reading config from file: {file.name}",sentinel='-',only_log=True)
            all_containers = yaml.load(file, Loader=DuplicateKeyDetector)

        for key in all_containers:
            # check model name does not contain anything surprising.
            if not is_valid_name(key):
                raise ValueError(
                    f"Model name {key} in {file.name} is not valid \
                                 model names must contain only, letter number and/or underscores"
                )
            all_containers[key] = check_config_options(all_containers[key],key,file.name)
            result = from_dict(data_class=ContainerConfig, data=all_containers[key])
            # check for duplicate model names
            if key not in Containers:
                Containers[key] = result
            else:
                raise DuplicateKeyError(
                    f"Error in config of model {key} in {conf_file} \
                        this appears to have the same \n \
                        name as another model. Two models must \
                        not share the same name."
                )
            # if no image file is given set default image file name as "model_name.sif"
            if result.image_file == "":
                result.image_file = f"{toolkit_home}/Images/{key}.sif"
            # if path is not absolute make it relative to toolkit home
            elif not Path(result.image_file).is_absolute():
                result.image_file = f"{toolkit_home}/{result.image_file}"
            
            if result.image_file.endswith(".sif"):
                # Make parent directories if they don't exist
                Path(result.image_file).parent.mkdir(parents=True, exist_ok=True)
            else:
                raise ValueError(
                    f"Error in config of Model name {key} in {file.name}:\n\
                                 image file name {result.image_file} must end in .sif"
                )
            # if no definition file is given set default definition file name as "model_name.def"
            if result.container_definition == "":
                result.container_definition = f"{toolkit_home}/Definitions/{key}.def"
            else:
                result.container_definition = check_container_def(
                    result.container_definition
                )

            # do some checks for shared directory if defined
            if result.shared_directories != []:
                for directory in result.shared_directories:
                    P = Path(directory)
                    if not P.exists():
                        err_msg = f"The shared directory {directory} \n \
                            defined in {file.name} does not exist. "
                        raise FileNotFoundError(err_msg)
                    if P.is_file():
                        err_msg = f"The shared directory {directory} \n \
                        defined in {file.name} should be directory not a file."
                        raise ValueError(err_msg)
                    
                    if P.is_symlink():
                        err_msg = f"The shared directory {directory} \n \
                        contains a symbolic link. Apptainer will not  \n \
                        be able to mount this. \n \
                        Please use the absolute path to this directory"
                        raise ValueError(err_msg)
                    
            # do some checks for automatic mount flags if needed
            if result.dont_mount != []:
                available_flags = ['home','cwd']
                for flag in result.dont_mount:
                    if flag not in available_flags:
                        err_msg = f"{flag} is not a valid option for the dont_mount parameter in {file.name} \n \
                        This should be one of {available_flags}"
                        raise ValueError(err_msg)

        logging.info(f"{file.name} OK")
    msg = "All config files look good"
    cmd_output(msg,sentinel=" ")
    return Containers


def load_container_config_file(container_config):
    """
    Load the config file, do some basic sanity checks
    and then return a dict of containers with model names
    as the keys.
    """
    container_config = Path(container_config)

    if container_config.is_dir():
        # directory containing config files
        config_files = []
        for file in container_config.glob("*.yaml"):
            config_files.append(Path(file))
    else:
        # single named config file
        if not container_config.exists():
            raise FileNotFoundError(f"Could not find config file {container_config}")

        if container_config.suffix not in [".yml", ".yaml"]:
            raise ValueError(
                f"config file {container_config} is not a \
                yaml file, \n the filename must end in .yml \
                or .yaml"
            )
        # create list with single container config file in it
        config_files = [container_config]

    Containers = check_container_config(config_files)

    return Containers


def image_exists(image_file: str):
    if not Path(image_file).exists():
        msg = f"A container with the name {image_file} \
            \n could not be found please run build first."
        raise FileNotFoundError(msg)
    return


def format_command(
    operation:str,
    model_name: str,
    Container: ContainerConfig,
    CMD_Options
):
    """
    Function to create appropriate Apptainer command based on the
    operation requested.
    """

    image = Container.image_file
    definition = Container.container_definition
    
    # set GPU flags
    # use Nvidia GPU
    if Container.device.lower() == 'cuda':
        gpu_flag = " --nv "
    # use AMD GPU
    elif Container.device.lower() == 'rocm':
        gpu_flag = " --rocm "        
    # use CPU
    elif Container.device.lower() == 'cpu':
        gpu_flag = " "
    # Default to cpu and print out warning message if device is unknown
    else:
        logging.warning(f"Device {Container.device} in config file for {model_name} not recognised.")
        logging.warning(f"Defaulting to cpu for calculations.")
        gpu_flag = ""
   
    # turn off automatic mounts if requested
    if Container.dont_mount != []:
        # remove auto-mount for users home directory if requested
        flags = []
        if 'home' in Container.dont_mount:
            logging.info(f"Removing access to {Path.home()} within the container")
            flags.append("home")
        else:
            logging.info(f"Granting access to {Path.home()} within the container")
        # remove auto-mount for current working directory if requested
        if 'cwd' in Container.dont_mount:
            logging.info(f"Removing access to {Path.cwd()} within the container")
            flags.append("cwd")
        else:
            logging.info(f"Granting access to {Path.cwd()} within the container")

        # convert list of flags into comma separated string
        flags_str = ''.join([item + ',' for item in flags])[:-1]
        no_mnt_flag = f" --no-mount {flags_str} "
    else:
        no_mnt_flag = ""

    # and bind mounts for directories if requested
    if Container.shared_directories != []:
        # we should always at least bind toolkit home
        dirs = [toolkit_home]
        for directory in Container.shared_directories:
            logging.info(f"Granting access to {directory} within the container")
            dirs.append(directory)
        # convert list of flags into comma separated string
        flags_str = ''.join([item + ',' for item in dirs])[:-1]
        bind_opt = f" --bind {flags_str} "
    else:
        bind_opt = f" --bind {toolkit_home} " 
    # check for encryption and add appropriate flags
    if Container.encrypted:
        if Container.encryption_key != "":
            enc_flag = " --passkey "
        else:
            enc_flag = f" --pem-path {Container.encryption_key} "
    else:
        enc_flag = ""

    if operation == "run":
        if (not CMD_Options['interactive'] and CMD_Options['cmd']==[]):
            print("error: the following arguments are required: cmd")
            sys.exit(12)
        cmd = " ".join(CMD_Options['cmd'])

        image_exists(image)
        if Path(image).is_dir():
            write_flag = " --writable "        
        else:    
            write_flag = ""

        # apptainer shell and apptainer exec share the same cmd options so I just combined the two
        if CMD_Options['interactive']:
            msg = "Running in interactive mode"
            apptainer_cmd = "shell"
        else:
            msg = "Running"
            apptainer_cmd = "exec"

        apptainer_command = f"apptainer {apptainer_cmd}{enc_flag}{write_flag}{no_mnt_flag}{bind_opt}{gpu_flag}{image} {cmd}"

    elif operation == "build" or operation == "load":
        if CMD_Options['writable']:
            sand_flag = " --sandbox "
            msg = "Building Writable container"
        else:    
            sand_flag = ""
            msg = "Building"
        # force overwrite of existing build if requested
        if CMD_Options['force']:
            force='-F'
        else:
            force=''
        # Make parent directory(s) of image file if it does not exist
        Path(Container.image_file).parent.mkdir(parents=True, exist_ok=True)
        build_options_str = create_build_options(Container.build_options)

        apptainer_command = (
            f"apptainer build{force}{build_options_str}{sand_flag}{enc_flag}{gpu_flag}{image} {definition}"
        )
    # convert existing container to/from editable sandbox
    elif operation == "convert":
        
        image_exists(image)

        if Path(Container.image_file).is_file():
            msg = "Converting to Writable Sandbox"
            sand_flag = " --sandbox "
            task = 'writable sandbox'
        else: 
            msg = "Converting to .sif file"
            sand_flag = " "
            task = '.sif file'

        print(f'you are about to convert {Container.image_file} to a {task} is this correct?')
        user_input = input('(yes/no)?')
        
        while True:
            if user_input.lower() == 'yes' or user_input.lower() == 'y':
                break
            elif user_input.lower() == 'no' or user_input.lower() == 'n':
                print("convert aborted")
                sys.exit(0)
            else:
                print('Type yes or no')

        apptainer_command = (
            f"apptainer build -F {sand_flag}{enc_flag}{image} {image}"
        )
        
    elif operation == "start":
        msg = "Starting"
        image_exists(image)
        if Path(image).is_dir():
            write_flag = " --writable "        
        else:    
            write_flag = ""
        # check file for stdout/stderr is writable
        if Container.output_file == '':
            Container.output_file = f'{Path.cwd}/{model_name}'
        if is_writable(Container.output_file):
            cmd_output('*',sep='',only_log=True)
            cmd_output(f"Container output can be found in {Container.output_file}.out and {Container.output_file}.err",only_log=True)
            cmd_output('*',sep='',only_log=True)
            Container.output_file = f'{toolkit_home}/logs/{model_name}'
        else:
            cmd_output('*',sep='',only_log=True)
            cmd_output(f"warning: output directory {Container.output_file} is not writable",only_log=True)
            cmd_output(f"output will default to {toolkit_home}/logs/{model_name}",only_log=True)
            cmd_output('*',sep='',only_log=True)

        # containers for use with CASTEP have a slightly different startup command.
        if Container.CASTEP:
            if CMD_Options['port']==None:
                # use default port for castep
                CMD_Options['port']=5000

            #pass in task argument if needed
            if CMD_Options['task'] !='':
                task=f'-T {CMD_Options['task']}'
            else:
                task=''
            cmd = f"-p {CMD_Options['port']} -t {CMD_Options['timeout']} -N {CMD_Options['num_servers']} {task}"
        else:
            cmd =''
        apptainer_command = f"apptainer instance start --env OUTPUT_FILE={Container.output_file}/{model_name} {enc_flag}{write_flag}{no_mnt_flag}{bind_opt}{gpu_flag}{image} {model_name} {cmd}"

    elif operation == "stop":
        msg = "Stopping"
        image_exists(image)
        apptainer_command = f"apptainer instance stop {model_name}"

    else:
        # this path should not happen but just in case.
        apptainer_command = ""
        raise CMD_FormatError(
            f"{operation} is Not a valid operation,"
            + "This should not happen. Did you add an option"
            + "and forget to update format_command?"
        )
    cmd_output('*',sep='')
    cmd_output(f"{msg}: {model_name}")
    cmd_output('*',sep='')
    return apptainer_command


def parse_cmd_arguments():
    """
    Function to handle parsing of command line arguments
    """

    parser = argparse.ArgumentParser(
        description="A CLI tool for easily running AI/ML containers on Bede."
    )

    # Subparser to create subcommands for each operation (run, build, load ect.)
    subparsers = parser.add_subparsers(
        dest="operation", required=True, help="Operation to perform."
    )
    # sub-parser for the run operation
    run_parser = subparsers.add_parser("run", help=f"Run command(s), with the Container")

    run_parser.add_argument("model_name", type=str, help="Name of Model to use")

    run_parser.add_argument("cmd", type=str, nargs=argparse.REMAINDER, help="Command(s) to run")
    run_parser.add_argument("--interactive", action="store_true", help="run in interactive mode, ignores extra commands")

    # sub-parser for the convert operation
    conv_parser = subparsers.add_parser("convert", help=f"Convert existing Model Container to/from editable/static, useful for development as it saves having to re-build containers when making small changes.")

    conv_parser.add_argument("model_name", type=str, help="Name of Model to use")

    # sub-parser for the build operation
    build_parser = subparsers.add_parser(
        "build", help="Build the Container, exactly equivalent to load"
    )

    build_parser.add_argument("model_name", type=str, help="Name of Model to use")
    build_parser.add_argument("--writable", action="store_true", help="Build container as an editable sandbox, useful for dev/debugging as it enables you to freely edit the container.")   
    build_parser.add_argument("-f","--force", action="store_true", help="Force overwrite of existing container.")

    # sub-parser for the load operation
    load_parser = subparsers.add_parser(
        "load", help="Build the Container, exactly equivalent to build"
    )

    load_parser.add_argument("model_name", type=str, help="Name of Model to use")
    load_parser.add_argument("--writable", action="store_true", help="Build container as an editable sandbox, useful for dev/debugging. Run with --writable to freely edit the container.")   

    # sub-parser for the list operation
    list_parser = subparsers.add_parser("list", help="List available containers")

    list_parser.add_argument(
        "-g","--group", type=str, default="", help="optional group of containers to list"
    )
    list_parser.add_argument(
        "-m","--model_name", type=str, default="", help="optional group of containers to list"
    )
    list_parser.add_argument(
        "--long_desc","-l", action="store_true", help="Output full descriptions, default is truncated to 80 characters."
    )
    # sub-parser for the start operation
    start_parser = subparsers.add_parser("start", help="Start Container as background process.")

    start_parser.add_argument("model_name", type=str, help="Name of Model to use")    
    start_parser.add_argument("-p","--port", type=int, default=None, help="Used with CASTEP, tcp network port, if provided ml-toolkit will check for network traffic on the given tcp port once the container has started. Used to verify a server has started correctly. ")    
    start_parser.add_argument("-t","--timeout", type=int, default=5, help="time in seconds before server times out. Default: 10")
    start_parser.add_argument("-n","--num_servers", type=int, default=1, help="Used with CASTEP, number of python servers to spawn. Default: 1")                       
    start_parser.add_argument("-r","--num_retry", type=int, default=3, help="number of times to retry when waiting for python server. Default: 5")
    start_parser.add_argument("-T","--task", type=str, default='', help="Task to perform, required for all Meta UMA and selected SevenNet models, ignored by all others. See the docs for valid options")

    # sub-parser for the stop operation
    stop_parser = subparsers.add_parser(
        "stop", help="Stop container that is running in the background"
    )

    stop_parser.add_argument("model_name", type=str, help="Name of Model to use")

    # other arguments for main parser
    parser.add_argument(
        "--config_file", type=str, default=None, help="path to Config file for Models"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print generated Apptainer command instead of running container, useful for sanity checking",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )   

    args = parser.parse_args()
    return args

def truncate_string(s, length):
    if len(s) > length:
        return s[:length-3] + '...'  # Subtract 3 to add ellipsis
    return s

from difflib import get_close_matches

def find_in_list(query, items, cutoff=0.8):
    """
    query: string to search for
    items: list of strings
    cutoff: similarity threshold (0 to 1)

    returns: matches OR suggestion string
    """
    query_lower = query.lower()
    items_lower = [item.lower() for item in items]

    # Find close matches
    matches_lower = get_close_matches(query_lower, items_lower, cutoff=cutoff)

    if matches_lower:
        return True

    return False

def list_containers(Containers: dict, group: str = "",long_desc=False,model_name:str =''):
    '''
    Print filtered list of containers to stdout, 
    formatted for readability
    
    :params
        Containers: dictionary of available containers, keys are 
                    container names and values are the groups it 
                    belongs to.
        group:      group to filter output by
        long_desc:  output full descriptions

    '''
    msg_length=40
    cmd_output("*",sep="",length=msg_length)
    cmd_output("Currently available containers: ",length=msg_length)
    cmd_output("*",sep="",length=msg_length)
    print(f"Name:          | Groups:    | Description:")
    cmd_output("-",sep="",sentinel='-',length=msg_length)
    # go through all models
    if model_name=="":
        for key, value in Containers.items():
            if find_in_list(group, value.groups) or group == "":
                if long_desc:
                    desc = value.description
                else:
                    desc = truncate_string(value.description,80)
                output = f"{key:<15} | {', '.join(value.groups)} | {desc}"
                print(output)
    # list info for just one model
    elif model_name in Containers:
        if find_in_list(group, Containers[model_name].groups) or group == "":
            if long_desc:
                desc = Containers[model_name].description
            else:
                desc = truncate_string(Containers[model_name].description,80)
            output = f"{model_name:<15} | {', '.join(Containers[model_name].groups)} | {desc}"
            print(output)       
    
    else:
        #model not found
        print(f"There is no model {model_name} available")
    return

def config_to_log(config:ContainerConfig,model_name:str):
    cmd_output(f"Loading Container: {model_name}",sentinel='-',only_log=True)

    for key, value in config.__dict__.items():
        logging.info(f"{key}: {value}")

def check_task(task,available_tasks,model_name):
    '''
    Function to check if task argument is a valid option 
    from the list read in from the yaml file.
    '''
    if available_tasks==[]:
        # no tasks required 
        return
    if task=='':
        print(f'Input argument --task is required for {model_name}.')
        print(f'This must be one of: {available_tasks}.')
        sys.exit(12)
    elif task not in available_tasks:
        print(f'unknown task: {task} for {model_name}.')
        print(f'This must be one of: {available_tasks}.')
        sys.exit(11)
    else:
        print(f'Performing task: {task} for {model_name}.')
        return
    
###############################################################################
# Main program starts here
###############################################################################
def main() -> int:
    args = parse_cmd_arguments()
    if args.config_file:
        container_config = Path(args.config_file)
    else:
        toolkit_home = get_toolkit_home()
        container_config = Path(f"{toolkit_home}/Container_Configs/")
    cmd_output("*",sep="")
    cmd_output("Loading Model Config Files")
    cmd_output("*",sep="")
    
    Containers = load_container_config_file(container_config)

    if args.operation.lower() == "list":
        # just list all detected containers then exit
        list_containers(Containers, args.group,args.long_desc, args.model_name)
        return 0

    if not hasattr(args,'interactive'):
        args.interactive=False
  
    shell=args.interactive

    model_name = args.model_name

    if model_name not in Containers.keys():
        raise ValueError(
            f"no model named {model_name} was found in a config file.\n \
                            Model must be one of \n{list(Containers.keys())}"
        )
    check_model_implemented(model_name)
    config_to_log(Containers[model_name],model_name)
    # check to see if Apptainer is available on the system path
    if which('apptainer') is None:
        msg = f"Apptainer does not appear to be installed or is not "
        msg2 = "available on the system path. Please check Your installation."
        raise ValueError(msg+msg2)
    
# we don't need to pass in any cmd arguments if using interactive shell
    if shell:
        args.cmd=[]

    if not hasattr(args,'cmd'):
        args.cmd=[]

    # check --task option if required by the model
    if hasattr(args,'task'):
        check_task(args.task,Containers[model_name].available_tasks,model_name)

    # get dict of cmd arguments
    cmd_options= vars(args)
    apptainer_command = format_command(args.operation, model_name, Containers[model_name],cmd_options)

    if args.debug:
        print("Debug enabled")
        print("current config will run the following command:")
        print(apptainer_command)
    else:
        logging.info(f"Running command: {apptainer_command}")
        proc = subprocess.run(apptainer_command, shell=True)
        try:
            proc.check_returncode()
        except subprocess.CalledProcessError as e:
            print(
                f"An error occurred. Container exited with the exit code {e.returncode}:"
            )
            return e.returncode
        
        if args.operation == 'start':
            if args.port != None:
                success =  wait_for_server("127.0.0.1",args.port,args.num_retry,args.timeout)
                if not success:
                    print(f"ERROR: Sever on port {args.port} does not appear to have started:")
                    print(f"ERROR: There is clearly an issue so stopping container")
                    proc = subprocess.run(f"apptainer instance stop {model_name}", shell=True)
            
    # return code is used by pytest to check code ran successfully
        return proc.returncode
    return 0

if __name__ == "__main__":
    main()