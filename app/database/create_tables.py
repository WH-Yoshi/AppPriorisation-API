import psycopg2
from psycopg2 import connect

from app.database.config import load_config


def create_tables():
    """Create tables in the PostgreSQL database"""

    commands = (
        """
        CREATE TABLE IF NOT EXISTS Proprietaire (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(50) NOT NULL,
            prenom VARCHAR(50) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Habitation (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            objectif VARCHAR(50) NOT NULL,
            region VARCHAR(255) NOT NULL,
            annee_construction INT NOT NULL,
            surface INT NOT NULL,
            type_logement VARCHAR(50) NOT NULL,
            label_peb VARCHAR(1) NOT NULL,
            type_chauffage VARCHAR(50) NOT NULL,
            temperature_moyenne INT NOT NULL,
            thermostat_programmable BOOLEAN NOT NULL,
            type_fenetre VARCHAR(50) NOT NULL,
            isolation_mur BOOLEAN NOT NULL,
            isolation_toit BOOLEAN NOT NULL,
            isolation_sol BOOLEAN NOT NULL,
            revenu_menage INT NOT NULL,
            nombre_enfants INT NOT NULL,
            methode_renovation VARCHAR(50) NOT NULL,
            proprietaire_id INT NOT NULL,
            FOREIGN KEY (proprietaire_id) REFERENCES Proprietaire (id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Travaux (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            type_travaux VARCHAR(50) NOT NULL,
            cout_estime INT NOT NULL,
            prime_estime INT NULL,
            habitation_id INT NOT NULL,
            FOREIGN KEY (habitation_id) REFERENCES Habitation (id)
        )    
        """,
        """
        CREATE TABLE IF NOT EXISTS Simulation (
            id SERIAL PRIMARY KEY,
            date VARCHAR(50) NOT NULL,
            budget_max INT NOT NULL,
            liste_travaux_id INT NOT NULL,
            habitation_id INT NOT NULL,
            FOREIGN KEY (liste_travaux_id) REFERENCES Travaux (id),
            FOREIGN KEY (habitation_id) REFERENCES Habitation (id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Prime (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            type_travaux VARCHAR(50) NOT NULL,
            montant_max INT NOT NULL,
            conditions TEXT NOT NULL,
            revenu_max_eligible INT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Simulation_Travaux (
            simulation_id INT NOT NULL,
            travaux_id INT NOT NULL,
            FOREIGN KEY (simulation_id) REFERENCES Simulation (id),
            FOREIGN KEY (travaux_id) REFERENCES Travaux (id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Liste_Travaux (
            id SERIAL PRIMARY KEY,
            genre VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            prime_estime FLOAT NULL,
            par_surface BOOLEAN NOT NULL,
            UNIQUE(genre, description)
        )
        """,
        )

    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cursor:
                for command in commands:
                    cursor.execute(command)
                conn.commit()

    except (psycopg2.DatabaseError, Exception) as error:
        raise error


def insert_data():
    """Insert works data into the tables"""
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Liste_Travaux 
                        (genre, description, prime_estime, par_surface) 
                    VALUES 
                        ('Toiture', 'Remplacement de la couverture', 4, TRUE),
                        ('Toiture', 'Appropriation de la charpente', 100, FALSE),
                        ('Toiture', 'Remplacement d’un dispositif de collecte et d’évacuation des eaux pluviales', 40, FALSE),
                        ('Toiture', 'Isolation thermique du toit ou des combles', 20, TRUE),
                        ('Murs', 'Assèchement des murs – infiltration', 2.4, TRUE),
                        ('Murs', 'Assèchement des murs – humidité ascensionnelle', 3.2, TRUE),
                        ('Murs', 'Renforcement/reconstruction des murs instables', 3.2, TRUE),
                        ('Murs', 'Isolation thermique des murs', 8.8, TRUE),
                        ('Sols', ' Isolation thermique des sols', 6, TRUE),
                        ('Menuiseries', 'Remplacement des menuiseries extérieures ou revitrage', 26, TRUE),
                        ('Chauffage', 'Pompe à chaleur', 600, FALSE),
                        ('Chauffage', 'Chaudière biomasse', 720, FALSE),
                        ('Eau chaude', 'Pompe à chaleur', 280, FALSE),
                        ('Eau chaude', 'Chauffe-eau solaire', 420, FALSE)
                    ON CONFLICT (genre, description) DO NOTHING
                """)
            conn.commit()
    except (psycopg2.DatabaseError, Exception) as error:
        raise error