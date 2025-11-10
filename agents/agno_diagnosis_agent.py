"""
Diagnosis Agent - Agno Framework Implementation
Generates differential diagnoses based on symptoms
"""
import logging
from typing import List, Dict, Any
from agno.agent import Agent
from agno.models.google.gemini import Gemini
from agno.db.sqlite import SqliteDb
from config import settings

logger = logging.getLogger(__name__)


class DiagnosisAgent(Agent):
    """Agno-based Diagnosis Agent for medical analysis"""

    def __init__(self):
        """Initialize Diagnosis Agent with Gemini model and SQLite database"""

        super().__init__(
            name="DiagnosisAgent",
            model=Gemini(
                id=settings.AGENT_MODEL,
                api_key=settings.GEMINI_API_KEY
            ),
            db=SqliteDb(db_file=settings.DB_FILE),
            instructions="""You are an expert medical diagnostic assistant.
            Your role is to:
            1. Analyze patient symptoms
            2. Consider medical data and disease patterns
            3. Generate differential diagnoses
            4. Assign confidence scores (0.0-1.0)
            5. Provide key indicators for each diagnosis
            6. List supporting evidence

            Guidelines:
            - Never exceed 95% confidence
            - Consider symptom patterns
            - Account for disease prevalence
            - Provide 2-5 most likely diagnoses
            - Sort by confidence (highest first)
            - Be honest about diagnostic uncertainty

            Output format:
            For each diagnosis, provide:
            - Disease name
            - Confidence score (0.0-1.0)
            - Key indicators (3-5 bullet points)
            - Supporting evidence (2-3 points)
            """,
            add_history_to_context=True,
            markdown=True,
        )

    def generate_diagnoses(
        self,
        symptoms: List[Dict[str, Any]],
        medical_data: Dict[str, Any],
        patient_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate differential diagnoses

        Args:
            symptoms: List of symptoms with details
            medical_data: Medical data from DataAgent
            patient_info: Patient information (age, gender, history)

        Returns:
            List of diagnoses with confidence scores
        """
        logger.info("Generating diagnoses")

        # Prepare context for diagnosis
        symptom_list = [s["name"] for s in symptoms]
        disease_list = [d["name"] for d in medical_data.get("diseases", [])]

        prompt = f"""
        Patient Information:
        - Age: {patient_info.get('age', 'Unknown')}
        - Gender: {patient_info.get('gender', 'Unknown')}
        - Medical History: {', '.join(patient_info.get('medical_history', ['None']))}

        Symptoms:
        {chr(10).join(f'- {s["name"]} (severity: {s.get("severity", "moderate")})' for s in symptoms)}

        Possible Diseases from Knowledge Base:
        {chr(10).join(f'- {d["name"]}' for d in medical_data.get("diseases", []))}

        Based on this information, provide differential diagnoses.
        For each diagnosis, provide:
        1. Disease name
        2. Confidence score (0.0-1.0, max 0.95)
        3. Key indicators (3-5 symptoms that support this diagnosis)
        4. Supporting evidence from the medical data

        Format your response as a structured list.
        """

        # Use agent to generate diagnoses
        run_output = self.run(prompt)

        # Convert RunOutput to string if needed
        if hasattr(run_output, 'content'):
            response = run_output.content
        elif hasattr(run_output, 'message'):
            response = run_output.message
        else:
            response = str(run_output)

        # Parse diagnoses from response
        diagnoses = self._parse_diagnoses(response, disease_list)

        logger.info(f"Generated {len(diagnoses)} diagnoses")

        return diagnoses

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

    def _parse_diagnoses(self, response: str, disease_list: List[str]) -> List[Dict[str, Any]]:
        """
        Parse diagnoses from agent response

        Args:
            response: Agent response text
            disease_list: List of disease names to match

        Returns:
            List of parsed diagnoses
        """
        diagnoses = []

        # Ensure response is a string
        response = self._ensure_string(response)

        # Simple parsing - match disease names in response
        for disease in disease_list:
            if disease.lower() in response.lower():
                # Extract confidence if present
                confidence = 0.65  # Default

                # Try to extract percentage if present
                lines = response.split('\n')
                for line in lines:
                    if disease.lower() in line.lower() and '%' in line:
                        try:
                            # Extract percentage
                            import re
                            match = re.search(r'(\d+(?:\.\d+)?)\s*%', line)
                            if match:
                                confidence = float(match.group(1)) / 100.0
                                confidence = min(confidence, 0.95)  # Cap at 95%
                        except:
                            pass

                diagnosis = {
                    "disease": disease,
                    "confidence_score": confidence,
                    "key_indicators": self._extract_indicators(response, disease),
                    "supporting_evidence": []
                }
                diagnoses.append(diagnosis)

        # Sort by confidence
        diagnoses.sort(key=lambda x: x["confidence_score"], reverse=True)

        return diagnoses[:5]  # Return top 5

    def _extract_indicators(self, response: str, disease: str) -> List[str]:
        """Extract key indicators for a disease from response"""
        # Find lines mentioning the disease and extract indicators
        indicators = []
        lines = response.split('\n')

        for i, line in enumerate(lines):
            if disease.lower() in line.lower():
                # Look for nearby lines with symptoms
                for j in range(max(0, i - 3), min(len(lines), i + 4)):
                    if any(symptom in lines[j].lower() for symptom in
                           ['fever', 'cough', 'headache', 'body ache', 'nausea',
                            'vomiting', 'rash', 'shortness', 'sore throat']):
                        indicator = lines[j].strip().lstrip('- •*')
                        if indicator and len(indicator) > 5:
                            indicators.append(indicator)

        return list(set(indicators))[:5]  # Return unique indicators


# ************* Create Diagnosis Agent *************
diagnosis_agent = DiagnosisAgent()


if __name__ == "__main__":
    # Test the agent
    symptoms = [
        {"name": "fever", "severity": "moderate"},
        {"name": "cough", "severity": "moderate"},
        {"name": "body ache", "severity": "mild"}
    ]
    medical_data = {"diseases": [{"name": "Dengue Fever"}, {"name": "Influenza"}]}
    patient_info = {"age": 35, "gender": "M", "medical_history": []}

    diagnoses = diagnosis_agent.generate_diagnoses(symptoms, medical_data, patient_info)
    print(f"Generated diagnoses: {len(diagnoses)}")
