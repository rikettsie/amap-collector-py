ALLOWED_DEPTS: list[str] = ["44"]


class Ia44ValidationError(RuntimeError):
    pass


def validate_department(department: int | str) -> str:
    dept = str(department)
    if dept not in ALLOWED_DEPTS:
        raise Ia44ValidationError(
            f"Parameter `department` must belong to {ALLOWED_DEPTS}, but {dept} was given"
        )
    return dept
