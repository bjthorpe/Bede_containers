import re
from pathlib import Path
# define regex's to check 3 common types of URI used by Apptainer
LIBRARY_RE = re.compile(
    r"^library://([A-Za-z0-9_.-]*)"
    r"/*([/A-Za-z0-9_.-]*)"
    r"/*([A-Za-z0-9_.-]+)"
    r"\:([A-Za-z0-9._-]+)$"
)

DOCKER_RE = re.compile(
    r"^docker://([A-Za-z0-9_.-]*)"
    r"/*([/A-Za-z0-9_.-]*)"
    r"/*([A-Za-z0-9_.-]+)"
    r"\:([A-Za-z0-9._-]+)$"
)

ORAS_RE = re.compile(
    r"^oras://([A-Za-z0-9_.-]*)"
    r"/*([/A-Za-z0-9_.-]*)"
    r"/*([A-Za-z0-9_.-]+)$"
)

def validate_uri(v):
    """ 
    Function to check each type of Apptainer uri to see if the string is valid
    """
    # docker:// (tag required)
    if DOCKER_RE.match(v):
        return True    
    
    # library:// (tag required)
    if LIBRARY_RE.match(v):
        return True
    # oras:// (no tag required)
    if ORAS_RE.match(v):
        return True   
    # not a vaild URI
    return False


def check_container_def(definition:str)->str:
            
    # first check if string is a valid uri,
    # that is it starts with: docker://, 
    # library:// or oras:// 
    # and has a tag if needed.

    if validate_uri(definition):
        return definition
    
    # not a valid uri so check once more to see if we need to add docker://
    elif validate_uri(f"docker://{definition}"):
        return f"docker://{definition}"
    
    else:
        # still not a uri so check if its a valid path to a file
        p = Path(definition)
        if p.exists() and p.is_file() and definition.endswith(".def"):
            return definition
        # no idea what this is so raise error
        msg = f" Container definition: {definition} is not valid. \n \
            This must be a path to an existing file, or an Apptainer URI \n \
                (with tag if required)"
        
        raise ValueError(msg)


