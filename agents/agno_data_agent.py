"""
Data Agent - Agno Framework Implementation
Fetches medical information from knowledge base
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from agno.agent import Agent
from agno.models.google.gemini import Gemini
from agno.db.sqlite import SqliteDb
from config import settings

logger = logging.getLogger(__name__)


class DataAgent(Agent):
    """Agno-based Data Agent for medical information retrieval"""

    def __init__(self):
        """Initialize Data Agent with Gemini model and SQLite database"""

        self.knowledge_base = self._load_knowledge_base()

        super().__init__(
            name="DataAgent",
            model=Gemini(
                id=settings.AGENT_MODEL,
                api_key=settings.GEMINI_API_KEY
            ),
            db=SqliteDb(db_file=settings.DB_FILE),
            instructions="""You are a medical data retrieval expert.
            Your role is to:
            1. Analyze symptoms provided by the patient
            2. Search the medical knowledge base for related diseases
            3. Extract relevant medical information
            4. Return structured data about possible conditions

            Always provide:
            - Disease names and descriptions
            - Associated symptoms
            - Prevalence rates
            - Risk factors
            - Possible complications
            - Treatment options
            - Diagnostic tests
            """,
            add_history_to_context=True,
            markdown=True,
        )

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load medical knowledge base from JSON file"""
        try:
            kb_path = Path(settings.KNOWLEDGE_BASE_FILE)
            if kb_path.exists():
                with open(kb_path, 'r') as f:
                    knowledge_base = json.load(f)
                logger.info(f"Loaded knowledge base with {len(knowledge_base.get('diseases', []))} diseases")
                return knowledge_base
            else:
                logger.warning(f"Knowledge base file not found at {kb_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            return {}

    def fetch_medical_data(self, symptoms: List[str]) -> Dict[str, Any]:
        """
        Fetch medical data based on symptoms

        Args:
            symptoms: List of symptom names

        Returns:
            Dictionary with medical data
        """
        logger.info(f"Fetching medical data for symptoms: {symptoms}")

        # Query knowledge base
        medical_data = {
            "diseases": [],
            "symptoms_found": [],
            "risk_factors": [],
            "treatments": [],
        }

        if not self.knowledge_base:
            logger.warning("Knowledge base is empty")
            return medical_data

        # Find diseases related to symptoms
        diseases = self.knowledge_base.get("diseases", [])
        symptom_to_disease = {}

        for disease in diseases:
            disease_symptoms = disease.get("symptoms", [])
            for symptom in symptoms:
                if symptom.lower() in [s.lower() for s in disease_symptoms]:
                    if disease["id"] not in symptom_to_disease:
                        symptom_to_disease[disease["id"]] = disease

        # Compile results
        medical_data["diseases"] = list(symptom_to_disease.values())
        medical_data["symptoms_found"] = symptoms

        # Extract unique risk factors and treatments
        for disease in medical_data["diseases"]:
            medical_data["risk_factors"].extend(disease.get("risk_factors", []))
            medical_data["treatments"].extend(disease.get("treatments", []))

        # Remove duplicates
        medical_data["risk_factors"] = list(set(medical_data["risk_factors"]))

        logger.info(f"Found {len(medical_data['diseases'])} related diseases")

        return medical_data

    def get_disease_info(self, disease_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific disease

        Args:
            disease_id: ID of the disease

        Returns:
            Disease information dictionary
        """
        diseases = self.knowledge_base.get("diseases", [])
        for disease in diseases:
            if disease["id"] == disease_id:
                return disease
        return {}

    def get_medications(self, disease_id: str) -> List[Dict[str, Any]]:
        """
        Get medications for a specific disease

        Args:
            disease_id: ID of the disease

        Returns:
            List of medication dictionaries
        """
        disease = self.get_disease_info(disease_id)
        return disease.get("treatments", [])

    def get_diagnostic_tests(self, disease_id: str) -> List[str]:
        """
        Get diagnostic tests for a specific disease

        Args:
            disease_id: ID of the disease

        Returns:
            List of diagnostic test names
        """
        disease = self.get_disease_info(disease_id)
        return disease.get("diagnostic_tests", [])

    def check_drug_interactions(self, drug1: str, drug2: str) -> Dict[str, Any]:
        """
        Check for drug interactions

        Args:
            drug1: First drug name
            drug2: Second drug name

        Returns:
            Interaction information
        """
        interactions = self.knowledge_base.get("drug_interactions", [])
        for interaction in interactions:
            if ((interaction["drug1"].lower() == drug1.lower() and
                 interaction["drug2"].lower() == drug2.lower()) or
                (interaction["drug1"].lower() == drug2.lower() and
                 interaction["drug2"].lower() == drug1.lower())):
                return interaction
        return {}

    def check_allergy(self, allergen: str) -> Dict[str, Any]:
        """
        Check allergy information

        Args:
            allergen: Allergen name

        Returns:
            Allergy information
        """
        allergies = self.knowledge_base.get("allergies", [])
        for allergy in allergies:
            if allergy["id"].lower() == allergen.lower():
                return allergy
        return {}

    def get_all_symptoms(self) -> List[Dict[str, Any]]:
        """
        Get all symptoms from knowledge base

        Returns:
            List of symptoms
        """
        return self.knowledge_base.get("symptoms", [])

    def get_all_diseases(self) -> List[Dict[str, Any]]:
        """
        Get all diseases from knowledge base

        Returns:
            List of diseases
        """
        return self.knowledge_base.get("diseases", [])


# ************* Create Data Agent *************
data_agent = DataAgent()


if __name__ == "__main__":
    # Test the agent
    symptoms = ["fever", "cough", "body ache"]
    result = data_agent.fetch_medical_data(symptoms)
    print(f"Found diseases: {len(result['diseases'])}")
    for disease in result['diseases']:
        print(f"  - {disease['name']}")
