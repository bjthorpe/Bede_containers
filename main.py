import argparse
from pathlib import Path
import subprocess, sys, yaml
from dataclasses import dataclass, field
from typing import Optional, List
from dacite import from_dict
from check_yaml import DuplicateKeyDetector, DuplicateKeyError, is_valid_name


@dataclass
class ContainerConfig:
    description: str
    image_file: Optional[str]
    container_definition: Optional[str]


@dataclass
class UserConfig:
    shared_directories: Optional[str]
    use_GPU: Optional[bool] = field(default=True)


def check_container_config(config_files: list):
    """
    Function to load configs from list of yaml files, check for errors
    and create dict of all container configs with names as keys.
    """

    Containers = {}
    for conf_file in config_files:
        with open(conf_file, "r") as file:
            print(f"Reading config from file: {file.name}")
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
            if result.image_file == None:
                result.image_file = f"Images/{key}.sif"
            elif result.image_file.endswith(".sif"):
                pass
            else:
                raise ValueError(
                    f"Error in config of Model name {key} in {file.name}:\n\
                                 image file name {result.image_file} must end in .sif"
                )
            # if no definition file is given set default definition file name as "model_name.def"
            if result.container_definition == None:
                result.container_definition = f"Definitions/{key}.def"
            elif result.container_definition.endswith(".def"):
                pass
            elif result.container_definition.startswith("docker://"):
                pass
            else:
                raise ValueError(
                    f"Error in config of Model name {key} in {file.name}:\n\
                                 container_definition {result.container_definition} must end in .def"
                )
        print(f"{file.name} OK")
    return Containers


def check_user_config_file(config_file: Path):
    """
    Function to load user config from yaml file and check for errors.
    """

    with open(config_file, "r") as file:
        print(f"Reading user config from file: {file.name}")
        tmp_dict = yaml.load(file, Loader=DuplicateKeyDetector)

    User_config = from_dict(data_class=UserConfig, data=tmp_dict)
    # check if shared dir is required and is so does it exist
    if User_config.shared_directories != None:
        shared_dir = Path(User_config.shared_directories)

        if not shared_dir.exists():
            raise ValueError(
                f"Error in user config file {file.name}: shared directory has \
                            been specified but does not appear to exist"
            )
        if not shared_dir.is_dir():
            raise ValueError(
                f"Error in user Config file {file.name}: shared directory \
                        must be a directory."
            )
    return User_config


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


def load_user_config_file(user_config_file):
    """
    Load the user config file, do some basic sanity checks.
    """
    user_config_file = Path(user_config_file)

    # we want a single named config file
    if not user_config_file.exists():
        raise FileNotFoundError(
            f"Could not find user \
                                config file {user_config_file}"
        )

    if user_config_file.suffix not in [".yml", ".yaml"]:
        raise ValueError(
            f"config file {user_config_file} is not a \
            yaml file, \n the filename must end in .yml \
            or .yaml"
        )

    User_config = check_user_config_file(user_config_file)

    return User_config

def image_exists(image_file:str):
    if not Path(image_file).exists():
        print(
            f"A container with the name {image_file} \
            \n could not be found please run build first."
        )
        sys.exit(1)
    return

def format_command(
    operation: str, model_name:str, image: str, definition: str, cmd_list: List[str] = ["hostname"]
):
    """
    Function to create appropriate apptainer command based on the
    operation requested.
    """

    if operation == "run":
        cmd = " ".join(cmd_list)
        msg = "Running"
        image_exists(image)
        apptainer_command = f"apptainer exec {image} {cmd}"

    elif operation == "build" or operation == "load":
        msg = "Building"
        apptainer_command = f"apptainer build {image} {definition}"

    elif operation == "start":
        msg = "Starting"
        image_exists(image)
        print("")
        apptainer_command = f"apptainer instance start {image} {model_name}"

    elif operation == "stop":
        msg = "Stopping"
        image_exists(image)
        apptainer_command = f"apptainer instance stop {model_name}"

    elif operation == "shell":
        apptainer_command = ""
        print("shell not yet implemented")
        sys.exit(1)
    else:
        # this path should not happen but just in case.
        apptainer_command = ""
        print("How did you get here that was not a valid choice?")
        sys.exit(1)

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
        nargs='*',
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

    parser.add_argument(
        "--config_file", 
        type=str, 
        default=None, 
        help="path to Config file for Models"
    )
    parser.add_argument(
        "--user_config_file",
        type=str,
        default="UserConfig.yaml",
        help="path to Config file for user options",
    )

    # separate out known args and pass the rest for the underlying container to deal with
    args =parser.parse_args()

    if args.operation != "run":
        args.cmd=""
    return args
###############################################################################
# Main program starts here
###############################################################################
if __name__ == "__main__":
    args = parse_cmd_arguments()
    if args.config_file:
        container_config = Path(args.config_file)
    else:
        container_config = Path("Container_Configs/")
    # if args.operation!='run' and container_cmds not None:

    model_name = args.model_name
    operation = ""
    print("*********************************************************************")
    print(f"***************** Loading Model Config Files ************************")
    print("*********************************************************************")
    Containers = load_container_config_file(container_config)

    if model_name not in Containers.keys():
        raise ValueError(
            f"no model named {model_name} was found in a config file.\n \
                            Model must be one of \n{list(Containers.keys())}"
        )

    apptainer_command = format_command(
        args.operation,
        model_name,
        Containers[model_name].image_file,
        Containers[model_name].container_definition,
        args.cmd,
    )

    proc = subprocess.run(apptainer_command, shell=True)
    try:
        proc.check_returncode()
    except subprocess.CalledProcessError as e:
        print(f"An error occurred. Container exited with the exit code {e.returncode}:")
