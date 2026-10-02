from fogis_api_client._login_form import find_login_form


def test_picks_the_password_form_and_its_hidden_fields() -> None:
    html = """
    <form action="/search"><input name="q"></form>
    <form method="post" action="/Account/Login?returnurl=x">
      <input name="Username"><input name="Password" type="password">
      <input name="RememberMe" type="checkbox" value="true">
      <input type="hidden" name="__RequestVerificationToken" value="t&amp;1">
    </form>"""
    form = find_login_form(html)
    assert form is not None
    assert form.action == "/Account/Login?returnurl=x"
    assert form.fields["__RequestVerificationToken"] == "t&1"
    assert "RememberMe" not in form.fields  # unchecked checkbox is not submitted


def test_no_login_form() -> None:
    assert find_login_form("<html><body>Start</body></html>") is None
