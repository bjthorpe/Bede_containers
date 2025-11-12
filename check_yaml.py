import sys
import yaml

class DuplicateKeyError(Exception):
    """
    Custom Exception to be raised when finding duplicate keys in yaml file.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    
class DuplicateKeyDetector(yaml.SafeLoader):
    '''
    The standard python yaml loader silently overwrites keys if a duplicate value occurs.
    This is a custom YAML loader that raises an error when duplicate keys are found.
    '''
    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise DuplicateKeyError(f"Duplicate key found: '{key}' at line {key_node.start_mark.line + 1}")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping
