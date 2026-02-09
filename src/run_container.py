import argparse
from pathlib import Path
import subprocess, sys, yaml
from dataclasses import dataclass, field
from typing import Optional, List
from dacite import from_dict
from src.check_yaml import DuplicateKeyDetector, DuplicateKeyError
from src.check_yaml import is_valid_name
from src.check_URI import check_container_def
from src.util_functions import create_build_options
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="logs/log.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
)
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


@dataclass
class ContainerConfig:
    description: str
    image_file: str = field(default="")
    container_definition: str = field(default="")
    encryption_key: str = field(default="")
    shared_directories: List[str] = field(default_factory=list)
    dont_mount: List[str] = field(default_factory=list)
    group: str = field(default="")
    encrypted: bool = field(default=False)
    Device: str = field(default='cuda')
    build_options: dict = field(default_factory=dict)


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


def check_container_config(config_files: list):
    """
    Function to load configs from list of yaml files, check for errors
    and create dict of all container configs with names as keys.
    """

    Containers = {}
    cmd_output("Checking all config files.",log=True,sentinel=" ")
    for conf_file in config_files:
        with open(conf_file, "r") as file:
            cmd_output(f"Reading config from file: {file.name}",sentinel='-',log=True)
            all_containers = yaml.load(file, Loader=DuplicateKeyDetector)

        for key in all_containers:
            # check model name does not contain anything surprising.
            if not is_valid_name(key):
                raise ValueError(
                    f"Model name {key} in {file.name} is not valid \
                                 model names must contain only, letter number and/or underscores"
                )

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
                result.image_file = f"Images/{key}.sif"
            elif result.image_file.endswith(".sif"):
                pass
            else:
                raise ValueError(
                    f"Error in config of Model name {key} in {file.name}:\n\
                                 image file name {result.image_file} must end in .sif"
                )
            # if no definition file is given set default definition file name as "model_name.def"
            if result.container_definition == "":
                result.container_definition = f"Definitions/{key}.def"
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
    operation: str,
    model_name: str,
    Container: ContainerConfig,
    cmd_list: List[str] = ["hostname"],
):
    """
    Function to create appropriate Apptainer command based on the
    operation requested.
    """

    image = Container.image_file
    definition = Container.container_definition
    
    # set GPU flags
    # use Nvidia GPU
    if Container.Device.lower() == 'cuda':
        gpu_flag = " --nv "
    # use AMD GPU
    elif Container.Device.lower() == 'rocm':
        gpu_flag = " --rocm "        
    # use CPU
    elif Container.Device.lower() == 'cpu':
        gpu_flag = ""
    # Default to cpu and print out warning message if device is unknown
    else:
        logging.warning(f"Device {Container.Device} in config file for {model_name} not recognised.")
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
        dirs = []
        for directory in Container.shared_directories:
            logging.info(f"Granting access to {directory} within the container")
            dirs.append(directory)
        # convert list of flags into comma separated string
        flags_str = ''.join([item + ',' for item in dirs])[:-1]
        bind_opt = f" --bind {flags_str} "
    else:
        bind_opt = "" 
    # check for encryption and add appropriate flags
    if Container.encrypted:
        if Container.encryption_key != "":
            enc_flag = " --passkey "
        else:
            enc_flag = f" --pem-path {Container.encryption_key} "
    else:
        enc_flag = ""

    if operation == "run":
        cmd = " ".join(cmd_list)
        msg = "Running"
        image_exists(image)
        apptainer_command = f"apptainer exec{enc_flag}{no_mnt_flag}{bind_opt}{gpu_flag}{image} {cmd}"

    elif operation == "build" or operation == "load":
        msg = "Building"
        build_options_str = create_build_options(Container.build_options)
        apptainer_command = (
            f"apptainer build{build_options_str}{enc_flag}{gpu_flag}{image} {definition}"
        )

    elif operation == "start":
        msg = "Starting"
        image_exists(image)
        apptainer_command = f"apptainer instance start{enc_flag}{no_mnt_flag}{bind_opt}{gpu_flag}{image} {model_name}"

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
    run_parser = subparsers.add_parser("run", help="Run command(s), with the Container")

    run_parser.add_argument("model_name", type=str, help="Name of Model to use")

    run_parser.add_argument("cmd", type=str, nargs="+", help="Command(s) to run")

    # sub-parser for the build operation
    build_parser = subparsers.add_parser(
        "build", help="Build the Container, exactly equivalent to load"
    )

    build_parser.add_argument("model_name", type=str, help="Name of Model to use")

    # sub-parser for the load operation
    load_parser = subparsers.add_parser(
        "load", help="Build the Container, exactly equivalent to build"
    )

    load_parser.add_argument("model_name", type=str, help="Name of Model to use")

    # sub-parser for the list operation
    list_parser = subparsers.add_parser("list", help="List available containers")

    list_parser.add_argument(
        "--group", type=str, default="", help="optional group of containers to list"
    )

    # sub-parser for the start operation
    start_parser = subparsers.add_parser(
        "start", help="Start Container as background process"
    )

    start_parser.add_argument("model_name", type=str, help="Name of Model to use")
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

    args = parser.parse_args()

    if args.operation != "run":
        args.cmd = ""
    return args


def list_containers(Containers: dict, group: str = ""):
    '''
    Print filtered list of containers to stdout, 
    formatted for readability
    
    :params
        Containers: dictionary of available containers, keys are 
                    container names and values are the group it 
                    belongs to.
        group:      group to filter output by

    '''
    msg_length=40
    cmd_output("*",sep="",length=msg_length)
    cmd_output("Currently available containers:",length=msg_length)
    cmd_output("*",sep="",length=msg_length)
    print(f"Name:          Group:    Description:")
    cmd_output("-",sep="",sentinel='-',length=msg_length)    
    for key, value in Containers.items():
        if value.group == group or group == "":
            output = f"{key:<15}{value.group:<10}{value.description}"
            print(output)


###############################################################################
# Main program starts here
###############################################################################
def main() -> int:
    args = parse_cmd_arguments()
    if args.config_file:
        container_config = Path(args.config_file)
    else:
        container_config = Path("Container_Configs/")
    cmd_output("*",sep="")
    cmd_output("Loading Model Config Files")
    cmd_output("*",sep="")
    
    Containers = load_container_config_file(container_config)

    if args.operation.lower() == "list":
        # just list all detected containers then exit
        list_containers(Containers, args.group)
        return 0

    model_name = args.model_name

    if model_name not in Containers.keys():
        raise ValueError(
            f"no model named {model_name} was found in a config file.\n \
                            Model must be one of \n{list(Containers.keys())}"
        )

    apptainer_command = format_command(
        args.operation, model_name, Containers[model_name], args.cmd
    )
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
        return proc.returncode
    # return code is used by pytest to check code ran successfully
    return 0


# if __name__ == "__main__":
#     return_code = main()
