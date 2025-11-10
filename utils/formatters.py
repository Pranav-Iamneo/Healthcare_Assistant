"""
Formatting utilities for assessment data
"""

from typing import Dict, Any, List


def format_confidence(confidence: float) -> str:
    """
    Format confidence score as percentage

    Args:
        confidence: Confidence score (0.0-1.0)

    Returns:
        Formatted confidence string
    """
    if isinstance(confidence, (int, float)):
        return f"{confidence:.1%}"
    return str(confidence)


def format_diagnosis(diagnosis: Dict[str, Any]) -> str:
    """
    Format diagnosis for display

    Args:
        diagnosis: Diagnosis dictionary

    Returns:
        Formatted diagnosis string
    """
    if isinstance(diagnosis, dict):
        disease = diagnosis.get("disease", "Unknown")
        confidence = diagnosis.get("confidence_score", 0)
        return f"{disease} (Confidence: {format_confidence(confidence)})"
    return str(diagnosis)


def format_treatment(treatment: Dict[str, Any]) -> str:
    """
    Format treatment recommendation for display

    Args:
        treatment: Treatment dictionary

    Returns:
        Formatted treatment string
    """
    if isinstance(treatment, dict):
        t_type = treatment.get("type", "").upper()
        recommendation = treatment.get("recommendation", "N/A")
        justification = treatment.get("justification", "")

        formatted = f"[{t_type}] {recommendation}"
        if justification:
            formatted += f" ({justification})"
        return formatted
    return str(treatment)


def format_date(date_str: str) -> str:
    """
    Format ISO date string to readable format

    Args:
        date_str: ISO format date string

    Returns:
        Formatted date string
    """
    if isinstance(date_str, str) and "T" in date_str:
        return date_str.split("T")[0]
    return str(date_str) if date_str else "N/A"


def format_assessment_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format complete assessment summary for display

    Args:
        summary: Assessment summary dictionary

    Returns:
        Formatted summary dictionary
    """
    formatted = {
        "patient_name": summary.get("patient_name", "Unknown"),
        "assessment_date": format_date(summary.get("assessment_date", "N/A")),
        "quality_score": format_confidence(summary.get("quality_score", 0)),
        "symptoms_analyzed": ", ".join(summary.get("symptoms_analyzed", [])) or "None",
        "num_diagnoses": len(summary.get("probable_diagnoses", [])),
        "num_treatments": len(summary.get("treatments", [])),
        "num_tests": len(summary.get("diagnostic_tests", [])),
    }
    return formatted


def format_diagnoses_list(diagnoses: List[Dict[str, Any]]) -> List[str]:
    """
    Format list of diagnoses

    Args:
        diagnoses: List of diagnosis dictionaries

    Returns:
        List of formatted diagnosis strings
    """
    formatted = []
    for diagnosis in diagnoses:
        formatted.append(format_diagnosis(diagnosis))
    return formatted


def format_treatments_list(treatments: List[Dict[str, Any]]) -> List[str]:
    """
    Format list of treatments

    Args:
        treatments: List of treatment dictionaries

    Returns:
        List of formatted treatment strings
    """
    formatted = []
    for treatment in treatments:
        formatted.append(format_treatment(treatment))
    return formatted


def extract_risk_level(quality_score: float) -> str:
    """
    Derive risk level from quality score

    Args:
        quality_score: Quality score (0.0-1.0)

    Returns:
        Risk level string (LOW, MODERATE, HIGH)
    """
    if quality_score >= 0.75:
        return "LOW"
    elif quality_score >= 0.5:
        return "MODERATE"
    else:
        return "HIGH"
