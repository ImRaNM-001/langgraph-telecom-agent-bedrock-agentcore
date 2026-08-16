import os
import yaml
from src.logging import logger, get_root_path
from ensure import ensure_annotations
from box import ConfigBox
from pathlib import Path
from box.exceptions import BoxValueError


@ensure_annotations
def read_yml(path_to_yml: Path) -> ConfigBox:
    """reads yml file and returns

    Args:
        path_to_yml (Path): path like input

    Raises:
        ValueError: if yml file is empty
        e: empty file

    Returns:
        ConfigBox: ConfigBox type
    """
    try:
        with open(path_to_yml) as yml_file:
            content = yaml.safe_load(yml_file)

            logger.info(f'yml file: {path_to_yml} loaded successfully')
            return ConfigBox(content)

    except BoxValueError:
        raise ValueError('yml file is empty')

    except Exception as exception:
        raise exception


@ensure_annotations
def create_directories(path_to_directories: list, verbose=True):
    """create list of directories

    Args:
        path_to_directories (list): list of path of directories
        verbose (bool, optional): log each created directory. Defaults to True.
    """
    for path in path_to_directories:
        os.makedirs(path, exist_ok=True)
        if verbose:
            logger.info(f'created directory at: {path}')
