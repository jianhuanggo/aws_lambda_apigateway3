import os
import inspect
from inspect import currentframe
import sys
from collections import deque
from typing import List
from pathlib import Path
from typing import Callable
from logging import Logger as Log


def info_logger(message: str = "",
                func_str: str = "",
                logger: Log = None,
                addition_msg: str = ""
                ) -> None:
    """Display message in a logger if there is one otherwise stdout
    Args:
        message: display message
        func_str: calling function, so error msg can be associated correctly
        logger: Whether error msg should be persisted in a log file
        addition_msg: A set of parameters which need to be verified
    Returns:
        No return value.
    """
    try:
        if func_str:
            message = f"{func_str}: {message}"
        logger.info(f"{message} {addition_msg}") if logger else print(f"{message} {addition_msg}")

    except Exception as err:
        raise err

def write_file(filepath: str, data: any, logger: Log = None) -> None:
    try:
        with open(filepath, "w") as file:
            file.write(data)
    except Exception as err:
        error_logger(currentframe().f_code.co_name,
                             err,
                             logger=logger,
                             mode="error",
                             ignore_flag=False)

def error_logger(func_str: str,
                 error,
                 logger: Log = None,
                 addition_msg: str = "",
                 mode: str = "critical",
                 ignore_flag: bool = True,
                 set_trace: bool = False) -> None:
    """Display error message in a logger if there is one otherwise stdout
    Args:
        func_str: calling function, so error msg can be associated correctly
        error: exception captured
        logger: Whether error msg should be persisted in a log file
        addition_msg: A set of parameters which need to be verified
        mode: error mode, either critical, debug, error or info
        ignore_flag: It will return to the calling function if set to True otherwise program will terminate
        set_trace: This will log stack trace
    Returns:
        No return value.
    """
    def _not_found(*args, **kwargs):
        raise "error mode should be 'critical', 'debug', 'error' and 'info'"
    if logger:
        _log_mode = {"critical": logger.critical,
                     "debug": logger.debug,
                     "error": logger.error,
                     "info": logger.info}
    try:
        _log_mode.get(mode, _not_found)(f"Error in {func_str}! {addition_msg} {error}") if logger \
            else print(f"Error in {func_str}! {addition_msg} {error}")
        if logger and set_trace:
            logger.exception("trace")
        return exit(99) if not ignore_flag else None
    except Exception as err:
        raise err


def is_file_exist(filepath: str) -> bool:
    return Path(filepath).is_file()


def get_original_func_filepath(func):
    while hasattr(func, '__wrapped__'):
        func = func.__wrapped__
    return inspect.getfile(func)


def get_relative_path_diff(parent_path: str, child_path: str) -> str:
    return os.path.relpath(child_path, parent_path)


def get_path_component(path: str) -> List:
    result = deque()
    while True:
        path, tail = os.path.split(path)
        if tail:
            result.appendleft(tail)
        else:
            if path:
                result.appendleft(path)
            break
    return list(result)


def get_file_basename(filename: str) -> str:
    from pathlib import Path
    return Path(filename).stem


"""
    output = databricks_upload_workspace_file(profile_name, from_local_filepath, to_workspace_filepath)
"""



def convert_flag(write_flg: bool = False, output_filepath: str = "") -> Callable:
    python_root = os.environ.get('PYTHONPATH', '') or sys.prefix
    code_generation_flag = True

    if is_file_exist(output_filepath):
        error_logger(currentframe().f_code.co_name,
                              f"file {output_filepath} already exists, skip cli generation, run the function instead",
                              logger=None,
                              mode="error",
                              ignore_flag=True)

        code_generation_flag = False

    def convert(func):
        if code_generation_flag:
            func_name = func.__name__
            signature = inspect.signature(func)
            parameters = signature.parameters
            func_filepath = get_original_func_filepath(func)
            print(func_filepath)
            module_rel_path = get_relative_path_diff(parent_path=python_root, child_path=func_filepath)
            path_to_root = get_path_component(module_rel_path)
            if len(path_to_root) > 0: path_to_root[-1] = get_file_basename(path_to_root[-1])

            print(path_to_root)

        def sub_func(*args, **kwargs):
            if code_generation_flag:

                options = []
                func_parameters = []
                for parameter_name, parameter in parameters.items():
                    parameter_type = parameter.annotation if parameter.annotation is not inspect.Parameter.empty else ""
                    required = parameter.default is inspect.Parameter.empty
                    default = parameter.default if parameter.default is not inspect.Parameter.empty else None

                    # @click.option('--profile_name', required=False, type=str)
                    default_value = f", default = str" if default is None else ""
                    options.append(
                        f"@click.option('--{parameter_name}', required={required}, type={parameter_type.__name__})")
                    func_parameters.append(parameter_name)

                parameter_args = ','.join(args)
                parameter_kwargs = " ".join([f"--{key} {val}" for key, val in kwargs.items()])
                _sample_msg = f"python {output_filepath} {parameter_args} {parameter_kwargs}"

                string = f"""
import click
from datetime import datetime
from time import sleep
from logging import Logger as Log
from inspect import currentframe



def error_logger(func_str: str, error,
                 logger: Log = None,
                 addition_msg: str = "",
                 mode: str = "critical",
                 ignore_flag: bool = True,
                 set_trace: bool = False) -> None:

    def _not_found(*args, **kwargs):
        raise "error mode should be 'critical', 'debug', 'error' and 'info'"
    if logger:
        _logger_mode = {{"critical": logger.critical,
                        "debug": logger.debug,
                        "error": logger.error,
                        "info": logger.info
                        }}
                        
    try:
        _logger_mode.get(mode, _logger_mode)(f"Error in {{func_str}} {{addition_msg}} {{error}}") if logger \\
            else print(f"Error in {{func_str}} {{addition_msg}} {{error}}")
        if logger and set_trace: logger.exception("trace")
        return exit(99) if not ignore_flag else None
    except Exception as err:
        raise err


@click.command()
{chr(10).join(options)}
def run_{func_name}({", ".join(func_parameters)}, logger: Log = None):
    \"\"\"
    to start a sample run, you can use following command:

    {_sample_msg}
    \"\"\"


    from {'.'.join(path_to_root[1:])} import {func_name}

    output = {func_name}({", ".join(func_parameters)})
    if not output:
        error_logger(currentframe().f_code.co_name,
                     f"command line utility should return True but it doesn't",
                     logger=logger,
                     mode="error",
                     ignore_flag=False)


if __name__ == "__main__":
    run_{func_name}()
"""
                if write_flg:
                    write_file(output_filepath, string)
                else:
                    print(string)

                info_logger(f"cli script successfully generated at {output_filepath}")
                info_logger(f"to start a sample run, you can use following command:\n\n"
                                     f"{_sample_msg}")
            else:
                ret = func(*args, **kwargs)
                info_logger(f"return message from cli: {ret}")
                return True
        return sub_func

    return convert
