import argparse
from pathlib import Path
import subprocess, sys, yaml
from dataclasses import dataclass, field
from typing import Optional, List
from dacite import from_dict
from check_yaml import DuplicateKeyDetector, DuplicateKeyError 
from check_yaml import is_valid_name
from check_URI import check_container_def
import logging

logging.basicConfig(level=logging.INFO,filename='logs/log.log',filemode='w',
                format="%(asctime)s - %(levelname)s - %(message)s")
@dataclass
class ContainerConfig:
    description: str
    image_file: str = field(default="")
    container_definition: str = field(default="")
    encryption_key: str = field(default="")
    shared_directories: str = field(default="")
    group: str = field(default="None")
    encrypted: bool= field(default=False)
    registry: str = field(default="docker")
    read_only: bool = field(default=False)
    use_GPU: bool = field(default=True)
    sandbox: bool = field(default=False)
    
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
    for conf_file in config_files:
        with open(conf_file, "r") as file:
            logging.info(f"Reading config from file: {file.name}")
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
                result.container_definition = check_container_def(result.container_definition)

            # do some checks for shared directory if defined
            if result.shared_directories != "":
                P = Path(result.shared_directories)
                if not P.exists():
                    err_msg = f"The shared directory {result.shared_directories} \n \
                        defined in {file.name} does not exist. "
                    raise FileNotFoundError(err_msg)
                if P.is_file():
                    err_msg = f"The shared directory {result.shared_directories} \n \
                    defined in {file.name} should be directory not a file."
                    raise FileNotFoundError(err_msg)
        logging.info(f"{file.name} OK")      
    print(f"All config files look OK")
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

def image_exists(image_file:str):
    if not Path(image_file).exists():
        msg = f"A container with the name {image_file} \
            \n could not be found please run build first."
        raise FileNotFoundError(msg)
    return

def format_command(
    operation: str,
    model_name:str, 
    Container:ContainerConfig, 
    cmd_list: List[str] = ["hostname"]
):
    """
    Function to create appropriate Apptainer command based on the
    operation requested.
    """

    image = Container.image_file
    definition = Container.container_definition
    # check for encryption and add appropriate flags
    if Container.encrypted:
        if Container.encryption_key != "":
            enc_flag = ' --passkey '
        else:
            enc_flag = f' --pem-path {Container.encryption_key} '
    else:
        enc_flag = ''

    if operation == "run":
        cmd = " ".join(cmd_list)
        msg = "Running"
        image_exists(image)
        apptainer_command = f"apptainer exec {enc_flag}{image} {cmd}"

    elif operation == "build" or operation == "load":
        msg = "Building"
        apptainer_command = f"apptainer build {enc_flag}{image} {definition}"

    elif operation == "start":
        msg = "Starting"
        image_exists(image)
        apptainer_command = f"apptainer instance start {enc_flag}{image} {model_name}"

    elif operation == "stop":
        msg = "Stopping"
        image_exists(image)
        apptainer_command = f"apptainer instance stop {model_name}"

    else:
        # this path should not happen but just in case.
        apptainer_command = ""
        raise CMD_FormatError(f"{operation} is Not a valid operation," + \
                               "This should not happen. Did you add an option" + \
                               "and forget to update format_command?")

    print("*********************************************************************")
    print(f"***************** {msg}: {model_name} *********************")
    print("*********************************************************************")
    return apptainer_command

def parse_cmd_arguments():
    """ 
    Function to handle parsing of command line arguments
    """

    parser = argparse.ArgumentParser(
        description="A CLI tool for easily running AI/ML containers on Bede.")
        
    # Subparser to create subcommands for each operation (run, build, load ect.)
    subparsers = parser.add_subparsers(
        dest="operation",
        required=True,
        help="Operation to perform."
    )
    # sub-parser for the run operation
    run_parser = subparsers.add_parser(
        "run", 
        help="Run command(s), with the Container")

    run_parser.add_argument(
        "model_name",
        type=str, 
        help="Name of Model to use")
    
    run_parser.add_argument(
        'cmd',
        type=str,
        nargs='+',
        help="Command(s) to run")
    
    # sub-parser for the build operation
    build_parser = subparsers.add_parser(
        "build", 
        help="Build the Container, exactly equivalent to load")

    build_parser.add_argument(
        "model_name",
        type=str, 
        help="Name of Model to use")
     
    # sub-parser for the load operation
    load_parser = subparsers.add_parser(
        "load",
        help="Build the Container, exactly equivalent to build")

    load_parser.add_argument(
        "model_name",
        type=str, 
        help="Name of Model to use")    
    
    # sub-parser for the list operation
    list_parser = subparsers.add_parser(
        "list",
        help="List available containers")

    list_parser.add_argument(
        "--group",
        type=str,
        default='', 
        help="optional group of containers to list")
    
# sub-parser for the start operation
    start_parser = subparsers.add_parser(
        "start", 
        help="Start Container as background process")

    start_parser.add_argument(
        "model_name",
        type=str, 
        help="Name of Model to use")
# sub-parser for the stop operation
    stop_parser = subparsers.add_parser(
        "stop", 
        help="Stop container that is running in the background")

    stop_parser.add_argument(
        "model_name",
        type=str, 
        help="Name of Model to use")
    
# other arguments for main parser
    parser.add_argument(
        "--config_file", 
        type=str, 
        default=None, 
        help="path to Config file for Models"
    )
    parser.add_argument(
        "--debug",
        action='store_true',
        help="Print generated Apptainer command instead of running container, useful for sanity checking",
    )

    args =parser.parse_args()

    if args.operation != "run":
        args.cmd=""
    return args

def list_containers(Containers:dict,group:str=''):
    print("*******************************")
    print("Currently available containers:")
    print("*******************************")
    print(f"Name:   Group:  Description:")
    print("-----------------------------")  
    for key, value in Containers.items():
        if value.group == group or group=='':
            output = f"{key}    {value.group}   {value.description}"
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
    print("*********************************************************************")
    print(f"***************** Loading Model Config Files ************************")
    print("*********************************************************************")
    Containers = load_container_config_file(container_config)

    if args.operation.lower() == 'list':
        # just list all detected containers then exit
        list_containers(Containers, args.group)
        return

    model_name = args.model_name

    if model_name not in Containers.keys():
        raise ValueError(
            f"no model named {model_name} was found in a config file.\n \
                            Model must be one of \n{list(Containers.keys())}"
        )

    apptainer_command = format_command(
        args.operation,
        model_name,
        Containers[model_name],
        args.cmd
    )
    if args.debug:
        print("Debug enabled")
        print("current config will run the following command:")
        print(apptainer_command)
    else:
        proc = subprocess.run(apptainer_command, shell=True)
        try:
            proc.check_returncode()
        except subprocess.CalledProcessError as e:
            print(f"An error occurred. Container exited with the exit code {e.returncode}:")

    #return code is used by pytest to check code ran successfully
    return 0

if __name__ == "__main__":
    return_code = main()