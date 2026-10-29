"""Where the CLI gets FOGIS credentials: environment variables, else the macOS Keychain.

One Keychain item (service "fogis") holds both: the username as its account, the password as its secret.
The password is read only when FOGIS needs a password login, and is never printed or written anywhere.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass

DEFAULT_SERVICE = "fogis"
ITEM_NOT_FOUND = 44  # exit status of `security find-generic-password` when nothing matches
KEYCHAIN_TIMEOUT = 120.0  # seconds; long enough to answer macOS's "allow access" dialog

Runner = Callable[[list[str]], "subprocess.CompletedProcess[bytes]"]


class CredentialsError(Exception):
    """No usable credentials were found, or the Keychain could not be read."""


@dataclass(frozen=True)
class Credentials:
    username: str
    password: Callable[[], str]  # called only when a login needs it
    source: str  # "environment" or "keychain (<service>)"


def find_credentials(env: Mapping[str, str] | None = None, run: Runner | None = None) -> Credentials:
    """FOGIS_USERNAME + FOGIS_PASSWORD if FOGIS_PASSWORD is set, else the Keychain item of service
    FOGIS_KEYCHAIN_SERVICE (default "fogis"; FOGIS_USERNAME then picks the account if there are several)."""
    env = os.environ if env is None else env
    username = env.get("FOGIS_USERNAME") or None
    if env.get("FOGIS_PASSWORD"):
        if username is None:
            raise CredentialsError("FOGIS_PASSWORD is set but FOGIS_USERNAME is not")
        password = env["FOGIS_PASSWORD"]
        return Credentials(username, lambda: password, "environment")

    service = env.get("FOGIS_KEYCHAIN_SERVICE") or DEFAULT_SERVICE
    if run is None:
        if shutil.which("security") is None:
            raise CredentialsError(
                "No FOGIS credentials: set FOGIS_USERNAME and FOGIS_PASSWORD (no macOS Keychain here)"
            )
        run = _run_security
    keychain = Keychain(service, run)
    account = keychain.account(username)
    if account is None:
        raise CredentialsError(
            f'No FOGIS credentials: no Keychain item for service "{service}". Add one with\n'
            f'  security add-generic-password -s {service} -a "YOUR FOGIS USERNAME" -w\n'
            "(it asks for the password), or set FOGIS_USERNAME and FOGIS_PASSWORD."
        )
    return Credentials(account, lambda: keychain.password(account), f"keychain ({service})")


class Keychain:
    """Generic-password items of one service, read with macOS's `security` tool."""

    def __init__(self, service: str, run: Runner) -> None:
        self.service = service
        self._run = run

    def account(self, username: str | None = None) -> str | None:
        """The item's account (the FOGIS username); None if there is no item. Never reads the secret."""
        args = ["find-generic-password", "-s", self.service]
        if username is not None:
            args += ["-a", username]
        out = self._find(args)
        if out is None:
            return None
        for line in out.stdout.decode("utf-8", "replace").splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key == '"acct"<blob>':
                return _value(value)
        raise CredentialsError(f'Keychain item "{self.service}" has no account (the FOGIS username)')

    def password(self, account: str) -> str:
        # -g, not -w: -w prints a password with non-ASCII characters as bare hex, indistinguishable from a
        # password that looks like hex. -g marks hex with 0x (on stderr).
        out = self._find(["find-generic-password", "-s", self.service, "-a", account, "-g"])
        if out is None:
            raise CredentialsError(f'Keychain item "{self.service}" for {account} disappeared')
        for line in out.stderr.decode("utf-8", "replace").splitlines():
            if line.startswith("password:"):
                return _value(line.removeprefix("password:"))
        raise CredentialsError(f'Keychain item "{self.service}" has no password')

    def _find(self, args: list[str]) -> subprocess.CompletedProcess[bytes] | None:
        out = self._run(args)
        if out.returncode == ITEM_NOT_FOUND:
            return None
        if out.returncode != 0:
            message = out.stderr.decode("utf-8", "replace").strip()
            raise CredentialsError(f"Could not read the Keychain: {message or f'exit {out.returncode}'}")
        return out


def _value(text: str) -> str:
    """A value as `security` prints it: "plain" for printable ASCII, else 0x<hex> "<escaped>" (UTF-8)."""
    text = text.strip()
    if text.startswith("0x"):
        return bytes.fromhex(text[2:].split()[0]).decode("utf-8")
    if len(text) >= 2 and text[0] == text[-1] == '"':
        return text[1:-1]  # `security` hex-encodes anything it would have to escape
    if text in ("", "<NULL>"):
        return ""
    raise CredentialsError("Unexpected Keychain output format")  # never echo it: it may be the password


def _run_security(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(["security", *args], capture_output=True, timeout=KEYCHAIN_TIMEOUT, check=False)
    except subprocess.TimeoutExpired as e:
        raise CredentialsError("Timed out waiting for the Keychain (was an access dialog left open?)") from e
