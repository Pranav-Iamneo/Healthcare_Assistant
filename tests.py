"""
Comprehensive Test Suite for Healthcare Assistant
Tests cover all critical components and functionality
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from agents.agno_orchestrator import orchestrator_agent
from agents.agno_data_agent import data_agent
from agents.agno_diagnosis_agent import diagnosis_agent
from agents.agno_treatment_agent import treatment_agent
from agents.agno_reasoning_agent import reasoning_agent
from agents.agno_evaluation_agent import evaluation_agent


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "name": "Test Patient",
        "age": 35,
        "gender": "Male",
        "allergies": ["Penicillin"],
        "medical_history": ["Hypertension", "Type 2 Diabetes"],
        "medications": ["Aspirin", "Metformin"],
        "symptoms": [
            {"name": "fever", "severity": "moderate", "duration_days": 3},
            {"name": "cough", "severity": "mild", "duration_days": 2}
        ]
    }


@pytest.fixture
def sample_symptoms():
    """Sample symptoms list for testing"""
    return [
        {"name": "fever", "severity": "moderate"},
        {"name": "cough", "severity": "mild"},
        {"name": "body ache", "severity": "moderate"}
    ]


@pytest.fixture
def sample_diagnoses():
    """Sample diagnoses for testing"""
    return [
        {
            "disease": "Dengue Fever",
            "confidence_score": 0.83,
            "key_indicators": ["fever", "body ache"],
            "supporting_evidence": []
        },
        {
            "disease": "Influenza",
            "confidence_score": 0.65,
            "key_indicators": ["fever", "cough"],
            "supporting_evidence": []
        }
    ]


# ============================================================================
# TEST CASES
# ============================================================================

class TestWorkflowInitialization:
    """Test 1: Workflow Initialization"""

    def test_workflow_initialization(self, sample_patient_data):
        """
        Test that workflow initializes correctly with patient data

        Expected: Workflow state should be created with all required fields
        """
        workflow = orchestrator_agent.initialize_workflow(sample_patient_data)

        # Assertions
        assert workflow is not None, "Workflow should not be None"
        assert workflow["status"] == "initialized", "Status should be 'initialized'"
        assert workflow["patient"] == sample_patient_data, "Patient data should match"
        assert len(workflow["symptoms"]) == 2, "Should have 2 symptoms"
        assert workflow["medical_data"] is None, "Medical data should be None initially"
        assert workflow["diagnoses"] is None, "Diagnoses should be None initially"
        assert workflow["final_summary"] is None, "Final summary should be None initially"


class TestDataRetrieval:
    """Test 2: Medical Data Retrieval"""

    def test_medical_data_retrieval(self):
        """
        Test that data agent retrieves medical data correctly

        Expected: Should return medical data dictionary with disease list
        """
        symptoms = ["fever", "cough"]
        medical_data = data_agent.fetch_medical_data(symptoms)

        # Assertions
        assert medical_data is not None, "Medical data should not be None"
        assert isinstance(medical_data, dict), "Medical data should be a dictionary"
        assert "diseases" in medical_data, "Medical data should contain 'diseases' key"
        assert "symptoms_found" in medical_data, "Medical data should contain 'symptoms_found' key"
        assert medical_data["symptoms_found"] == symptoms, "Symptoms should match input"


class TestDiagnosisGeneration:
    """Test 3: Diagnosis Generation"""

    def test_diagnosis_generation(self, sample_symptoms, sample_patient_data):
        """
        Test that diagnosis agent generates diagnoses correctly

        Expected: Should return list of diagnoses with confidence scores
        """
        medical_data = {"diseases": [{"name": "Dengue Fever"}, {"name": "Influenza"}]}

        # Mock the run method to avoid API calls
        with patch.object(diagnosis_agent, 'run') as mock_run:
            mock_run.return_value = Mock(
                content="Dengue Fever (83%) - fever, body ache. Influenza (65%) - fever, cough"
            )

            diagnoses = diagnosis_agent.generate_diagnoses(
                sample_symptoms,
                medical_data,
                sample_patient_data
            )

        # Assertions
        assert diagnoses is not None, "Diagnoses should not be None"
        assert isinstance(diagnoses, list), "Diagnoses should be a list"
        assert len(diagnoses) > 0, "Should generate at least one diagnosis"

        # Check diagnosis structure
        for diagnosis in diagnoses:
            assert "disease" in diagnosis, "Diagnosis should have 'disease' field"
            assert "confidence_score" in diagnosis, "Diagnosis should have 'confidence_score'"
            assert 0 <= diagnosis["confidence_score"] <= 1, "Confidence should be between 0 and 1"


class TestTreatmentRecommendation:
    """Test 4: Treatment Recommendation"""

    def test_treatment_recommendation(self, sample_diagnoses, sample_patient_data):
        """
        Test that treatment agent recommends treatments correctly

        Expected: Should return list of treatment recommendations
        """
        # Mock the run method to avoid API calls
        with patch.object(treatment_agent, 'run') as mock_run:
            mock_run.return_value = Mock(
                content="Medication: Paracetamol 500mg every 6 hours\nTest: Dengue NS1 antigen test\nLifestyle: Complete bed rest"
            )

            treatments = treatment_agent.recommend_treatments(
                sample_diagnoses,
                sample_patient_data
            )

        # Assertions
        assert treatments is not None, "Treatments should not be None"
        assert isinstance(treatments, list), "Treatments should be a list"
        assert len(treatments) > 0, "Should recommend at least one treatment"

        # Check treatment structure
        for treatment in treatments:
            assert "type" in treatment, "Treatment should have 'type' field"
            assert "recommendation" in treatment, "Treatment should have 'recommendation'"
            assert treatment["type"] in ["medication", "test", "lifestyle", "consultation"], \
                f"Treatment type should be valid, got: {treatment['type']}"


class TestDiagnosisValidation:
    """Test 5: Diagnosis Validation"""

    def test_diagnosis_validation(self, sample_diagnoses, sample_symptoms):
        """
        Test that reasoning agent validates diagnoses correctly

        Expected: Should return validation result with reasoning
        """
        # Mock the run method to avoid API calls
        with patch.object(reasoning_agent, 'run') as mock_run:
            mock_run.return_value = Mock(
                content="Dengue Fever is valid with strong symptoms match. Influenza is also possible but less likely."
            )

            validation = reasoning_agent.validate_diagnoses(
                sample_diagnoses,
                sample_symptoms
            )

        # Assertions
        assert validation is not None, "Validation result should not be None"
        assert isinstance(validation, dict), "Validation should be a dictionary"
        assert "status" in validation, "Validation should have 'status' field"
        assert validation["status"] == "validated", "Status should be 'validated'"
        assert "reasoning" in validation, "Validation should have 'reasoning'"


class TestQualityEvaluation:
    """Test 6: Quality Evaluation"""

    def test_quality_evaluation(self, sample_patient_data, sample_symptoms, sample_diagnoses):
        """
        Test that evaluation agent evaluates assessment quality correctly

        Expected: Should return evaluation with quality score and feedback
        """
        workflow_state = {
            "patient": sample_patient_data,
            "symptoms": sample_symptoms,
            "diagnoses": sample_diagnoses,
            "treatments": [{"type": "medication", "recommendation": "Paracetamol"}]
        }

        # Mock the run method to avoid API calls
        with patch.object(evaluation_agent, 'run') as mock_run:
            mock_run.return_value = Mock(
                content="Quality Score: 75/100. Assessment is comprehensive with good symptom-diagnosis match. Strengths: good coverage. Concerns: limited test recommendations."
            )

            evaluation = evaluation_agent.evaluate_assessment(workflow_state)

        # Assertions
        assert evaluation is not None, "Evaluation should not be None"
        assert isinstance(evaluation, dict), "Evaluation should be a dictionary"
        assert "status" in evaluation, "Evaluation should have 'status' field"
        assert "quality_score" in evaluation, "Evaluation should have 'quality_score'"
        assert 0 <= evaluation["quality_score"] <= 1, "Quality score should be between 0 and 1"
        assert "assessment" in evaluation, "Evaluation should have 'assessment'"


class TestFinalSummaryCreation:
    """Test 7: Final Summary Creation"""

    def test_final_summary_creation(self, sample_patient_data):
        """
        Test that orchestrator creates final summary correctly

        Expected: Summary should contain all required fields and never be None
        """
        workflow = orchestrator_agent.initialize_workflow(sample_patient_data)

        # Manually create a workflow state to test summary creation
        workflow["symptoms"] = sample_patient_data["symptoms"]
        workflow["diagnoses"] = [
            {"disease": "Dengue Fever", "confidence_score": 0.83}
        ]
        workflow["treatments"] = [
            {"type": "medication", "recommendation": "Paracetamol"}
        ]
        workflow["evaluation"] = {"quality_score": 0.75}

        # Create final summary
        summary = orchestrator_agent._create_final_summary(workflow)

        # Assertions
        assert summary is not None, "Summary should not be None"
        assert isinstance(summary, dict), "Summary should be a dictionary"
        assert "patient_name" in summary, "Summary should have patient name"
        assert "assessment_date" in summary, "Summary should have assessment date"
        assert "quality_score" in summary, "Summary should have quality score"
        assert "probable_diagnoses" in summary, "Summary should have diagnoses"
        assert "treatments" in summary, "Summary should have treatments"
        assert "symptoms_analyzed" in summary, "Summary should have symptoms"


class TestCompleteWorkflowExecution:
    """Test 8: Complete Workflow Execution"""

    def test_complete_workflow(self, sample_patient_data):
        """
        Test that complete assessment workflow executes successfully

        Expected: Workflow should complete with all stages populated
        """
        # Initialize workflow
        workflow = orchestrator_agent.initialize_workflow(sample_patient_data)

        # Create agents dictionary
        agents = {
            "data_agent": data_agent,
            "diagnosis_agent": diagnosis_agent,
            "reasoning_agent": reasoning_agent,
            "treatment_agent": treatment_agent,
            "evaluation_agent": evaluation_agent
        }

        # Mock all agent run methods to avoid API calls
        with patch.object(diagnosis_agent, 'run') as mock_diagnosis, \
             patch.object(treatment_agent, 'run') as mock_treatment, \
             patch.object(reasoning_agent, 'run') as mock_reasoning, \
             patch.object(evaluation_agent, 'run') as mock_evaluation:

            mock_diagnosis.return_value = Mock(content="Dengue Fever (83%)")
            mock_treatment.return_value = Mock(content="Paracetamol. Test: NS1 antigen")
            mock_reasoning.return_value = Mock(content="Valid diagnosis")
            mock_evaluation.return_value = Mock(content="Quality: 75/100")

            # Run complete assessment
            workflow = orchestrator_agent.coordinate_assessment(workflow, agents)

        # Assertions
        assert workflow is not None, "Workflow should not be None"
        assert workflow["status"] == "completed", "Workflow should be completed"
        assert workflow["medical_data"] is not None, "Medical data should be populated"
        assert workflow["diagnoses"] is not None, "Diagnoses should be populated"
        assert workflow["treatments"] is not None, "Treatments should be populated"
        assert workflow["evaluation"] is not None, "Evaluation should be populated"
        assert workflow["final_summary"] is not None, "Final summary should be populated"


class TestErrorHandling:
    """Test 9: Error Handling and Fallback"""

    def test_empty_diagnoses_handling(self, sample_patient_data):
        """
        Test that system handles empty diagnoses gracefully

        Expected: Should not crash and provide fallback summary
        """
        workflow = orchestrator_agent.initialize_workflow(sample_patient_data)
        workflow["symptoms"] = sample_patient_data["symptoms"]
        workflow["diagnoses"] = []  # Empty diagnoses
        workflow["treatments"] = []
        workflow["evaluation"] = {"quality_score": 0.0}

        # Should not crash
        summary = orchestrator_agent._create_final_summary(workflow)

        # Assertions
        assert summary is not None, "Summary should not be None even with empty diagnoses"
        assert isinstance(summary, dict), "Summary should be a dictionary"
        assert summary["probable_diagnoses"] == [], "Diagnoses should be empty list"


class TestDataValidation:
    """Test 10: Data Validation and Type Safety"""

    def test_runoutput_string_conversion(self):
        """
        Test that RunOutput objects are properly converted to strings

        Expected: All agents should handle RunOutput conversion safely
        """
        # Test with simple symptoms
        symptoms = ["fever"]

        # Test diagnosis agent's ensure_string method
        medical_data = data_agent.fetch_medical_data(symptoms)
        assert isinstance(medical_data, dict), "Medical data should be dict"

        # Test that diagnosis agent can parse responses with mocked run
        patient_info = {"age": 35, "gender": "Male", "medical_history": []}
        test_symptoms = [{"name": "fever", "severity": "moderate"}]

        with patch.object(diagnosis_agent, 'run') as mock_run:
            mock_run.return_value = Mock(content="Dengue Fever (70%)")
            diagnoses = diagnosis_agent.generate_diagnoses(
                test_symptoms,
                medical_data,
                patient_info
            )

        # Assertions
        assert diagnoses is not None, "Diagnoses should not be None"
        assert isinstance(diagnoses, list), "Diagnoses should be a list"

        # Verify all diagnoses have proper types
        for diagnosis in diagnoses:
            assert isinstance(diagnosis.get("disease"), str), "Disease should be string"
            assert isinstance(diagnosis.get("confidence_score"), (int, float)), \
                "Confidence score should be numeric"


# ============================================================================
# TEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Run all tests with pytest

    Commands:
    - Run all tests: pytest tests.py -v
    - Run specific test: pytest tests.py::TestWorkflowInitialization -v
    - Run with coverage: pytest tests.py --cov=agents --cov=config
    - Run with detailed output: pytest tests.py -vv -s
    """
    pytest.main([__file__, "-v", "--tb=short"])
