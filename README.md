# Reddit Crawler

Ce projet est un crawler conçu pour extraire des données depuis le site Reddit. Il permet de collecter des informations sur les posts, les commentaires, et d'autres métadonnées utiles pour des analyses ou des projets de recherche.

## Fonctionnalités
- Extraction de posts et commentaires.
- Export des données au format JSON pour le debug.
-  Export des données dans une base données PGSQL

## Installation

### Prérequis
- Python 3.12 ou supérieur
- `pip` (gestionnaire de paquets Python)

### Étapes d'installation
1. Clonez le dépôt :
    ```bash
    git clone <URL_DU_DEPOT>
    cd <NOM_DU_DEPOT>
    ```

2. Créez un environnement virtuel :
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Sur Windows : venv\Scripts\activate
    ```

3. Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
4. Le .env est fournis pour permettre de lancer le prjet plus facilement.

## Docker

Le docker du projet contient deux images:
- Une base de données PostgreSQL (car je n'avais pas les droits su snowflakes)
- Une image pour lancer le crawler

## Utilisation
Lancez le script principal pour démarrer le crawler :
```bash
python src/crawler.py 
```
Le projet est aussi sous docker:
```bash
docker compse build
docker compose up ( si vous voulez voir l'avancement du crawler)
```

on peut ajouter le `--debug <nom du fichier.json>` pour extraire les données dans un fichier `.json` 
