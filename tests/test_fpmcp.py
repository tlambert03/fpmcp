import fpmcp


def test_imports_with_version():
    assert isinstance(fpmcp.__version__, str)
