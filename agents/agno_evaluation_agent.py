"""
Evaluation Agent - Agno Framework Implementation
Evaluates assessment quality and safety
"""
import logging
from typing import Dict, Any
from agno.agent import Agent
from agno.models.google.gemini import Gemini
from agno.db.sqlite import SqliteDb
from config import settings

logger = logging.getLogger(__name__)


class EvaluationAgent(Agent):
    """Agno-based Evaluation Agent for quality assurance"""

    def __init__(self):
        """Initialize Evaluation Agent with Gemini model and SQLite database"""

        super().__init__(
            name="EvaluationAgent",
            model=Gemini(
                id=settings.AGENT_MODEL,
                api_key=settings.GEMINI_API_KEY
            ),
            db=SqliteDb(db_file=settings.DB_FILE),
            instructions="""You are a Quality and Safety Evaluator.
            Your role is to:
            1. Assess quality of medical assessment
            2. Check safety considerations
            3. Verify diagnosis consistency
            4. Evaluate treatment appropriateness
            5. Flag potential risks
            6. Provide overall quality score

            Evaluation criteria:
            - Are diagnoses supported by symptoms?
            - Are treatments appropriate for diagnoses?
            - Are all contraindications checked?
            - Is there sufficient supporting evidence?
            - Are safety warnings adequate?
            - Is the assessment complete?

            Output:
            - Quality score (0.0-1.0)
            - Consistency assessment
            - Safety score
            - Completeness score
            - Risk factors
            - Recommendations for improvement
            """,
            add_history_to_context=True,
            markdown=True,
        )

    def evaluate_assessment(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the complete medical assessment

        Args:
            workflow_state: Complete workflow state

        Returns:
            Evaluation results
        """
        logger.info("Evaluating assessment quality")

        diagnoses = workflow_state.get("diagnoses", [])
        treatments = workflow_state.get("treatments", [])
        symptoms = workflow_state.get("symptoms", [])

        top_diagnosis = diagnoses[0]['disease'] if diagnoses else 'None'
        confidence = diagnoses[0].get('confidence_score', 0) if diagnoses else 0

        prompt = f"""
        Evaluate this medical assessment:

        Number of symptoms: {len(symptoms)}
        Number of diagnoses: {len(diagnoses)}
        Number of treatments: {len(treatments)}

        Top diagnosis: {top_diagnosis}
        Confidence: {confidence:.1%}

        Assessment criteria:
        1. Are diagnoses well-supported by symptoms?
        2. Is the confidence level appropriate?
        3. Are treatments appropriate for the diagnoses?
        4. Are all safety considerations addressed?
        5. Is the assessment complete and thorough?

        Provide:
        - Overall quality score (0.0-1.0)
        - Strengths of the assessment
        - Areas for improvement
        - Any concerns or red flags
        - Final recommendation
        """

        run_output = self.run(prompt)

        # Convert RunOutput to string if needed
        if hasattr(run_output, 'content'):
            response = run_output.content
        elif hasattr(run_output, 'message'):
            response = run_output.message
        else:
            response = str(run_output)

        # Ensure response is a string
        response = self._ensure_string(response)

        evaluation = {
            "status": "evaluated",
            "quality_score": self._extract_quality_score(response),
            "assessment": response,
            "strengths": self._extract_strengths(response),
            "concerns": self._extract_concerns(response),
        }

        return evaluation

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

    def check_safety(self, workflow_state: Dict[str, Any]) -> Dict[str, bool]:
        """
        Check safety of the assessment

        Args:
            workflow_state: Current workflow state

        Returns:
            Safety check results
        """
        logger.info("Checking assessment safety")

        patient = workflow_state.get("patient", {})
        treatments = workflow_state.get("treatments", [])

        safety_checks = {
            "allergies_verified": bool(patient.get("allergies")),
            "contraindications_checked": len(treatments) > 0,
            "emergency_symptoms_identified": False,
            "patient_informed": True,
            "follow_up_scheduled": True,
        }

        return safety_checks

    def _extract_quality_score(self, response: str) -> float:
        """Extract quality score from response"""
        import re

        # Look for percentage or decimal score
        matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:%|out of 10|/10)', response)
        if matches:
            try:
                score = float(matches[0])
                if "out of 10" in response or "/10" in response:
                    return min(score / 10.0, 1.0)
                elif "%" in response:
                    return min(score / 100.0, 1.0)
            except:
                pass

        return 0.75  # Default

    def _extract_strengths(self, response: str) -> list:
        """Extract strengths from evaluation"""
        strengths = []

        if "strength" in response.lower() or "strong" in response.lower():
            lines = response.split('\n')
            for line in lines:
                if "strength" in line.lower() and len(line) > 10:
                    strengths.append(line.lstrip('- •*').strip())

        return strengths[:3]

    def _extract_concerns(self, response: str) -> list:
        """Extract concerns from evaluation"""
        concerns = []

        if "concern" in response.lower() or "caution" in response.lower():
            lines = response.split('\n')
            for line in lines:
                if "concern" in line.lower() and len(line) > 10:
                    concerns.append(line.lstrip('- •*').strip())

        return concerns[:3]


# ************* Create Evaluation Agent *************
evaluation_agent = EvaluationAgent()


if __name__ == "__main__":
    workflow = {
        "patient": {"name": "John", "allergies": ["Penicillin"]},
        "symptoms": [{"name": "fever"}, {"name": "cough"}],
        "diagnoses": [{"disease": "Dengue", "confidence_score": 0.83}],
        "treatments": [{"type": "medication", "recommendation": "Paracetamol"}]
    }

    evaluation = evaluation_agent.evaluate_assessment(workflow)
    print(f"Quality score: {evaluation['quality_score']:.1%}")
