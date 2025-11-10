"""
Validation utilities for patient data and symptoms
"""

from typing import Dict, List, Any, Tuple


def validate_patient_data(patient_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate patient information

    Args:
        patient_data: Patient information dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not patient_data:
        return False, "Patient data is required"

    # Extract patient info from nested structure if present
    if isinstance(patient_data.get("patient"), dict):
        patient_info = patient_data["patient"]
    else:
        patient_info = patient_data

    # Validate required fields
    if not patient_info.get("name"):
        return False, "Patient name is required"

    if not patient_info.get("age"):
        return False, "Patient age is required"

    try:
        age = int(patient_info.get("age", 0))
        if age < 0 or age > 150:
            return False, "Patient age must be between 0 and 150"
    except (ValueError, TypeError):
        return False, "Patient age must be a valid number"

    if not patient_info.get("gender"):
        return False, "Patient gender is required"

    valid_genders = ["Male", "Female", "Other", "M", "F"]
    if patient_info.get("gender") not in valid_genders:
        return False, f"Patient gender must be one of: {', '.join(valid_genders)}"

    return True, ""


def validate_symptoms(symptoms: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Validate patient symptoms

    Args:
        symptoms: List of symptom dictionaries

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not symptoms:
        return False, "At least one symptom is required"

    if not isinstance(symptoms, list):
        return False, "Symptoms must be a list"

    for idx, symptom in enumerate(symptoms):
        if not isinstance(symptom, dict):
            return False, f"Symptom {idx + 1} must be a dictionary"

        if not symptom.get("name"):
            return False, f"Symptom {idx + 1} name is required"

        severity = symptom.get("severity", "moderate")
        valid_severities = ["mild", "moderate", "severe"]
        if severity.lower() not in valid_severities:
            return False, f"Symptom {idx + 1} severity must be one of: {', '.join(valid_severities)}"

        try:
            duration = int(symptom.get("duration_days", 0))
            if duration < 0:
                return False, f"Symptom {idx + 1} duration must be non-negative"
        except (ValueError, TypeError):
            return False, f"Symptom {idx + 1} duration must be a valid number"

    return True, ""


def validate_assessment_input(patient_data: Dict[str, Any], symptoms: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Validate complete assessment input

    Args:
        patient_data: Patient information
        symptoms: List of symptoms

    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, error = validate_patient_data(patient_data)
    if not is_valid:
        return False, error

    is_valid, error = validate_symptoms(symptoms)
    if not is_valid:
        return False, error

    return True, ""
