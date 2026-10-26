import argparse
import os
from typing import Optional, Type

from clay.core import BlockWrapper
from clay.runners.runner import JobRunner


def _parse_input_args() -> argparse.Namespace:
    """Parse --input and --input-uri CLI flags if present.
    """
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--input", dest="input_json", default=None, help="JSON input array")
    parser.add_argument("--input-uri", dest="input_uri", default=None, help="URI to input JSON (e.g. s3://...)")
    args, _ = parser.parse_known_args()
    return args


def Run(block: Type[BlockWrapper], name: str, cfg_path: str,
        input_json: Optional[str] = None, input_uri: Optional[str] = None) -> None:
    """The general method to execute a block. In most cases, users and programs alike
    should be using this method to run the block. The function looks at a bunch of internal
    environment variables and infers which runner *or execution mode* to use.
    This ensures that the execution mode of the block is abstracted away from the user.

    Args:
        block (Type[BlockWrapper]):
            The user defined block that subclasses `BlockWrapper`.
        name (str):
            Name of the block to be run. This is used as an identifier in the in-built logger.
        cfg_path (str): Path to the configuration that is meant to be used.
        input_json (Optional[str]):
            JSON input array string. Overridden by either CLI flag, and takes precedence
            over the env vars.
        input_uri (Optional[str]):
            URI to input JSON (e.g. s3://...). Overridden by either CLI flag, and takes
            precedence over the env vars.

    Resolution order, first one set wins:
        `--input-uri` → `--input` → `input_uri` → `input_json` → `INPUT_JSON_URI`
        → `INPUT_JSON` → `[{}]`. Passing either CLI flag discards both function
        arguments, so a CLI flag can never be outranked by a programmatic one.

    Raises:
        FileNotFoundError:
            Raised when `cfg_path` does not exist.
        ValueError:
            Raised when the runner requires a set of command line arguments but no arguments
            were provided.
    """
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(cfg_path)

    cli_args = _parse_input_args()
    if cli_args.input_json is not None or cli_args.input_uri is not None:
        input_json, input_uri = cli_args.input_json, cli_args.input_uri

    runner = JobRunner(
        block_name=name,
        block_class=block,
        block_args={"config": cfg_path},
        cfg_path=cfg_path,
        input_json=input_json,
        input_uri=input_uri,
    )
    return runner.start()

