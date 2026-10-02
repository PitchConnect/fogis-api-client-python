"""Exceptions raised by the client. All inherit from FogisError."""


class FogisError(Exception):
    """Base class for every error raised by this package."""

    @property
    def message(self) -> str:
        """The error text (0.x exceptions had this attribute)."""
        return str(self.args[0]) if self.args else ""


class FogisLoginError(FogisError):
    """Could not get an authenticated session."""


class FogisInvalidCredentialsError(FogisLoginError):
    """FOGIS rejected the username or password."""


class FogisAuthServiceUnavailableError(FogisLoginError):
    """auth.fogis.se could not be reached or answered with a server error."""


class FogisSessionExpiredError(FogisLoginError):
    """The session expired and could not be renewed (no password to fall back on, or renewal failed)."""


class FogisAPIRequestError(FogisError):
    """A call to MatchWebMetoder failed at the HTTP level (network error or non-2xx status)."""

    def __init__(
        self, message: str, status_code: int | None = None, server_message: str | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.server_message = server_message  # FOGIS's own text, when it sent one


class FogisRejectedError(FogisAPIRequestError):
    """FOGIS refused the call on a rule of its own (an ApplicationException), e.g. submitting a report whose
    squad has no captain: server_message is then "Bortalagets matchtrupp saknar lagkapten."."""


class FogisDataError(FogisError):
    """FOGIS answered, but not with the JSON shape expected."""
