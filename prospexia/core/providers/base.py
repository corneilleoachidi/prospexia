from __future__ import annotations

import abc

import httpx

from prospexia.core.models import Company
from prospexia.data.countries import Country


class ProviderError(RuntimeError):
    """Erreur bloquante côté fournisseur (clé invalide, quota…)."""


class CompanyProvider(abc.ABC):
    name: str = "base"

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @abc.abstractmethod
    async def search(self, term: str, country: Country, city: str | None, limit: int) -> list[Company]:
        """Recherche des entreprises pour `term` (déjà traduit) dans le pays/ville donné."""
