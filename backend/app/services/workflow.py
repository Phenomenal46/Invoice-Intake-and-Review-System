from app.schemas.document import LLMOutput, ValidationResult, WorkflowStatus


def decide_status(validation: ValidationResult, llm: LLMOutput) -> WorkflowStatus:
    if not validation.is_valid:
        return WorkflowStatus.needs_review

    if llm.confidence >= 0.75:
        return WorkflowStatus.approved

    return WorkflowStatus.needs_review
