"""
Agno Healthcare Agents Module
Smart Healthcare Assistant Multi-Agent System
"""
# Lazy imports to avoid circular import issues
__all__ = [
    "OrchestratorAgent",
    "DataAgent",
    "DiagnosisAgent",
    "ReasoningAgent",
    "TreatmentAgent",
    "EvaluationAgent",
    "orchestrator_agent",
    "data_agent",
    "diagnosis_agent",
    "reasoning_agent",
    "treatment_agent",
    "evaluation_agent",
]

def __getattr__(name):
    """Lazy load agents on demand"""
    if name == "OrchestratorAgent" or name == "orchestrator_agent":
        from agents.agno_orchestrator import OrchestratorAgent, orchestrator_agent
        return OrchestratorAgent if name == "OrchestratorAgent" else orchestrator_agent
    elif name == "DataAgent" or name == "data_agent":
        from agents.agno_data_agent import DataAgent, data_agent
        return DataAgent if name == "DataAgent" else data_agent
    elif name == "DiagnosisAgent" or name == "diagnosis_agent":
        from agents.agno_diagnosis_agent import DiagnosisAgent, diagnosis_agent
        return DiagnosisAgent if name == "DiagnosisAgent" else diagnosis_agent
    elif name == "ReasoningAgent" or name == "reasoning_agent":
        from agents.agno_reasoning_agent import ReasoningAgent, reasoning_agent
        return ReasoningAgent if name == "ReasoningAgent" else reasoning_agent
    elif name == "TreatmentAgent" or name == "treatment_agent":
        from agents.agno_treatment_agent import TreatmentAgent, treatment_agent
        return TreatmentAgent if name == "TreatmentAgent" else treatment_agent
    elif name == "EvaluationAgent" or name == "evaluation_agent":
        from agents.agno_evaluation_agent import EvaluationAgent, evaluation_agent
        return EvaluationAgent if name == "EvaluationAgent" else evaluation_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
