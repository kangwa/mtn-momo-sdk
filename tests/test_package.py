from momo_sdk import hello


def test_hello() -> None:
    assert hello() == "Hello from momo-sdk!"
