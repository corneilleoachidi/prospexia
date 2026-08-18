from __future__ import annotations

import abc
import re
import unicodedata
from difflib import SequenceMatcher

import httpx

from prospexia.core.models import Company, LegalInfo


def normalize_name(name: str) -> str:
    """Minuscule, sans accents, sans forme juridique ni ponctuation — pour comparer des raisons sociales."""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    n = re.sub(r"\b(sarl|sas|sasu|eurl|sa|snc|sci|selarl|scp|ei|eirl|ltd|gmbh|bv|srl|sprl|ag|llc|inc)\b", " ", n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def name_similarity(a: str, b: str) -> float:
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    ratio = SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    overlap = len(ta & tb) / max(1, min(len(ta), len(tb)))
    return max(ratio, overlap * 0.95 if len(ta & tb) >= 1 else 0.0)


class RegistryProvider(abc.ABC):
    name: str = "registry"

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @abc.abstractmethod
    async def lookup(self, company: Company) -> LegalInfo | None:
        """Retourne les informations légales appariées, ou un lien de recherche, ou None."""
