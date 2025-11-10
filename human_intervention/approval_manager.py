"""
Approval Manager for handling assessment approvals and rejections
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ApprovalManager:
    """
    Manages approval workflow for healthcare assessments
    """

    def __init__(self):
        """Initialize Approval Manager"""
        self.approvals: Dict[str, Dict[str, Any]] = {}
        self.approval_counter = 0
        self.approval_chain = ["physician", "supervisor", "director"]

    def create_approval_request(
        self,
        assessment_id: str,
        assessment_data: Dict[str, Any],
        required_level: str = "physician"
    ) -> str:
        """
        Create an approval request

        Args:
            assessment_id: Assessment ID
            assessment_data: Assessment data requiring approval
            required_level: Required approval level

        Returns:
            Approval request ID
        """
        self.approval_counter += 1
        approval_id = f"APR-{self.approval_counter:06d}"

        approval = {
            "id": approval_id,
            "assessment_id": assessment_id,
            "assessment_data": assessment_data,
            "required_level": required_level,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "approvals": [],
            "rejections": [],
            "final_decision": None,
            "final_decision_at": None,
        }

        self.approvals[approval_id] = approval
        logger.info(f"Created approval request {approval_id} at level {required_level}")
        return approval_id

    def approve_at_level(
        self,
        approval_id: str,
        level: str,
        approver_name: str,
        notes: str = ""
    ) -> bool:
        """
        Approve assessment at a specific level

        Args:
            approval_id: Approval request ID
            level: Approval level (physician, supervisor, director)
            approver_name: Name of approver
            notes: Approval notes

        Returns:
            Success status
        """
        if approval_id not in self.approvals:
            logger.warning(f"Approval {approval_id} not found")
            return False

        approval = self.approvals[approval_id]

        approval["approvals"].append({
            "level": level,
            "approver": approver_name,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        })

        # Update status if all levels are approved
        if self._check_all_approvals(approval_id):
            approval["status"] = "fully_approved"
            approval["final_decision"] = "approved"
            approval["final_decision_at"] = datetime.now().isoformat()
            logger.info(f"Approval {approval_id} fully approved")
        else:
            approval["status"] = "partially_approved"

        logger.info(f"Assessment approved at level {level} by {approver_name}")
        return True

    def reject_at_level(
        self,
        approval_id: str,
        level: str,
        rejector_name: str,
        reason: str
    ) -> bool:
        """
        Reject assessment at a specific level

        Args:
            approval_id: Approval request ID
            level: Rejection level
            rejector_name: Name of rejector
            reason: Rejection reason

        Returns:
            Success status
        """
        if approval_id not in self.approvals:
            return False

        approval = self.approvals[approval_id]

        approval["rejections"].append({
            "level": level,
            "rejector": rejector_name,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

        approval["status"] = "rejected"
        approval["final_decision"] = "rejected"
        approval["final_decision_at"] = datetime.now().isoformat()

        logger.info(f"Assessment rejected at level {level} by {rejector_name}: {reason}")
        return True

    def _check_all_approvals(self, approval_id: str) -> bool:
        """
        Check if all required approval levels have approved

        Args:
            approval_id: Approval request ID

        Returns:
            True if all levels approved, False otherwise
        """
        approval = self.approvals[approval_id]
        required_level = approval["required_level"]

        # Get index of required level
        required_index = self.approval_chain.index(required_level) if required_level in self.approval_chain else 0

        # Check if all levels up to required_level have approved
        approved_levels = {a["level"] for a in approval["approvals"]}

        for i in range(required_index + 1):
            if i < len(self.approval_chain) and self.approval_chain[i] not in approved_levels:
                return False

        return True

    def can_proceed(self, approval_id: str) -> bool:
        """
        Check if assessment can proceed based on approval status

        Args:
            approval_id: Approval request ID

        Returns:
            True if assessment is fully approved, False otherwise
        """
        if approval_id not in self.approvals:
            return False

        approval = self.approvals[approval_id]
        return approval["status"] == "fully_approved" and approval["final_decision"] == "approved"

    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """
        Get approval details

        Args:
            approval_id: Approval request ID

        Returns:
            Approval details or None
        """
        return self.approvals.get(approval_id)

    def get_pending_approvals(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all pending approvals

        Args:
            level: Optional filter by approval level

        Returns:
            List of pending approvals
        """
        pending = []
        for approval in self.approvals.values():
            if approval["status"] in ["pending", "partially_approved"]:
                if level is None or level in {a["level"] for a in approval["approvals"]}:
                    pending.append(approval)
        return pending

    def get_approval_status(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """
        Get approval status summary

        Args:
            approval_id: Approval request ID

        Returns:
            Approval status summary or None
        """
        approval = self.get_approval(approval_id)
        if not approval:
            return None

        return {
            "approval_id": approval_id,
            "status": approval["status"],
            "final_decision": approval["final_decision"],
            "approvals_count": len(approval["approvals"]),
            "rejections_count": len(approval["rejections"]),
            "approved_by": [a["approver"] for a in approval["approvals"]],
            "rejected_by": [r["rejector"] for r in approval["rejections"]],
            "created_at": approval["created_at"],
            "final_decision_at": approval["final_decision_at"]
        }

    def get_approval_history(self, approval_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get full approval history

        Args:
            approval_id: Approval request ID

        Returns:
            Approval history timeline or None
        """
        approval = self.get_approval(approval_id)
        if not approval:
            return None

        history = []

        # Add approvals
        for app in approval["approvals"]:
            history.append({
                "action": "approved",
                "level": app["level"],
                "actor": app["approver"],
                "notes": app["notes"],
                "timestamp": app["timestamp"]
            })

        # Add rejections
        for rej in approval["rejections"]:
            history.append({
                "action": "rejected",
                "level": rej["level"],
                "actor": rej["rejector"],
                "reason": rej["reason"],
                "timestamp": rej["timestamp"]
            })

        # Sort by timestamp
        history.sort(key=lambda x: x["timestamp"])
        return history
