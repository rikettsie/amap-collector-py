ALLOWED_DEPTS: list[str] = ["27", "76"]

class HnValidationError(RuntimeError):
    pass

def validate_department(department: int|str) -> str:
    dept = str(department)
    if dept not in ALLOWED_DEPTS:
        raise HnValidationError(f"Parameter `department` must belong to {ALLOWED_DEPTS}, but {dept} was given")
    return dept
