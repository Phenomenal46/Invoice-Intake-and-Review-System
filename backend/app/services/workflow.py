from app.schemas.document import LLMOutput, ValidationResult, WorkflowStatus


def decide_status(validation: ValidationResult, llm: LLMOutput) -> WorkflowStatus:
    """
    The 'Brain' of the project. It looks at the results from the validator 
    and the AI to decide if the document is 'Approved' or needs a human to check it ('Needs Review').
    """
    
    # Rule 1: If any required data is missing from the document, it's not ready yet.
    if not validation.is_valid:
        return WorkflowStatus.needs_review

    # Rule 2: If the AI (Gemini) says it is less than 75% confident, we play it safe and ask for a review.
    # 0.75 is a float (decimal number).
    if llm.confidence >= 0.75:
        return WorkflowStatus.approved

    # Default Choice: If it didn't pass the rules above, it goes to review.
    return WorkflowStatus.needs_review
