import re
from pathlib import Path
# define regex's to check all 5 types of URI used by Apptainer
LIBRARY_RE = re.compile(
    r"^library://"
    r"(?P<user>[a-z0-9][a-z0-9_.-]*)/"
    r"(?P<collection>[a-z0-9][a-z0-9_.-]*)/"
    r"(?P<container>[a-z0-9][a-z0-9_.-]*)"
    r"\:(?P<tag>[A-Za-z0-9._-]+)$"
)

DOCKER_RE = re.compile(
    r"^docker://"
    r"([a-zA-Z0-9.-]+(?:\:[0-9]+)?/)*"
    r"[a-z0-9._-]+"
    r"\:(?P<tag>[A-Za-z0-9._-]+)$"
)

ORAS_RE = re.compile(
    r"^oras://"
    r"(?P<registry>[a-zA-Z0-9.-]+(?:\:[0-9]+)?)"
    r"/(?P<repo>[a-z0-9._/-]+)"
    r"\:(?P<tag>[A-Za-z0-9._-]+)$"      
)

SHUB_RE = re.compile(
    r"^shub://[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$"
)

HTTP_RE = re.compile(r"^https?://.+$")


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

    # oras:// (tag required)
    if ORAS_RE.match(v):
        return True

    # shub:// (no tags)
    if SHUB_RE.match(v):
        return True

    # https:// (no tags)
    if HTTP_RE.match(v):
        return True
    
    # not a vaild URI
    return False


def check_container_def(definition:str)->str:
            
    # first check if string is a valid uri,
    # that is it starts with: docker://, shub://, 
    # http(s)://, library:// or oras:// 
    # and has a tag if needed.

    if validate_uri(definition):
        return definition
    
    # not a valid uri so check once more to see if we need to add docker://
    elif validate_uri(f"docker://{definition}"):
        return f"docker://{definition}"
    
    # still not a uri so check if its a valid path to a file
    p = Path(definition)
    if p.is_absolute() or "/" in definition or definition.endswith(".def"):
        return definition
    # no idea what this is so raise error
    msg = f" Container definition: {definition} is not valid. \n \
          This must be a path to a file, or an Apptainer URI \n \
            (with tag if required)"
    
    raise ValueError(msg)


