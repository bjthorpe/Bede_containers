import argparse
from pathlib import Path
import subprocess, sys, yaml
from dataclasses import dataclass
from typing import Optional
from dacite import from_dict

parser = argparse.ArgumentParser()

parser.add_argument('operation',
                    choices=['run', 'load', 'build', 'shell'],
                    help='Operation to perform')
parser.add_argument('model_name',
                    type=str,
                    help='Model name to use')
parser.add_argument('--config_file',
                    type=str,
                    default='container_config.yaml',
                    help='path to Config file')
args = parser.parse_args()

container_config=Path(args.config_file)
model_name=args.model_name
operation=''

@dataclass
class Container:
    description: str
    image_file: Optional[str]
    repo_url: Optional[str]
    shared_directories: Optional[str]

if not container_config.exists():
    raise ValueError(f"Could not find config file {container_config}")

with open(container_config, 'r') as file:
    all_containers = yaml.safe_load(file)

# create dict of all containers with names as keys
Containers = {}
for key,value in all_containers.items():
    result = from_dict(data_class=Container, data=value)
    Containers[key] = result

if model_name not in Containers.keys():
    raise ValueError(f"no model named {model_name} was found in the config file.\n Model must be one of \n{list(Containers.keys())}")

if(args.operation=='run'):
    operation='exec'
elif(args.operation=='build' or args.operation=='load'):
    print("build/load not yet implemented")
elif(args.operation=='shell'):
    print("shell not yet implemented")
else:
    # this path should not happen but just in case.
    print("How did you get here that was not a valid choice?")
    sys.exit(1)

apptainer_command = f'apptainer {operation} {Containers[model_name].repo_url} ls'
subprocess.run(apptainer_command,shell=True)


