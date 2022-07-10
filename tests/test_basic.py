from pypi_user_agent import user_agent


def test_user_basic_string() -> None:
    ua = user_agent("myinstaller", "1.0")

    assert ua.startswith("myinstaller/1.0 ")
