"""Enrichissement légal via les registres officiels d'entreprises.

- `FranceRegistry` : API publique « Recherche d'entreprises » (api.gouv.fr), gratuite, sans clé.
- Autres pays : pas d'API ouverte sans clé → `LinkOnlyRegistry` fournit un lien de recherche
  pré-rempli vers le registre officiel (à consulter manuellement).
"""
from __future__ import annotations

import httpx

from prospexia.data.countries import Country

from .base import RegistryProvider
from .france import FranceRegistry
from .links import LinkOnlyRegistry


def registry_for(country: Country, client: httpx.AsyncClient) -> RegistryProvider:
    if country.code == "FR":
        return FranceRegistry(client)
    return LinkOnlyRegistry(client, country)


__all__ = ["RegistryProvider", "FranceRegistry", "LinkOnlyRegistry", "registry_for"]
