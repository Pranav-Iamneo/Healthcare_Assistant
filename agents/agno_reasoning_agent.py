"""
Reasoning Agent - Agno Framework Implementation
Applies medical logic and validates diagnoses
"""
import logging
from typing import List, Dict, Any
from agno.agent import Agent
from agno.models.google.gemini import Gemini
from agno.db.sqlite import SqliteDb
from config import settings

logger = logging.getLogger(__name__)


class ReasoningAgent(Agent):
    """Agno-based Reasoning Agent for medical logic validation"""

    def __init__(self):
        """Initialize Reasoning Agent with Gemini model and SQLite database"""

        super().__init__(
            name="ReasoningAgent",
            model=Gemini(
                id=settings.AGENT_MODEL,
                api_key=settings.GEMINI_API_KEY
            ),
            db=SqliteDb(db_file=settings.DB_FILE),
            instructions="""You are a Medical Reasoning Expert.
            Your role is to:
            1. Validate proposed diagnoses
            2. Check consistency with symptoms
            3. Apply medical logic rules
            4. Assess severity and urgency
            5. Identify potential pitfalls
            6. Provide reasoning transparency

            When validating diagnoses:
            - Check if symptoms match the disease pattern
            - Verify no contradictions exist
            - Assess if diagnosis explains all symptoms
            - Consider alternative possibilities
            - Rate confidence appropriately
            - Flag any urgent symptoms

            Your output should include:
            - Validation status (valid/questionable/invalid)
            - Reasoning explanation
            - Confidence assessment
            - Risk assessment
            - Alternative considerations
            """,
            add_history_to_context=True,
            markdown=True,
        )

    def validate_diagnoses(
        self,
        diagnoses: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate proposed diagnoses

        Args:
            diagnoses: List of proposed diagnoses
            symptoms: Patient symptoms

        Returns:
            Validation results
        """
        logger.info("Validating diagnoses")

        if not diagnoses:
            return {"status": "no_diagnoses", "message": "No diagnoses to validate"}

        symptom_names = [s["name"] for s in symptoms]

        prompt = f"""
        Validate these diagnoses:

        Symptoms: {', '.join(symptom_names)}

        Proposed Diagnoses:
        {chr(10).join(f'- {d["disease"]} (confidence: {d.get("confidence_score", 0.5):.1%})' for d in diagnoses[:3])}

        For each diagnosis, provide:
        1. Is it valid for these symptoms?
        2. How well do the symptoms match?
        3. What's the confidence level?
        4. Are there any contradictions?
        5. What tests would confirm this?

        Provide clear, logical reasoning for each assessment.
        """

        run_output = self.run(prompt)

        # Convert RunOutput to string if needed
        if hasattr(run_output, 'content'):
            response = run_output.content
        elif hasattr(run_output, 'message'):
            response = run_output.message
        else:
            response = str(run_output)

        validation_result = {
            "status": "validated",
            "reasoning": response,
            "adjusted_diagnoses": diagnoses,
        }

        return validation_result

    def assess_urgency(
        self,
        symptoms: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assess urgency of symptoms

        Args:
            symptoms: Patient symptoms

        Returns:
            Urgency assessment
        """
        logger.info("Assessing symptom urgency")

        urgent_symptoms = [
            "severe chest pain",
            "shortness of breath",
            "severe headache",
            "unconsciousness",
            "severe bleeding"
        ]

        urgency_level = "normal"
        for symptom in symptoms:
            if any(urgent in symptom.get("name", "").lower() for urgent in urgent_symptoms):
                urgency_level = "urgent"
                break

        return {
            "urgency_level": urgency_level,
            "requires_emergency": urgency_level == "urgent",
            "assessed_symptoms": [s["name"] for s in symptoms]
        }


# ************* Create Reasoning Agent *************
reasoning_agent = ReasoningAgent()


if __name__ == "__main__":
    diagnoses = [
        {"disease": "Dengue Fever", "confidence_score": 0.83},
        {"disease": "Influenza", "confidence_score": 0.65}
    ]
    symptoms = [
        {"name": "fever", "severity": "moderate"},
        {"name": "cough", "severity": "mild"}
    ]

    result = reasoning_agent.validate_diagnoses(diagnoses, symptoms)
    print(f"Validation status: {result['status']}")
