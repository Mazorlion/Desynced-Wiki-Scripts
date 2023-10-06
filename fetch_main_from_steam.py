"""Logs into steam and downloads the latest version of the Desynced main mod.

Requires a valid purchase of Desynced in your account.
If 2FA is enabled, you will be prompted to provide a code.
"""
import os
from zipfile import ZipFile

# Apply patches before importing.
import steam.monkey

steam.monkey.patch_minimal()

# pylint: disable=wrong-import-position
from steam.client import SteamClient
from steam.client.cdn import CDNClient


DESYNCED_APP_ID = 1450900


def fetch_main(output_zip_file: str, output_game_data_dir: str):
    """Does the things."""
    # Validate we won't run into any existing files.
    assert not os.path.isfile(output_zip_file), "output file already exists"
    assert not os.path.isdir(output_game_data_dir), "output dir already exists"

    # Log in to steam (will prompt on CLI).
    client = SteamClient()
    client.cli_login()
    cdn_client: CDNClient = CDNClient(client)

    # Grab the main zip.
    files = list(
        cdn_client.iter_files(DESYNCED_APP_ID, "Desynced\Content\mods\main.zip")
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
    # TODO(maz): Make this arguments.
    OUT_DIR = "fetched_game_data"
    OUT_FILE = "fetch_main.zip"
    fetch_main(OUT_FILE, OUT_DIR)
