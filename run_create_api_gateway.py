
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
        _logger_mode = {"critical": logger.critical,
                        "debug": logger.debug,
                        "error": logger.error,
                        "info": logger.info
                        }
                        
    try:
        _logger_mode.get(mode, _logger_mode)(f"Error in {func_str} {addition_msg} {error}") if logger \
            else print(f"Error in {func_str} {addition_msg} {error}")
        if logger and set_trace: logger.exception("trace")
        return exit(99) if not ignore_flag else None
    except Exception as err:
        raise err


@click.command()
@click.option('--api_name', required=True, type=str)
@click.option('--resource_path', required=True, type=str)
@click.option('--http_method', required=True, type=str)
@click.option('--lambda_function_name', required=True, type=str)
def run_main(api_name, resource_path, http_method, lambda_function_name, logger: Log = None):
    """
    to start a sample run, you can use following command:

    python run_create_api_gateway.py  --api_name test_test_api --resource_path lambda-test-20250301 --http_method GET --lambda_function_name lambda-test-20250301
    """


    from main import main

    output = main(api_name, resource_path, http_method, lambda_function_name)
    if not output:
        error_logger(currentframe().f_code.co_name,
                     f"command line utility should return True but it doesn't",
                     logger=logger,
                     mode="error",
                     ignore_flag=False)


if __name__ == "__main__":
    run_main()
