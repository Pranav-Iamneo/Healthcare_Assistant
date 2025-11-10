"""
Review Handler for managing assessment reviews
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ReviewHandler:
    """
    Handles the review process for healthcare assessments
    """

    def __init__(self):
        """Initialize Review Handler"""
        self.reviews: Dict[str, Dict[str, Any]] = {}
        self.review_counter = 0

    def create_review(
        self,
        intervention_id: str,
        assessment_data: Dict[str, Any],
        reviewer_name: str
    ) -> str:
        """
        Create a new review for an assessment

        Args:
            intervention_id: Associated intervention ID
            assessment_data: Assessment data to review
            reviewer_name: Name of the reviewer

        Returns:
            Review ID
        """
        self.review_counter += 1
        review_id = f"REV-{self.review_counter:06d}"

        review = {
            "id": review_id,
            "intervention_id": intervention_id,
            "reviewer": reviewer_name,
            "created_at": datetime.now().isoformat(),
            "assessment_data": assessment_data,
            "findings": [],
            "questions": [],
            "recommendations": [],
            "status": "in_progress",
            "completed_at": None,
        }

        self.reviews[review_id] = review
        logger.info(f"Created review {review_id}")
        return review_id

    def add_finding(self, review_id: str, finding: str, severity: str = "normal") -> bool:
        """
        Add a finding to the review

        Args:
            review_id: Review ID
            finding: Finding text
            severity: Severity level (low, normal, high, critical)

        Returns:
            Success status
        """
        if review_id not in self.reviews:
            return False

        self.reviews[review_id]["findings"].append({
            "text": finding,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Added finding to review {review_id}")
        return True

    def add_question(self, review_id: str, question: str, field: str = "") -> bool:
        """
        Add a question to the review

        Args:
            review_id: Review ID
            question: Question text
            field: Related assessment field

        Returns:
            Success status
        """
        if review_id not in self.reviews:
            return False

        self.reviews[review_id]["questions"].append({
            "text": question,
            "field": field,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Added question to review {review_id}")
        return True

    def add_recommendation(self, review_id: str, recommendation: str, action_type: str = "follow_up") -> bool:
        """
        Add a recommendation to the review

        Args:
            review_id: Review ID
            recommendation: Recommendation text
            action_type: Type of action (follow_up, test, specialist, override, etc.)

        Returns:
            Success status
        """
        if review_id not in self.reviews:
            return False

        self.reviews[review_id]["recommendations"].append({
            "text": recommendation,
            "action_type": action_type,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Added recommendation to review {review_id}")
        return True

    def complete_review(self, review_id: str) -> bool:
        """
        Mark review as completed

        Args:
            review_id: Review ID

        Returns:
            Success status
        """
        if review_id not in self.reviews:
            return False

        self.reviews[review_id]["status"] = "completed"
        self.reviews[review_id]["completed_at"] = datetime.now().isoformat()
        logger.info(f"Completed review {review_id}")
        return True

    def get_review(self, review_id: str) -> Optional[Dict[str, Any]]:
        """
        Get review details

        Args:
            review_id: Review ID

        Returns:
            Review details or None
        """
        return self.reviews.get(review_id)

    def get_review_summary(self, review_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary of review findings

        Args:
            review_id: Review ID

        Returns:
            Review summary or None
        """
        review = self.get_review(review_id)
        if not review:
            return None

        return {
            "review_id": review_id,
            "reviewer": review["reviewer"],
            "status": review["status"],
            "total_findings": len(review["findings"]),
            "critical_findings": sum(1 for f in review["findings"] if f["severity"] == "critical"),
            "high_findings": sum(1 for f in review["findings"] if f["severity"] == "high"),
            "total_questions": len(review["questions"]),
            "total_recommendations": len(review["recommendations"]),
            "completed_at": review["completed_at"]
        }
