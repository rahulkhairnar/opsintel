import os
from pathlib import Path

import pyexasol
from dotenv import load_dotenv

load_dotenv()

EXASOL_HOST = os.getenv("EXASOL_HOST", "127.0.0.1")
EXASOL_PORT = os.getenv("EXASOL_PORT", "8563")
EXASOL_USER = os.getenv("EXASOL_USER", "sys")

PASSWORD_FILE = (
    Path.home()
    / ".exasol-starter-kit"
    / "credentials"
    / "nano_sys_password"
)

EXASOL_FINGERPRINT = (
    "8C447BE51AC8275D2093968B333D932355444F7B7DA2668D3087EEF6924BB9A0"
)


def get_connection():
    """Create a TLS-encrypted, fingerprint-verified Exasol connection."""

    password = os.getenv("EXASOL_PASSWORD")

    if not password:
        if not PASSWORD_FILE.exists():
            raise RuntimeError(
                "EXASOL_PASSWORD is not set and the Exasol credential file "
                "was not found."
            )

        password = PASSWORD_FILE.read_text().strip()

    dsn = f"{EXASOL_HOST}/{EXASOL_FINGERPRINT}:{EXASOL_PORT}"

    return pyexasol.connect(
        dsn=dsn,
        user=EXASOL_USER,
        password=password,
        encryption=True,
    )


def test_connection():
    """Verify Exasol connectivity."""

    connection = get_connection()

    try:
        return connection.execute("SELECT 1").fetchall()
    finally:
        connection.close()
