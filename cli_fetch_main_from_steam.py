"""Logs into steam and downloads the latest version of the Desynced main mod.

Requires a valid purchase of Desynced in your account.
If 2FA is enabled, you will be prompted to provide a code.
"""

from steam.client.cdn import CDNClient
from steam.client import SteamClient
import os
from zipfile import ZipFile
import argparse

# Apply patches before importing.
import steam.monkey

from util.constants import DESYNCED_APP_ID, FETCHED_GAME_DATA_DIR

steam.monkey.patch_minimal()

CONFIG_SECTION = "steam"


def fetch_main(output_zip_file: str, output_game_data_dir: str, branch: str = "public"):
    """Fetch main mod from steam server."""

    # Validate we won't run into any existing files.
    assert not os.path.isfile(output_zip_file), "output file already exists"
    assert not os.path.isdir(output_game_data_dir), "output dir already exists"

    # Log in to steam (will prompt on CLI).
    client = SteamClient()
    client.cli_login()
    cdn_client: CDNClient = CDNClient(client)

    # Grab the main zip.
    files = list(
        cdn_client.iter_files(
            DESYNCED_APP_ID, "Desynced/Content/mods/main.zip", branch=branch
        )
    )
    assert len(files) == 1, f"Found invalid number of main files {len(files)}: {files}"
    main_zip = files.pop()
    with open(output_zip_file, "wb") as zip_file:
        written_bytes = zip_file.write(main_zip.read(main_zip.size))
        assert written_bytes > 0, "No bytes written to file."

    # Extract files for analysis.
    with ZipFile(output_zip_file) as zip_file:
        zip_file.extractall(output_game_data_dir)

    # Cleanup downloaded zip.
    os.remove(output_zip_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and extract Desynced main mod from Steam",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        default=FETCHED_GAME_DATA_DIR,
        help="Directory to extract game data to",
    )
    parser.add_argument(
        "--output-zip", default="fetch_main.zip", help="Temporary zip file to download"
    )
    parser.add_argument(
        "--branch",
        default="public",
        help="Steam branch to download from (e.g., public, experimental)",
    )
    args = parser.parse_args()

    fetch_main(args.output_zip, args.output_dir, args.branch)
