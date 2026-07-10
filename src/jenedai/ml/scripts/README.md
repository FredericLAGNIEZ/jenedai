



# Deploiement sur Prefect Cloud
## Se logger
Se logger avec le compte jenedai sur prefect et github ainsi que sur github

## Se placer dans l'environnement virtuel du projet
```bash
source .venv/bin/activate
```

## Login
```bash
prefect cloud login
```

## List prefect pools
```bash
prefect work-pool ls
```

## If not existing, create a pool named energy-pool
```bash
prefect work-pool create energy-pool --type prefect:managed
```


## Launch deployment on GithUb
```bash
prefect deploy -n consume-energy
```

## Config
Le fichier prefect.yaml à la racine sert de configuration

## UI
On peut observer les runs sur l'interface graphique. Attention, l'emploi des ressources CPU est limité à 500 minutes par cycle de facturation.


# Deploiement en local
Flow is being served with :
```bash
uv run python src/jenedai/ml/scripts/test_prefect.py
```

## To schedule a run
```bash
prefect deployment run 'consume_energy_etl/consume-energy'
```


##etl.serve(name="cpd-pipeline-deployment", cron="0 0 * * *")

## Resssources :
## Inspect deployment
```bash
prefect deployment inspect consume_energy_etl/consume-energy
```


## Delete deployment
```bash
 prefect deployment delete consume_energy_etl/consume-energy
```

## obberver le flow des runs
 prefect flow-run ls
