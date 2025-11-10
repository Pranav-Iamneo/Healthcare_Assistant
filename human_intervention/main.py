"""
Main Human Intervention Manager
Orchestrates human review and approval workflows for healthcare assessments
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class InterventionType(str, Enum):
    """Types of human intervention required"""
    REVIEW = "review"  # Assessment needs review
    APPROVAL = "approval"  # Assessment needs approval
    CLARIFICATION = "clarification"  # Need more information
    OVERRIDE = "override"  # Need to override AI decision
    URGENT = "urgent"  # Urgent case requiring immediate attention


class InterventionStatus(str, Enum):
    """Status of intervention request"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class HumanInterventionManager:
    """
    Manages human intervention workflows for healthcare assessments

    This class handles:
    - Identifying assessments that need human review
    - Creating intervention requests
    - Tracking intervention status
    - Managing approvals and rejections
    - Escalating urgent cases
    """

    def __init__(self):
        """Initialize Human Intervention Manager"""
        self.interventions: Dict[str, Dict[str, Any]] = {}
        self.intervention_counter = 0
        logger.info("Human Intervention Manager initialized")

    def create_intervention_request(
        self,
        assessment_id: str,
        intervention_type: InterventionType,
        assessment_data: Dict[str, Any],
        reason: str,
        priority: str = "normal"
    ) -> str:
        """
        Create a new human intervention request

        Args:
            assessment_id: ID of the assessment needing intervention
            intervention_type: Type of intervention required
            assessment_data: Complete assessment data
            reason: Reason for intervention
            priority: Priority level (low, normal, high, urgent)

        Returns:
            Intervention request ID
        """
        self.intervention_counter += 1
        request_id = f"INT-{self.intervention_counter:06d}"

        intervention = {
            "id": request_id,
            "assessment_id": assessment_id,
            "type": intervention_type.value,
            "status": InterventionStatus.PENDING.value,
            "priority": priority,
            "reason": reason,
            "created_at": datetime.now().isoformat(),
            "assessment_data": assessment_data,
            "assigned_to": None,
            "comments": [],
            "decision": None,
            "resolved_at": None,
        }

        self.interventions[request_id] = intervention
        logger.info(f"Created intervention request {request_id}: {intervention_type.value}")

        return request_id

    def flag_high_risk_assessment(
        self,
        assessment_id: str,
        assessment_data: Dict[str, Any],
        risk_factors: List[str]
    ) -> str:
        """
        Flag assessment as high-risk requiring human review

        Args:
            assessment_id: Assessment ID
            assessment_data: Assessment data
            risk_factors: List of risk factors identified

        Returns:
            Intervention request ID
        """
        reason = f"High-risk assessment identified. Risk factors: {', '.join(risk_factors)}"
        return self.create_intervention_request(
            assessment_id=assessment_id,
            intervention_type=InterventionType.REVIEW,
            assessment_data=assessment_data,
            reason=reason,
            priority="high"
        )

    def flag_low_confidence_assessment(
        self,
        assessment_id: str,
        assessment_data: Dict[str, Any],
        confidence_score: float,
        threshold: float = 0.6
    ) -> Optional[str]:
        """
        Flag assessment with low confidence for human review

        Args:
            assessment_id: Assessment ID
            assessment_data: Assessment data
            confidence_score: Confidence score from AI
            threshold: Confidence threshold (below this triggers review)

        Returns:
            Intervention request ID or None if confidence is acceptable
        """
        if confidence_score < threshold:
            reason = f"Low confidence assessment (score: {confidence_score:.1%}, threshold: {threshold:.1%})"
            return self.create_intervention_request(
                assessment_id=assessment_id,
                intervention_type=InterventionType.REVIEW,
                assessment_data=assessment_data,
                reason=reason,
                priority="normal"
            )
        return None

    def flag_contradictory_diagnosis(
        self,
        assessment_id: str,
        assessment_data: Dict[str, Any],
        conflicting_diagnoses: List[str]
    ) -> str:
        """
        Flag assessment with conflicting diagnoses

        Args:
            assessment_id: Assessment ID
            assessment_data: Assessment data
            conflicting_diagnoses: List of conflicting diagnoses

        Returns:
            Intervention request ID
        """
        reason = f"Contradictory diagnoses detected: {', '.join(conflicting_diagnoses)}"
        return self.create_intervention_request(
            assessment_id=assessment_id,
            intervention_type=InterventionType.CLARIFICATION,
            assessment_data=assessment_data,
            reason=reason,
            priority="high"
        )

    def flag_urgent_symptoms(
        self,
        assessment_id: str,
        assessment_data: Dict[str, Any],
        urgent_symptoms: List[str]
    ) -> str:
        """
        Flag assessment with urgent symptoms requiring immediate attention

        Args:
            assessment_id: Assessment ID
            assessment_data: Assessment data
            urgent_symptoms: List of urgent symptoms

        Returns:
            Intervention request ID
        """
        reason = f"Urgent symptoms detected: {', '.join(urgent_symptoms)}. Immediate medical attention required."
        return self.create_intervention_request(
            assessment_id=assessment_id,
            intervention_type=InterventionType.URGENT,
            assessment_data=assessment_data,
            reason=reason,
            priority="urgent"
        )

    def assign_intervention(self, request_id: str, assigned_to: str) -> bool:
        """
        Assign intervention request to a reviewer

        Args:
            request_id: Intervention request ID
            assigned_to: Name/ID of reviewer

        Returns:
            Success status
        """
        if request_id not in self.interventions:
            logger.warning(f"Intervention request {request_id} not found")
            return False

        intervention = self.interventions[request_id]
        intervention["assigned_to"] = assigned_to
        intervention["status"] = InterventionStatus.IN_PROGRESS.value
        logger.info(f"Assigned intervention {request_id} to {assigned_to}")
        return True

    def add_comment(self, request_id: str, comment: str, reviewer: str) -> bool:
        """
        Add comment to intervention request

        Args:
            request_id: Intervention request ID
            comment: Comment text
            reviewer: Reviewer name/ID

        Returns:
            Success status
        """
        if request_id not in self.interventions:
            return False

        self.interventions[request_id]["comments"].append({
            "text": comment,
            "reviewer": reviewer,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Added comment to intervention {request_id}")
        return True

    def approve_assessment(self, request_id: str, reviewer: str, notes: str = "") -> bool:
        """
        Approve assessment after human review

        Args:
            request_id: Intervention request ID
            reviewer: Reviewer name/ID
            notes: Approval notes

        Returns:
            Success status
        """
        if request_id not in self.interventions:
            return False

        intervention = self.interventions[request_id]
        intervention["status"] = InterventionStatus.APPROVED.value
        intervention["decision"] = "approved"
        intervention["resolved_at"] = datetime.now().isoformat()
        if notes:
            self.add_comment(request_id, f"Approval notes: {notes}", reviewer)

        logger.info(f"Approved assessment for intervention {request_id}")
        return True

    def reject_assessment(self, request_id: str, reviewer: str, reason: str) -> bool:
        """
        Reject assessment and request revision

        Args:
            request_id: Intervention request ID
            reviewer: Reviewer name/ID
            reason: Rejection reason

        Returns:
            Success status
        """
        if request_id not in self.interventions:
            return False

        intervention = self.interventions[request_id]
        intervention["status"] = InterventionStatus.REJECTED.value
        intervention["decision"] = "rejected"
        intervention["resolved_at"] = datetime.now().isoformat()
        self.add_comment(request_id, f"Rejection reason: {reason}", reviewer)

        logger.info(f"Rejected assessment for intervention {request_id}")
        return True

    def escalate_intervention(self, request_id: str, escalation_reason: str) -> bool:
        """
        Escalate intervention to higher level

        Args:
            request_id: Intervention request ID
            escalation_reason: Reason for escalation

        Returns:
            Success status
        """
        if request_id not in self.interventions:
            return False

        intervention = self.interventions[request_id]
        intervention["status"] = InterventionStatus.ESCALATED.value
        intervention["priority"] = "urgent"
        self.add_comment(request_id, f"Escalated: {escalation_reason}", "SYSTEM")

        logger.info(f"Escalated intervention {request_id}")
        return True

    def get_intervention(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get intervention request details

        Args:
            request_id: Intervention request ID

        Returns:
            Intervention details or None
        """
        return self.interventions.get(request_id)

    def get_pending_interventions(self, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all pending intervention requests

        Args:
            priority: Optional priority filter

        Returns:
            List of pending interventions
        """
        pending = []
        for intervention in self.interventions.values():
            if intervention["status"] == InterventionStatus.PENDING.value:
                if priority is None or intervention["priority"] == priority:
                    pending.append(intervention)
        return pending

    def get_urgent_interventions(self) -> List[Dict[str, Any]]:
        """
        Get all urgent intervention requests

        Returns:
            List of urgent interventions
        """
        return self.get_pending_interventions(priority="urgent")

    def generate_intervention_report(self) -> Dict[str, Any]:
        """
        Generate report of all interventions

        Returns:
            Intervention statistics and details
        """
        total = len(self.interventions)
        pending = len(self.get_pending_interventions())
        urgent = len(self.get_urgent_interventions())
        approved = sum(1 for i in self.interventions.values() if i["status"] == InterventionStatus.APPROVED.value)
        rejected = sum(1 for i in self.interventions.values() if i["status"] == InterventionStatus.REJECTED.value)

        return {
            "total_interventions": total,
            "pending": pending,
            "urgent": urgent,
            "approved": approved,
            "rejected": rejected,
            "escalated": sum(1 for i in self.interventions.values() if i["status"] == InterventionStatus.ESCALATED.value),
            "interventions": self.interventions
        }


# Global instance
intervention_manager = HumanInterventionManager()


if __name__ == "__main__":
    # Example usage
    manager = HumanInterventionManager()

    # Create intervention request
    assessment_data = {
        "patient_name": "John Doe",
        "diagnosis": "Possible dengue fever",
        "confidence": 0.65
    }

    request_id = manager.flag_low_confidence_assessment(
        assessment_id="ASS-001",
        assessment_data=assessment_data,
        confidence_score=0.65,
        threshold=0.75
    )

    print(f"Created intervention request: {request_id}")

    # Assign to reviewer
    manager.assign_intervention(request_id, "Dr. Smith")

    # Add comments
    manager.add_comment(request_id, "Assessment looks reasonable but need more tests", "Dr. Smith")

    # Approve
    manager.approve_assessment(request_id, "Dr. Smith", "Patient should get TB test")

    # Get details
    intervention = manager.get_intervention(request_id)
    print(f"\nIntervention Details:\n{intervention}")

    # Generate report
    report = manager.generate_intervention_report()
    print(f"\nIntervention Report:\n{report}")
