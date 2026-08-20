import mtn_momo


class TestPublicAPI:
    def test_all_exports_are_importable(self) -> None:
        for name in mtn_momo.__all__:
            assert hasattr(mtn_momo, name), f"{name} listed in __all__ but not importable"
