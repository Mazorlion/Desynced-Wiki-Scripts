import configparser
from pathlib import Path

CONFIG_FILE = "config.ini"


def ParseConfigSection(section: str) -> configparser.SectionProxy:
    """Parses a section from the config file."""

    config = configparser.ConfigParser()

    if not Path(CONFIG_FILE).exists():
        raise FileNotFoundError(
            f"Config file {CONFIG_FILE} does not exist. Please create it from the {CONFIG_FILE}.example"
        )

    config.read(CONFIG_FILE)

    if section not in config:
        raise KeyError(f"Section [{section}] not found in {CONFIG_FILE}")

    return config[section]


def GetCredentials(section: str) -> tuple[str, str]:
    """Reads wiki credentials from config."""

    parsedSection = ParseConfigSection(section)

    userkey = "username"
    passkey = "password"

    missing = [field for field in [userkey, passkey] if field not in parsedSection]
    if missing:
        raise RuntimeError(f"Missing fields in [{section}]: {', '.join(missing)}")

    username = parsedSection[userkey]
    password = parsedSection[passkey]

    return username, password
