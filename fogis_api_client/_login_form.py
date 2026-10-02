"""Find the login form on auth.fogis.se/Account/LogIn (FOGIS_API.md §1)."""

from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass
class LoginForm:
    action: str
    fields: dict[str, str] = field(default_factory=dict)


class _FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[LoginForm] = []
        self._current: LoginForm | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): v or "" for k, v in attrs}
        if tag == "form":
            self._current = LoginForm(action=a.get("action", ""))
            self.forms.append(self._current)
        elif tag == "input" and self._current is not None and a.get("name"):
            if a.get("type", "text").lower() in ("checkbox", "radio") and "checked" not in a:
                return
            self._current.fields.setdefault(a["name"], a.get("value", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self._current = None


def find_login_form(html: str) -> LoginForm | None:
    """Return the form that has a Password field, with all its current input values."""
    parser = _FormParser()
    parser.feed(html)
    return next((f for f in parser.forms if "Password" in f.fields), None)
