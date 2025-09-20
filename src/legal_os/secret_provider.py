from __future__ import annotations

from typing import Optional, Protocol


class SecretProvider(Protocol):
    def get(self, name: str) -> Optional[str]:
        ...


class EnvSecretProvider:
    def get(self, name: str) -> Optional[str]:  # pragma: no cover - trivial
        import os

        return os.getenv(name)


class KeyVaultSecretProvider:
    """Placeholder Key Vault provider.

    In production, use azure-identity and azure-keyvault-secrets to fetch secrets.
    This stub preserves the interface and allows easy swap-in later.
    """

    def __init__(self, vault_uri: str):
        self.vault_uri = vault_uri

    def get(self, name: str) -> Optional[str]:
        # TODO: integrate with Azure SDKs; for now, return None to fallback to env
        return None
