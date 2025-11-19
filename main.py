import argparse
from pathlib import Path
import subprocess, sys, yaml
from dataclasses import dataclass
from typing import Optional
from dacite import from_dict
from check_yaml import DuplicateKeyDetector, DuplicateKeyError


@dataclass
class Container:
    description: str
    image_file: Optional[str]
    repo_url: Optional[str]
    shared_directories: Optional[str]


def check_config(config_files: list):
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
            result = from_dict(data_class=Container, data=all_containers[key])
            # check for duplicate model names
            if key not in Containers:
                Containers[key] = result
            else:
                raise DuplicateKeyError(
                    f"Error in config of model {key} in {conf_file} this appears to have the same \n \
                                name as another model. Two models must not share the same name."
                )
            # Handles special case where at least one of these options is required
            if result.image_file == None and result.repo_url == None:
                raise ValueError(
                    f"Error in config of model {key} you must \
                                specify one of either image_file or repo_url in the config file."
                )
            # check if shared dir is required and is so does it exist
            if result.shared_directories != None:
                shared_dir = Path(result.shared_directories)
                if not shared_dir.exists():
                    raise ValueError(
                        f"Error in config of model {key}: shared directory has \
                                    been specified but does not appear to exist"
                    )
                if not shared_dir.is_dir():
                    raise ValueError(
                        f"Error in config of model {key}: shared directory \
                                must be a directory."
                    )
        print(f"{file.name} OK")
    return Containers


def load_config_file(container_config):
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
                f"config file {container_config} is not a yaml file, \n it must end in .yml or .yaml"
            )
        # create list with single container config file in it
        config_files = [container_config]

    Containers = check_config(config_files)

    return Containers


###############################################################################
# Main program starts here
###############################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "operation",
        choices=["run", "load", "build", "shell"],
        help="Operation to perform",
    )
    parser.add_argument("model_name", type=str, help="Model name to use")
    parser.add_argument(
        "--config_file", type=str, default=None, help="path to Config file"
    )
    args = parser.parse_args()

    if args.config_file:
        container_config = Path(args.config_file)
    else:
        container_config = Path("Configs/")

    model_name = args.model_name
    operation = ""
    print("*********************************************************************")
    print(f"***************** Loading Model Config Files ************************")
    print("*********************************************************************")
    Containers = load_config_file(container_config)

    if model_name not in Containers.keys():
        raise ValueError(
            f"no model named {model_name} was found in a config file.\n \
                            Model must be one of \n{list(Containers.keys())}"
        )

    if args.operation == "run":
        operation = "exec"
    elif args.operation == "build" or args.operation == "load":
        print("build/load not yet implemented")
    elif args.operation == "shell":
        print("shell not yet implemented")
    else:
        # this path should not happen but just in case.
        print("How did you get here that was not a valid choice?")
        sys.exit(1)
    print("*********************************************************************")
    print(f"***************** Running Model: {model_name} *********************")
    print("*********************************************************************")

    apptainer_command = (
        f"apptainer {operation} {Containers[model_name].repo_url} hostname1"
    )
    proc = subprocess.run(apptainer_command, shell=True)
    try:
        proc.check_returncode()
    except subprocess.CalledProcessError as e:
        print(f"An error occurred. Container exited with the exit code {e.returncode}:")
