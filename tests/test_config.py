from typing import Any

import pytest

from mtn_momo.config import ProductConfig
from mtn_momo.exceptions import MomoConfigError

VALID_KWARGS: dict[str, Any] = {
    "base_url": "https://sandbox.momodeveloper.mtn.com",
    "subscription_key": "key",
    "api_user": "user",
    "api_key": "secret",
}


class TestProductConfig:
    def test_defaults(self) -> None:
        config = ProductConfig(**VALID_KWARGS)
        assert config.target_environment == "sandbox"
        assert config.timeout == 10.0

    @pytest.mark.parametrize(
        "missing_field", ["base_url", "subscription_key", "api_user", "api_key"]
    )
    def test_rejects_missing_required_field(self, missing_field: str) -> None:
        kwargs = {**VALID_KWARGS, missing_field: ""}
        with pytest.raises(MomoConfigError):
            ProductConfig(**kwargs)


class TestProductConfigFromEnv:
    def test_reads_prefixed_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MOMO_COLLECTIONS_SUBSCRIPTION_KEY", "key")
        monkeypatch.setenv("MOMO_COLLECTIONS_API_USER", "user")
        monkeypatch.setenv("MOMO_COLLECTIONS_API_KEY", "secret")

        config = ProductConfig.from_env("MOMO_COLLECTIONS_")

        assert config.subscription_key == "key"
        assert config.api_user == "user"
        assert config.api_key == "secret"
        assert config.target_environment == "sandbox"

    def test_missing_env_var_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MOMO_COLLECTIONS_SUBSCRIPTION_KEY", raising=False)
        with pytest.raises(MomoConfigError):
            ProductConfig.from_env("MOMO_COLLECTIONS_")
