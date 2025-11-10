"""
Orchestrator Agent - Agno Framework Implementation
Coordinates all healthcare agents
"""
import logging
from typing import List, Dict, Any
from agno.agent import Agent
from agno.models.google.gemini import Gemini
from agno.db.sqlite import SqliteDb
from config import settings

logger = logging.getLogger(__name__)


class OrchestratorAgent(Agent):
    """Agno-based Orchestrator Agent that coordinates all medical agents"""

    def __init__(self):
        """Initialize Orchestrator Agent with Gemini model and SQLite database"""

        super().__init__(
            name="OrchestratorAgent",
            model=Gemini(
                id=settings.AGENT_MODEL,
                api_key=settings.GEMINI_API_KEY
            ),
            db=SqliteDb(db_file=settings.DB_FILE),
            instructions="""You are the Healthcare Orchestrator Agent.
            Your responsibilities are:
            1. Receive patient information and symptoms
            2. Coordinate with other specialized agents
            3. Manage the workflow of medical assessment
            4. Integrate results from all agents
            5. Generate comprehensive medical summary
            6. Ensure consistency across all assessments

            You coordinate with:
            - DataAgent: Retrieves medical information
            - DiagnosisAgent: Generates diagnoses
            - ReasoningAgent: Validates diagnoses
            - TreatmentAgent: Recommends treatments
            - EvaluationAgent: Assesses quality

            Your goal is to produce a comprehensive, safe, and
            evidence-based medical assessment.
            """,
            add_history_to_context=True,
            markdown=True,
        )

    def initialize_workflow(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize healthcare assessment workflow

        Args:
            patient_data: Patient information

        Returns:
            Workflow state dictionary
        """
        # Extract patient name from nested structure if present
        patient_name = patient_data.get("name")
        if not patient_name and isinstance(patient_data.get("patient"), dict):
            patient_name = patient_data.get("patient", {}).get("name", "Unknown")

        logger.info(f"Initializing workflow for patient: {patient_name or 'Unknown'}")

        workflow_state = {
            "patient": patient_data,
            "symptoms": patient_data.get("symptoms", []),
            "medical_data": None,
            "diagnoses": None,
            "reasoning": None,
            "treatments": None,
            "evaluation": None,
            "final_summary": None,
            "status": "initialized"
        }

        return workflow_state

    def coordinate_assessment(
        self,
        workflow_state: Dict[str, Any],
        agents: Dict[str, Agent]
    ) -> Dict[str, Any]:
        """
        Coordinate the full assessment workflow

        Args:
            workflow_state: Current workflow state
            agents: Dictionary of available agents

        Returns:
            Updated workflow state with results
        """
        logger.info("Starting coordinated healthcare assessment")

        try:
            # Step 1: Data Retrieval
            logger.info("Step 1: Retrieving medical data")
            data_agent = agents.get("data_agent")
            if data_agent:
                medical_data = data_agent.fetch_medical_data(
                    [s["name"] for s in workflow_state["symptoms"]]
                )
                workflow_state["medical_data"] = medical_data

            # Step 2: Diagnosis Generation
            logger.info("Step 2: Generating diagnoses")
            diagnosis_agent = agents.get("diagnosis_agent")
            if diagnosis_agent:
                diagnoses = diagnosis_agent.generate_diagnoses(
                    workflow_state["symptoms"],
                    workflow_state["medical_data"],
                    workflow_state["patient"]
                )
                workflow_state["diagnoses"] = diagnoses

            # Step 3: Reasoning & Validation
            logger.info("Step 3: Applying medical reasoning")
            reasoning_agent = agents.get("reasoning_agent")
            if reasoning_agent:
                reasoning = reasoning_agent.validate_diagnoses(
                    workflow_state["diagnoses"],
                    workflow_state["symptoms"]
                )
                workflow_state["reasoning"] = reasoning

            # Step 4: Treatment Recommendations
            logger.info("Step 4: Recommending treatments")
            treatment_agent = agents.get("treatment_agent")
            if treatment_agent:
                treatments = treatment_agent.recommend_treatments(
                    workflow_state["diagnoses"],
                    workflow_state["patient"]
                )
                workflow_state["treatments"] = treatments

            # Step 5: Quality Evaluation
            logger.info("Step 5: Evaluating assessment quality")
            evaluation_agent = agents.get("evaluation_agent")
            if evaluation_agent:
                evaluation = evaluation_agent.evaluate_assessment(
                    workflow_state
                )
                workflow_state["evaluation"] = evaluation

            # Step 6: Final Summary
            logger.info("Step 6: Creating final summary")
            try:
                final_summary = self._create_final_summary(workflow_state)
                if final_summary:
                    workflow_state["final_summary"] = final_summary
                    logger.info("Final summary created successfully")
                else:
                    logger.warning("Final summary is None/empty, creating minimal summary")
                    workflow_state["final_summary"] = {
                        "patient_name": None,
                        "assessment_date": None,
                        "quality_score": 0.0,
                        "probable_diagnoses": workflow_state.get("diagnoses", []),
                        "treatments": workflow_state.get("treatments", []),
                        "symptoms_analyzed": [s["name"] for s in workflow_state.get("symptoms", [])],
                        "diagnostic_tests": [],
                        "next_steps": [],
                        "safety_warnings": []
                    }
            except Exception as summary_error:
                logger.error(f"Error creating final summary: {str(summary_error)}")
                workflow_state["final_summary"] = {
                    "patient_name": None,
                    "assessment_date": None,
                    "quality_score": 0.0,
                    "probable_diagnoses": workflow_state.get("diagnoses", []),
                    "treatments": workflow_state.get("treatments", []),
                    "symptoms_analyzed": [s["name"] for s in workflow_state.get("symptoms", [])],
                    "error": str(summary_error)
                }

            workflow_state["status"] = "completed"

        except Exception as e:
            logger.error(f"Error in workflow: {str(e)}")
            workflow_state["status"] = "error"
            workflow_state["error"] = str(e)

        return workflow_state

    def _create_final_summary(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create final medical assessment summary

        Args:
            workflow_state: Complete workflow state

        Returns:
            Final summary dictionary
        """
        from datetime import datetime

        diagnoses = workflow_state.get("diagnoses", [])

        # Extract patient info from nested structure
        patient_data = workflow_state.get("patient", {})
        if isinstance(patient_data, dict) and "patient" in patient_data:
            patient_info = patient_data["patient"]
        else:
            patient_info = patient_data

        summary = {
            "patient_name": patient_info.get("name") if isinstance(patient_info, dict) else None,
            "assessment_date": datetime.now().isoformat(),
            "symptoms_analyzed": [s["name"] for s in workflow_state["symptoms"]],
            "probable_diagnoses": diagnoses[:3] if diagnoses else [],
            "treatments": workflow_state.get("treatments", []),
            "diagnostic_tests": self._extract_tests(workflow_state),
            "next_steps": self._generate_next_steps(diagnoses),
            "safety_warnings": self._extract_warnings(workflow_state),
            "quality_score": workflow_state.get("evaluation", {}).get("quality_score", 0.0),
        }

        return summary

    def _extract_tests(self, workflow_state: Dict[str, Any]) -> List[str]:
        """Extract diagnostic tests from workflow"""
        tests = []
        diagnoses = workflow_state.get("diagnoses", [])

        # In a real system, would look up tests from knowledge base
        for diagnosis in diagnoses[:2]:
            if diagnosis.get("disease"):
                # Would query knowledge base for tests
                tests.append(f"Test for {diagnosis['disease']}")

        return tests

    def _generate_next_steps(self, diagnoses: List[Dict]) -> List[str]:
        """Generate next steps based on diagnoses"""
        steps = []

        if diagnoses:
            top_diagnosis = diagnoses[0]
            steps.append(f"Confirm diagnosis: {top_diagnosis.get('disease')}")
            steps.append("Complete recommended diagnostic tests")
            steps.append("Schedule follow-up consultation")
            steps.append("Monitor symptoms")

        return steps

    def _extract_warnings(self, workflow_state: Dict[str, Any]) -> List[str]:
        """Extract safety warnings"""
        warnings = []

        patient_data = workflow_state.get("patient", {})

        # Extract patient info from nested structure if present
        if isinstance(patient_data, dict) and "patient" in patient_data:
            patient = patient_data["patient"]
        else:
            patient = patient_data

        if patient.get("allergies"):
            allergies = patient.get('allergies', [])
            if isinstance(allergies, list):
                warnings.append(f"Allergies: {', '.join(allergies)}")
            else:
                warnings.append(f"Allergies: {allergies}")

        if patient.get("medical_history"):
            history = patient.get('medical_history', [])
            if isinstance(history, list):
                warnings.append(f"Medical history: {', '.join(history)}")
            else:
                warnings.append(f"Medical history: {history}")

        return warnings


# ************* Create Orchestrator Agent (Lazy Loading) *************
_orchestrator_agent = None

def get_orchestrator_agent():
    """Get or create the orchestrator agent"""
    global _orchestrator_agent
    if _orchestrator_agent is None:
        _orchestrator_agent = OrchestratorAgent()
    return _orchestrator_agent

# For backwards compatibility, create a module-level instance
try:
    orchestrator_agent = OrchestratorAgent()
except Exception as e:
    logger.warning(f"Failed to initialize orchestrator agent at import: {e}")
    orchestrator_agent = None


if __name__ == "__main__":
    # Test the agent
    patient = {
        "name": "John Doe",
        "age": 35,
        "gender": "M",
        "allergies": ["Penicillin"],
        "medical_history": ["Hypertension"],
        "symptoms": [
            {"name": "fever", "severity": "moderate"},
            {"name": "cough", "severity": "moderate"}
        ]
    }

    workflow = orchestrator_agent.initialize_workflow(patient)
    print(f"Workflow initialized for: {workflow['patient']['name']}")
