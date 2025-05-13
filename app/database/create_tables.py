import psycopg2
from config import load_config

# https://neon.tech/postgresql/postgresql-python/create-tables

def create_tables():
    """Create tables in the PostgreSQL database"""
    commands = (
        """
        CREATE TABLE IF NOT EXISTS Habitation (
            id SERIAL PRIMARY KEY,
            adresse VARCHAR(255) NOT NULL,
            annee_construction INT NOT NULL,
            surface INT NOT NULL,
            type_logement VARCHAR(50) NOT NULL,
            label_peb VARCHAR(1) NOT NULL,
            proprietaire_id INT NOT NULL,
            FOREIGN KEY (proprietaire_id) REFERENCES Proprietaire (id),
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Proprietaire (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(50) NOT NULL,
            prenom VARCHAR(50) NOT NULL,
            email VARCHAR(255) NOT NULL,
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
            strategie VARCHAR(50) NOT NULL,
            liste_travaux_id INT NOT NULL,
            habitation_id INT NOT NULL,
            FOREIGN KEY (liste_travaux_id) REFERENCES Travaux (id),
            FOREIGN KEY (habitation_id) REFERENCES Habitation (id),
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
            revenu_max_eligible INT NOT NULL,
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Simulation_Travaux (
            simulation_id INT NOT NULL,
            travaux_id INT NOT NULL,
            FOREIGN KEY (simulation_id) REFERENCES Simulation (id),
            FOREIGN KEY (travaux_id) REFERENCES Travaux (id),
        )
        """)
    try:
        config = load_config()
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                # execute the CREATE TABLE statement
                for command in commands:
                    cur.execute(command)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

if __name__ == '__main__':
    create_tables()