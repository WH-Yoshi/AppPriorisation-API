import psycopg2

from app.database.config import load_config
from app.pydantic_models import ProjectRequest
import pandas as pd


def prioritize(ProjectData: ProjectRequest):
    raw_weights = {
        'Confort et bien-être': 80,
        'Économies d\'énergie': 70,
        'Durabilité environnementale': 80,
        'Augmentation de la valeur immobilière': 30,
        'Isolation thermique': 45,
        'Production d\'énergie renouvelable': 41,
        'Modernisation des infrastructures': 50
    }

    # Normalisation pour que le total fasse 1
    total = sum(raw_weights.values())
    weights = {k: v / total for k, v in raw_weights.items()}

    config = load_config()
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT genre, description, prime_estime, par_surface FROM liste_travaux
            """)
            travaux = [(row[0], row[1], row[2], row[3]) for row in cur.fetchall()]

    df = pd.DataFrame(travaux, columns=["Genre", "Description", "Prime", "Prime par surface"])

    # === Facteurs de priorisation en pourcentage (0 à 1) ===
    factors = {
        'Isolation thermique': 0.6 if ProjectData['logementData']['windowType'] == 'simple_vitrage' else 0.3,
        'Production d\'énergie renouvelable': 0.5,
        'Modernisation des infrastructures': 0.4,
        'Économies d\'énergie': 0.7 if ProjectData['logementData']['programmableThermostat'] == 'oui' else 0.5,
        'Durabilité environnementale': 0.8 if ProjectData['profilData'] == 'Ecolo' else 0.5
    }

    # === Création de la matrice de décision ===
    df = pd.DataFrame(list(factors.items()), columns=['Critère', 'Facteur'])
    df['Pondération'] = df['Critère'].map(weights)
    df['Score'] = df['Facteur'] * df['Pondération']

    # === Tri des résultats par score décroissant ===
    df = df.sort_values(by='Score', ascending=False)

    # === Affichage des résultats ===
    print("\nMatrice de Décision Pondérée :\n")
    print(df.to_string(index=False))
