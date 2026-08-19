# Prospexia

Application de bureau (Python / PySide6) pour **prospecter des entreprises ayant besoin d'un site web
ou d'une expertise SEO** : elle trouve des sociétés dans un pays et des secteurs donnés, analyse leur
présence en ligne (site web absent, obsolète ou hors service, réseaux sociaux, visibilité sur les
moteurs) et classe les prospects par priorité.

## Fonctionnalités

- Choix du **pays** (50+ pays, villes principales incluses pour élargir la recherche)
- Sélection **multiple de secteurs** depuis un catalogue prétraduit (73 secteurs, FR/EN/DE/ES/IT/PT/NL)
  ou saisie d'un secteur libre en français, traduit automatiquement dans la langue du pays
- Nombre max. de résultats : 5, 10, 20, 50, 100, 200, 300
- Mode de pertinence **Strict** (aucun site web + quasi invisibles) ou **Flexible** (site absent,
  obsolète ou HS + faible présence)
- Score de présence 0-100, verdict (Prioritaire / Cible / Hors cible), diagnostic détaillé, opportunité
  suggérée (création de site, refonte + SEO, SEO)
- **Registre officiel** : pour la France, SIREN/SIRET, forme juridique, NAF, dirigeants, effectif, date de
  création, n° TVA via l'API publique gratuite « Recherche d'entreprises » ; pour les autres pays, lien de
  recherche pré-rempli vers le registre national
- **Cache 30 jours** (SQLite) des recherches fournisseurs et des analyses : une recherche identique ou
  partiellement identique relancée ne consomme aucun crédit API (paramétrable, vidable depuis ⚙)
- Résultats en direct pendant l'analyse, filtre, fiche détaillée, **export CSV / Excel / PDF** (rapport
  prêt à partager sur WhatsApp ou par e-mail, avec les données légales)

## Sources de données

| Étape | Avec clé API | Sans clé |
|---|---|---|
| Recherche d'entreprises | Google Places API (New) | OpenStreetMap / Nominatim (couverture variable) |
| Visibilité web & réseaux | SerpAPI (Google) | DuckDuckGo (best-effort, souvent limité) |
| Traduction des secteurs | — | catalogue intégré, puis Google Translate via `deep-translator` |
| État du site web | requêtes HTTP directes (HTTPS, mobile, copyright, pages « en construction »…) | idem |
| Données légales | — | France : recherche-entreprises.api.gouv.fr (gratuit) ; ailleurs : lien vers le registre |

Les clés se configurent dans l'application (⚙ en bas de la barre latérale) et sont stockées dans le
dossier de configuration utilisateur (`~/.config/Prospexia/config.json` sous Linux).

## Installation & lancement

Prérequis : Python ≥ 3.11 et [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev      # crée .venv et installe les dépendances
uv run prospexia         # lance l'application
```

### Lanceur dans le menu des applications (Linux)

```bash
scripts/install-desktop.sh   # ajoute « Prospexia » (icône incluse) au menu de l'utilisateur courant
```

## Développement

```bash
uv run pytest -q                       # tests (rendu Qt offscreen)
uv run pytest tests/test_scoring.py -q # un fichier
uv run ruff check --fix prospexia      # lint
```
