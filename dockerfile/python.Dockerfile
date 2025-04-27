# Utiliser une image de base Python
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers du projet dans le conteneur
COPY . /app

# Installer les dépendances requises via pip
RUN pip install --no-cache-dir -r ./requirements.txt

# Exécuter le crawler (assurez-vous que votre script est le bon point d'entrée)
CMD ["python", "./src/crawler.py"]