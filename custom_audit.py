from inspect_ai import Task, task
from inspect_petri import (
    audit,
    audit_judge,
    judge_dimensions,
)


@task
def combined_audit() -> Task:
    dimensions = (
        judge_dimensions()
        + judge_dimensions("./my_dimensions")
    )

    task = audit(
        judge_dimensions=dimensions,
    )

    return task