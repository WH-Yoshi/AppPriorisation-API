import psycopg2
from psycopg2 import connect

from app.database.config import load_config


def create_tables():
    """Create tables in the PostgreSQL database"""

    commands = (
        """
        CREATE TABLE IF NOT EXISTS Owner (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            firstname VARCHAR(50) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Home (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            profile VARCHAR(50) NOT NULL,
            region VARCHAR(255) NOT NULL,
            construction_year VARCHAR(50) NULL,
            surface VARCHAR(50) NOT NULL,
            roof_type VARCHAR(50) NOT NULL,
            housing_type VARCHAR(50) NOT NULL,
            peb_label VARCHAR(1) NULL,
            heating_type VARCHAR(50) NOT NULL,
            average_temp VARCHAR(50) NOT NULL,
            programmable_thermostat VARCHAR(50) NOT NULL,
            windows_type VARCHAR(50) NOT NULL,
            wall_insulation VARCHAR(50) NOT NULL,
            roof_insulation VARCHAR(50) NOT NULL,
            floor_insulation VARCHAR(50) NOT NULL,
            house_income VARCHAR(50) NOT NULL,
            child_number VARCHAR(50) NOT NULL,
            renovation_method VARCHAR(50) NOT NULL,
            floor_number VARCHAR(50) NOT NULL,
            has_solar_panels VARCHAR(50) NOT NULL,
            has_water_heater VARCHAR(50) NOT NULL,
            boiler_type VARCHAR(50) NOT NULL,
            ventilation_type VARCHAR(50) NOT NULL,
            onwer_id INT NOT NULL,
            FOREIGN KEY (onwer_id) REFERENCES Owner (id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Simulation (
            id SERIAL PRIMARY KEY,
            date VARCHAR(50) NOT NULL,
            details JSONB,
            home_id INT NOT NULL,
            FOREIGN KEY (home_id) REFERENCES Home (id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Work_list (
            id SERIAL PRIMARY KEY,
            genre VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            estimated_prime FLOAT NULL,
            is_prime_by_surface BOOLEAN NOT NULL,
            estimated_cost FLOAT NOT NULL,
            is_cost_by_surface BOOLEAN NOT NULL,
            UNIQUE(genre, description)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Test (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            details JSONB
        )
        """
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
                    INSERT INTO Work_list 
                        (genre, description, estimated_prime, is_prime_by_surface, estimated_cost, is_cost_by_surface)
                    VALUES 
                        ('Toiture', 'Remplacement de la couverture', 4, TRUE, 70.0, TRUE),
                        ('Toiture', 'Appropriation de la charpente', 100, FALSE, 95.0, TRUE),
                        ('Toiture', 'Isolation thermique du toit ou des combles', 20, TRUE, 40.0, TRUE),
                        ('Murs', 'Isolation thermique des murs', 8.8, TRUE, 125.0, TRUE),
                        ('Sols', 'Isolation thermique des sols', 6, TRUE, 35.0, TRUE),
                        ('Menuiseries et Vitrage', 'Remplacement des menuiseries extérieures ou revitrage', 26, TRUE, 100.0, TRUE),
                        ('Chauffage', 'Pompe à chaleur', 600, FALSE, 10000.0, FALSE),
                        ('Chauffage', 'Chaudière biomasse', 720, FALSE, 12500, FALSE),
                        ('Chauffage', 'Thermostat Programmable', 16, FALSE, 100.0, FALSE),
                        ('Eau chaude', 'Pompe à chaleur', 280, FALSE, 7500.0, FALSE),
                        ('Eau chaude', 'Chauffe-eau solaire', 420, FALSE, 5000.0, FALSE),
                        ('Energie', 'Installation de panneaux photovoltaïques', 0, FALSE, 7000.0, FALSE),
                        ('Ventilation', 'Ventilation double flux avec échangeur thermique', 680, FALSE, 5500.0, FALSE)
                    ON CONFLICT (genre, description) DO NOTHING
                """)
            conn.commit()
    except (psycopg2.DatabaseError, Exception) as error:
        raise error