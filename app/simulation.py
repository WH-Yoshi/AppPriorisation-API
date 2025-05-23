import json
import math
from typing import Dict, List, Any, Optional, Tuple

import psycopg2
import pandas as pd

from app.database.calls import insert_project
from app.database.config import load_config
from app.pydantic_models import ProjectRequest


class PrioritizationSystem:
    """Main class for prioritizing renovation works."""

    def __init__(self, project_data: ProjectRequest):
        """
        Initializes the prioritization system with project data.
        
        Args:
            project_data: Renovation project data
        """
        self.project_data = project_data.model_dump()
        self.weights = self._load_weights()
        self.income_category, self.prime_multiplier = self._calculate_income_category()
        print(f"Income category: {self.income_category}, Grant multiplier: {self.prime_multiplier}")
        self.works_df = self._load_work_from_db()
        self.profile_factors = self._get_profile_factors()
        self.works_criteria = self._load_works_criteria()

    def _load_weights(self) -> Dict[str, float]:
        """
        Loads and normalizes criteria weights.
        
        Returns:
            Dictionary of normalized weights
        """
        with open("app/weighting/desires.json", 'r') as f:
            raw_weights = json.load(f)
        total = sum(raw_weights.values())
        return {k: v / total for k, v in raw_weights.items()}

    def _load_works_criteria(self) -> Dict[str, List[str]]:
        """
        Loads criteria associated with each type of work.
        
        Returns:
            Dictionary of criteria by work type
        """
        with open("app/weighting/work_criteria.json", 'r') as f:
            return json.load(f)

    def _calculate_income_category(self) -> Tuple[str, int]:
        """
        Determines the income category and associated grant multiplier.
        
        Returns:
            Tuple containing the income category and multiplier
        """
        income = int(self.project_data['budgetData']['householdIncome'])
        child_nbr = int(self.project_data['budgetData']['childNumber'])
        income = income - (5000 * child_nbr)

        with open("app/weighting/incomes.json", 'r') as f:
            revenus = json.load(f)

        multiplier = {'R1': 6, 'R2': 4, 'R3': 3, 'R4': 2}
        for category, threshold in revenus.items():
            if income <= threshold:
                return category, multiplier[category]

        return "Not applicable", 0

    def _load_work_from_db(self) -> pd.DataFrame:
        """
        Loads the list of works from the database.
        
        Returns:
            DataFrame containing information on available works
        """
        config = load_config()
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            SELECT genre, description, estimated_prime, is_prime_by_surface, estimated_cost, is_cost_by_surface FROM work_list
                            """)
                travaux = [(row[0], row[1], row[2], row[3], row[4], row[5]) for row in cur.fetchall()]

        return pd.DataFrame(travaux, columns=["Type", "Description", "Estimated Grant", "Grant by surface?", "Estimated Cost", "Cost by surface?"])

    def _get_profile_factors(self) -> Dict[str, float]:
        """
        Gets the weighting factors associated with the chosen user profile.
        
        Returns:
            Dictionary of weighting factors
        """
        profil_factors = {
            "Eco-friendly": {
                'Environmental sustainability': 1.2,
                'Renewable energy production': 1.2,
                'Thermal insulation': 1.1
            },
            "Economy": {
                'Energy savings': 1.2,
                'Thermal insulation': 1.1,
                'Infrastructure modernization': 1.1
            },
            "Valuation": {
                'Increase in property value': 1.3,
                'Infrastructure modernization': 1.2
            },
            "Comfort": {
                'Comfort and well-being': 1.3,
                'Thermal insulation': 1.2,
                'Infrastructure modernization': 1.1
            }
        }

        return profil_factors.get(self.project_data['profileData'], {})

    def _calculate_roof_surface(self) -> float:
        """
        Calculates the roof surface based on floor area and roof type.
        
        Returns:
            Roof surface in m²
        """
        floor_surface = int(self.project_data['housingData']['surface'])
        roof_type = self.project_data['housingData']['roofType']
        floor_length = floor_width = math.sqrt(floor_surface)

        if roof_type == "flat":
            return floor_surface
        elif roof_type == "single":
            roof_height = floor_length * math.tan(math.radians(37.5))
            roof_width = math.sqrt(roof_height**2 + floor_width**2)
            return floor_length * roof_width
        elif roof_type == "double":
            roof_height = (floor_length / 2) * math.tan(math.radians(37.5))
            roof_width = math.sqrt(roof_height**2 + floor_width**2)
            return 2 * (roof_width * floor_length)
        else:
            raise ValueError(f"Invalid roof type: {roof_type}")

    def _calculate_base_scores(self) -> pd.DataFrame:
        """
        Calculates base scores for each type of work.
        
        Returns:
            DataFrame with calculated base scores
        """
        df = self.works_df.copy()
        df['Score'] = 0.0

        for idx, row in df.iterrows():
            genre = row['Type']
            criteres = self.works_criteria.get(genre, [])

            score_total = 0
            for critere in criteres:
                base_score = self.weights.get(critere, 0)
                facteur = self.profile_factors.get(critere, 1)
                score_total += base_score * facteur

            df.at[idx, 'Score'] = score_total

        return df

    def _apply_housing_adjustments(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies score adjustments based on housing characteristics.
        
        Args:
            df: DataFrame of works with base scores
            
        Returns:
            DataFrame with adjusted scores
        """
        logement_data = self.project_data['housingData']

        # Adjustments for heating
        if logement_data.get('heatingType') != "heat_pump":
            mask = df['Description'] == "Heat pump"
            df.loc[mask, 'Score'] += (
                    self.weights.get('Environmental sustainability', 0) *
                    self.profile_factors.get('Environmental sustainability', 1)
            )
        else:
            df.loc[df['Description'] == "Heat pump", 'Score'] = 0

        # Adjustment for programmable thermostat
        if logement_data.get('programmableThermostat') == "no":
            mask = df['Description'] == "Programmable Thermostat"
            df.loc[mask, 'Score'] += (
                    self.weights.get('Energy savings', 0) *
                    self.profile_factors.get('Energy savings', 1)
            )
        else:
            df.loc[df['Description'] == "Programmable Thermostat", 'Score'] = 0

        # Adjustments for temperature
        if logement_data.get('averageTemperature') == "<18":
            adjustments = [
                ("Programmable Thermostat", 'Energy savings'),
                ("Wall thermal insulation", 'Comfort and well-being'),
                ("Roof or attic thermal insulation", 'Thermal insulation'),
                ("Floor thermal insulation", 'Comfort and well-being')
            ]

            for desc, factor_key in adjustments:
                mask = df['Description'] == desc
                df.loc[mask, 'Score'] += (
                        self.weights.get(factor_key, 0) *
                        self.profile_factors.get(factor_key, 1)
                )

        # Adjustments for insulation
        if logement_data.get('wallInsulation') == "no":
            mask = df['Description'] == "Wall thermal insulation"
            df.loc[mask, 'Score'] += (
                    self.weights.get('Thermal insulation', 0) *
                    self.profile_factors.get('Thermal insulation', 1)
            )

        if logement_data.get('roofInsulation') == "no":
            mask = df['Description'] == "Roof or attic thermal insulation"
            df.loc[mask, 'Score'] += (
                    self.weights.get('Thermal insulation', 0) *
                    self.profile_factors.get('Thermal insulation', 1)
            )

        if logement_data.get('floorInsulation') == "no":
            mask = df['Description'] == "Floor thermal insulation"
            df.loc[mask, 'Score'] += (
                    self.weights.get('Thermal insulation', 0) *
                    self.profile_factors.get('Thermal insulation', 1)
            )

        return df

    def _apply_budget_adjustments(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies score adjustments based on budget.
        
        Args:
            df: DataFrame of works with initial scores
            
        Returns:
            DataFrame with scores adjusted according to budget
        """
        budget_data = self.project_data['budgetData']
        total_budget = int(budget_data['totalBudget'])
        household_income = int(budget_data['householdIncome'])

        # Score reduction for overly expensive works
        if total_budget < household_income:
            df['Score'] = df.apply(
                lambda x: x['Score'] * 0.8 if x['Estimated Grant'] > total_budget else x['Score'],
                axis=1
            )

        # Adjustments according to property type
        property_type = budget_data.get('propertyType')
        if property_type == "house":
            df['Score'] = df.apply(
                lambda x: x['Score'] * 1.1 if x['Type'] in ["Roofing", "Walls", "Floors"] else x['Score'],
                axis=1
            )
        elif property_type == "apartment":
            df['Score'] = df.apply(
                lambda x: x['Score'] * 0.9 if x['Type'] == "Roofing" else x['Score'],
                axis=1
            )

        # Adjustments according to renovation method
        renovation_method = budget_data.get('renovationMethod')
        if renovation_method == "professional":
            df['Score'] = df.apply(
                lambda x: x['Score'] * 1.1 if x['Type'] in ["Heating", "Joinery"] else x['Score'],
                axis=1
            )
        elif renovation_method == "do_it_yourself":
            df['Score'] = df.apply(
                lambda x: x['Score'] * 0.9 if x['Type'] == "Heating" else x['Score'],
                axis=1
            )

        return df

    def _apply_technical_adjustments(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies technical adjustments based on dwelling characteristics.

        Args:
            df: DataFrame of works with initial scores

        Returns:
            DataFrame with scores adjusted according to technical characteristics
        """
        # Example of technical adjustment
        if self.project_data['technicalData']['hasSolarPanels'] == "yes":
            mask = df['Description'] == "Installation of photovoltaic panels"
            df.loc[mask, 'Score'] += (
                    self.weights.get('Renewable energy production', 0) *
                    self.profile_factors.get('Renewable energy production', 1)
            )

        if self.project_data['technicalData']['hasWaterHeater'] == "yes":
            mask = df['Description'] == "Solar water heater"
            df.loc[mask, 'Score'] += (
                    self.weights.get('Environmental sustainability', 0) *
                    self.profile_factors.get('Environmental sustainability', 1)
            )

        if self.project_data['technicalData']['boilerType'] != "heat_pump":
            mask = (df['Description'] == "Heat pump") & (df['Type'] == "Hot water")
            df.loc[mask, 'Score'] += (
                    self.weights.get('Environmental sustainability', 0) *
                    self.profile_factors.get('Environmental sustainability', 1)
            )

        if self.project_data['technicalData']['ventilationType'] not in ["mechanical", "double_flow"]:
            mask = df['Description'] == "Controlled mechanical ventilation"
            df.loc[mask, 'Score'] += (
                    self.weights.get('Energy savings', 0) *
                    self.profile_factors.get('Energy savings', 1)
            )

        return df

    def _calculate_eligible_prime(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the eligible grant for each type of work.

        Args:
            df: DataFrame of prioritized works

        Returns:
            DataFrame with calculated eligible grants
        """
        surface_totale = int(self.project_data['housingData']['surface'])
        floor_number = int(self.project_data['budgetData']['floorNumber'])
        wall_surface = self._calculate_wall_surface(floor_number)
        roof_surface = self._calculate_roof_surface()

        plafonds = {
            'R1': 0.7,
            'R2': 0.7,
            'R3': 0.5,
            'R4': 0.5
        }
        plafond = plafonds.get(self.income_category, 0)

        def prime_eligible(row):
            prime = row['Estimated Grant'] * self.prime_multiplier
            surface = wall_surface if row['Type'] == "Walls" else (roof_surface if row['Type'] == "Roofing" else surface_totale)

            if row['Grant by surface?']:
                if row['Cost by surface?']:
                    prime_max = (row['Estimated Cost'] * surface) * plafond
                else:
                    prime_max = row['Estimated Cost'] * plafond
                prime = prime * surface
            else:
                if row['Cost by surface?']:
                    prime_max = (row['Estimated Cost'] * surface) * plafond
                else:
                    prime_max = row['Estimated Cost'] * plafond

            return min(prime, prime_max)

        df['Eligible Grant'] = df.apply(prime_eligible, axis=1)
        return df

    def prioritize(self) -> pd.DataFrame:
        """
        Prioritizes renovation works based on all criteria.
        
        Returns:
            DataFrame of prioritized works with scores and grants
        """
        # Add income categories to project data
        self.project_data['incomeCategory'] = self.income_category
        self.project_data['primeMultiplier'] = self.prime_multiplier

        # Calculate base scores
        df = self._calculate_base_scores()

        # Apply adjustments based on dwelling
        df = self._apply_housing_adjustments(df)

        # Apply adjustments based on budget
        df = self._apply_budget_adjustments(df)

        # Apply technical adjustments
        df = self._apply_technical_adjustments(df)

        # Remove rows with zero scores
        df = df[df['Score'] > 0]

        # Sort by score in descending order
        df = df.sort_values(by='Score', ascending=False)

        # Calculate eligible grants
        df = self._calculate_eligible_prime(df)

        return df

    def _calculate_wall_surface(self, floor_number) -> Tuple[float, float]:
        """
        Calculates the wall surface based on the number of floors and floor area.

        Args:
            floor_number: Number of floors

        Returns:
            Wall surface in m²
        """
        floor_surface = int(self.project_data['housingData']['surface'])
        wall_height = 2.5
        floor_circumference = math.sqrt(floor_surface) * 4
        return floor_circumference * wall_height * floor_number


def prioritize(project_data: ProjectRequest) -> pd.DataFrame:
    """
    Main entry point for prioritizing works.
    
    Args:
        project_data: Renovation project data
        
    Returns:
        DataFrame of prioritized works
    """
    insert_project(project_data)
    system = PrioritizationSystem(project_data)
    prioritized_works = system.prioritize()

    print("\nList of prioritized works:\n")
    print(prioritized_works.to_string(index=False))

    return prioritized_works