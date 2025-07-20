# Étape 1 : Choisir une image de base
FROM python:3.10-slim

# Étape 2 : Définir le répertoire de travail dans le container
WORKDIR /app
ENV PYTHONPATH=/app

# Étape 3 : Copier les fichiers nécessaires dans le container
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Étape 4 : Copier le reste de l'app
COPY . .

# Étape 5 : Lancer le serveur FastAPI via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
