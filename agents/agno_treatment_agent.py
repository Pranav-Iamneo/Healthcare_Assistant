"""
Treatment Agent - Agno Framework Implementation
Recommends treatments and interventions
"""
import logging
from typing import List, Dict, Any
from agno.agent import Agent
from agno.models.google.gemini import Gemini
from agno.db.sqlite import SqliteDb
from config import settings

logger = logging.getLogger(__name__)


class TreatmentAgent(Agent):
    """Agno-based Treatment Agent for medical recommendations"""

    def __init__(self):
        """Initialize Treatment Agent with Gemini model and SQLite database"""

        super().__init__(
            name="TreatmentAgent",
            model=Gemini(
                id=settings.AGENT_MODEL,
                api_key=settings.GEMINI_API_KEY
            ),
            db=SqliteDb(db_file=settings.DB_FILE),
            instructions="""You are a Treatment Recommendation Specialist.
            Your role is to:
            1. Recommend appropriate treatments
            2. Check for contraindications
            3. Verify allergy compatibility
            4. Suggest diagnostic tests
            5. Provide lifestyle advice
            6. Consider drug interactions

            For each recommendation, provide:
            - Type (medication/test/lifestyle/consultation)
            - Specific recommendation
            - Justification
            - Dosage if applicable
            - Warnings and precautions
            - Duration

            Always:
            - Check patient allergies
            - Verify no drug interactions
            - Consider patient age and conditions
            - Recommend evidence-based treatments
            - Flag any safety concerns
            - Suggest follow-up care
            """,
            add_history_to_context=True,
            markdown=True,
        )

    def recommend_treatments(
        self,
        diagnoses: List[Dict[str, Any]],
        patient_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Recommend treatments for diagnoses

        Args:
            diagnoses: List of diagnoses
            patient_info: Patient information

        Returns:
            List of treatment recommendations
        """
        logger.info("Recommending treatments")

        if not diagnoses:
            return []

        diseases = [d["disease"] for d in diagnoses[:2]]  # Top 2 diagnoses

        prompt = f"""
        Recommend treatments for:

        Patient Information:
        - Age: {patient_info.get('age', 'Unknown')}
        - Allergies: {', '.join(patient_info.get('allergies', ['None']))}
        - Current medications: {', '.join(patient_info.get('medications', ['None']))}
        - Medical history: {', '.join(patient_info.get('medical_history', ['None']))}

        Diagnoses:
        {chr(10).join(f'- {d}' for d in diseases)}

        Provide:
        1. Medication recommendations with dosage
        2. Diagnostic tests to confirm diagnosis
        3. Lifestyle modifications
        4. Any precautions or warnings
        5. When to seek emergency care

        Check for:
        - Drug interactions
        - Allergy contraindications
        - Age-appropriate dosing
        - Pregnancy considerations

        Format clearly with sections.
        """

        run_output = self.run(prompt)

        # Convert RunOutput to string if needed
        if hasattr(run_output, 'content'):
            response = run_output.content
        elif hasattr(run_output, 'message'):
            response = run_output.message
        else:
            response = str(run_output)

        treatments = self._parse_treatments(response, patient_info)

        logger.info(f"Generated {len(treatments)} treatment recommendations")

        return treatments

    def _ensure_string(self, obj: Any) -> str:
        """Ensure object is a string, extracting content if needed"""
        if isinstance(obj, str):
            return obj
        if hasattr(obj, 'content'):
            return str(obj.content)
        if hasattr(obj, 'message'):
            return str(obj.message)
        if hasattr(obj, 'text'):
            return str(obj.text)
        return str(obj)

    def _parse_treatments(
        self,
        response: str,
        patient_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse treatments from response"""

        treatments = []
        # Ensure response is a string
        response = self._ensure_string(response)
        lines = response.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to identify treatment type
            treatment_type = "medication"
            if "test" in line.lower() or "diagnostic" in line.lower():
                treatment_type = "test"
            elif "lifestyle" in line.lower() or "modify" in line.lower():
                treatment_type = "lifestyle"
            elif "consult" in line.lower() or "specialist" in line.lower():
                treatment_type = "consultation"

            if len(line) > 10:
                treatment = {
                    "type": treatment_type,
                    "recommendation": line.lstrip('- •*'),
                    "justification": "As recommended by medical guidelines",
                    "confidence": 0.75
                }
                treatments.append(treatment)

        return treatments[:10]  # Return top 10


# ************* Create Treatment Agent *************
treatment_agent = TreatmentAgent()


if __name__ == "__main__":
    diagnoses = [{"disease": "Dengue Fever", "confidence_score": 0.83}]
    patient = {
        "age": 35,
        "allergies": ["Penicillin"],
        "medications": [],
        "medical_history": []
    }

    treatments = treatment_agent.recommend_treatments(diagnoses, patient)
    print(f"Generated {len(treatments)} treatments")
