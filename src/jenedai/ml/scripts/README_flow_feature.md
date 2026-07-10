tranckintgtracking


# Flow Prefect — Mise à jour du Feature Store Jenedai

## Vue d'ensemble

Ce flow orchestre la mise à jour hebdomadaire du feature store PostgreSQL de Jenedai, en enchaînant trois extractions séquentielles :

```
enedis_conso → météo → vacances scolaires
```

Chaque étape dépend de la précédente : les extractions météo et vacances scolaires auto-détectent leur plage de dates à partir des données Enedis fraîchement insérées, ce qui garantit la cohérence temporelle des trois sources dans le feature store.

## Prérequis

- Une base PostgreSQL accessible via `config.yaml` (profil `local` par défaut)
- Les scripts d'extraction présents dans `jenedai/data/connectors/` :
  - `extract_enedis_to_feature_store.py`
  - `extract_meteo_to_feature_store.py`
  - `extract_vacances_to_feature_store.py`
- `uv` installé pour l'exécution des sous-scripts

## Architecture

### Construction de l'engine SQLAlchemy

```python
_build_engine(config: Path, profile: str) -> sqlalchemy.Engine
```

Lit `config.yaml`, résout le profil (`local`), et construit une URL `postgresql+psycopg2://` avec gestion du `sslmode`. Réutilise la même logique que `query_table.py` pour rester cohérent avec le reste du projet.

### Exécution des scripts enfants

```python
_run(script: str, extra_args: list[str]) -> None
```

Lance chaque script d'extraction via `uv run python <script> --config ... --profile ...`, en subprocess, avec streaming des logs (`capture_output=False`). Lève une `RuntimeError` si le script échoue (`returncode != 0`), ce qui déclenche les retries Prefect au niveau de la tâche.

## Tâches

### `extract_enedis`

|                   |                                                     |
| ----------------- | --------------------------------------------------- |
| **Retries** | 2, délai 60s                                       |
| **Logique** | Calcule`date_start` via `MAX(horodate)` en base |

Comportement :

- **Table vide** → fallback sur `date_start = aujourd'hui - 7 jours`
- **Table déjà à jour** (`date_start >= date_end`) → skip silencieux, rien à extraire
- Sinon → extraction bornée à `MAX_RECORDS = 40 000` lignes

### `extract_meteo`

|                   |                                               |
| ----------------- | --------------------------------------------- |
| **Retries** | 2, délai 60s                                 |
| **Logique** | Dates auto-détectées depuis`enedis_conso` |

Ne prend aucun argument de date explicite — le script sous-jacent lit directement les horodates présentes dans `enedis_conso`, d'où la nécessité que `extract_enedis` s'exécute en premier.

### `extract_vacances`

|                   |                                               |
| ----------------- | --------------------------------------------- |
| **Retries** | 2, délai 60s                                 |
| **Logique** | Dates auto-détectées depuis`enedis_conso` |

Même principe que `extract_meteo` : dépend implicitement de `extract_enedis` pour connaître la plage temporelle à couvrir.

## Flow principal

```python
@flow(name="feature-store-daweekly-update")
def feature_store_update() -> None:
    date_end = date.today().isoformat()
    extract_enedis(date_end)
    extract_meteo()
    extract_vacances()
```

L'enchaînement est **séquentiel et strict** : chaque tâche attend la fin de la précédente (pas de parallélisation), car `meteo` et `vacances` dépendent des données fraîchement écrites par `enedis`.

## Utilisation

### Lancement manuel (one-shot)

```bash
uv run python flow_feature_store.py
```

Exécute le flow une seule fois, immédiatement.

### Déploiement avec schedule

```bash
uv run python flow_feature_store.py --deploy
```

Enregistre le flow via `.serve()` avec :

| Paramètre                  | Valeur                                       |
| --------------------------- | -------------------------------------------- |
| **name**              | `feature-store-weekly`                     |
| **cron**              | `0 3 * * 1` (tous les lundis à 03h00 UTC) |
| **tags**              | `jenedai`, `etl`, `feature-store`      |
| **pause_on_shutdown** | `False`                                    |
| **limit**             | `1` (une seule exécution concurrente)     |

## Points de vigilance

- **Ordre des tâches** : ne jamais paralléliser `extract_meteo`/`extract_vacances` avec `extract_enedis` — leur auto-détection de dates dépend des données Enedis déjà en base.
- **Idempotence** : le skip sur `date_start >= date_end` évite les extractions redondantes en cas de relance manuelle le même jour.
- **Limite Enedis** : `MAX_RECORDS = 40 000` reflète la contrainte de pagination connue de l'API Enedis (fenêtres mensuelles pour éviter le hard limit de 10k enregistrements par requête).
- **Échecs partiels** : si `extract_meteo` échoue après un `extract_enedis` réussi, une relance du flow re-déclenchera `extract_enedis` — celui-ci skippera correctement grâce à la vérification `MAX(horodate)`, évitant une double extraction.
