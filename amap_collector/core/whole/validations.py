from amap_collector.core.idf.validations import ALLOWED_DEPTS as IDF_DEPTS
from amap_collector.core.hn.validations import ALLOWED_DEPTS as HN_DEPTS
from amap_collector.core.ia44.validations import ALLOWED_DEPTS as IA44_DEPTS

_EXCLUDED: frozenset[str] = frozenset(IDF_DEPTS + HN_DEPTS + IA44_DEPTS)


def _build_allowed_depts() -> list[str]:
    result: list[str] = []
    for dept in ["2A", "2B"]:
        if dept not in _EXCLUDED:
            result.append(dept)
    for i in range(1, 96):
        s = str(i)
        if s == "2":
            continue
        s = f"0{s}" if len(s) == 1 else s
        if s not in _EXCLUDED:
            result.append(s)
    return result


ALLOWED_DEPTS: list[str] = _build_allowed_depts()


class WholeValidationError(RuntimeError):
    pass


def validate_department(department: int | str) -> str:
    dept = str(department)
    if dept not in ALLOWED_DEPTS:
        raise WholeValidationError(
            f"Parameter `department` must belong to {ALLOWED_DEPTS}, but {dept} was given"
        )
    return dept
