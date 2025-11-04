import subprocess, sys, yaml
from dataclasses import dataclass
from typing import Optional
from dacite import from_dict

command = sys.argv[1:]
container_config="container_config.yaml"

@dataclass
class Container:
    name: str
    description: str
    image_file: Optional[str]
    repo_url: Optional[str]
    shared_directories: Optional[str]


with open(container_config, 'r') as file:
    all_containers = yaml.safe_load(file)

# create dict of all containers with names as keys
Containers = {}
for key,value in all_containers.items():
    result = from_dict(data_class=Container, data=value)
    Containers[result.name] = result


subprocess.run(f"apptainer exec docker://alpine {" ".join(command)}",shell=True)


