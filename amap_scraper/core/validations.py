from amap_scraper.core.endpoint import ZipCodeInfo

ALLOWED_DEPTS: list[str] = ["75", "77", "78", "91", "92", "93", "94", "95"]
ALLOWED_RADII: list[str] = ["2", "5", "10", "15", "20"]

DEFAULT_DEPT: str = "75"
DEFAULT_RADIUS: str = "2"

class ValidationError(RuntimeError):
    pass

def validate_department(department: int|str) -> str:
    dept = str(department)
    if dept not in ALLOWED_DEPTS:
        raise ValidationError(f"Parameter `department` must belong to {ALLOWED_DEPTS}, but {dept} was given")
    return dept
    
def validate_km_radius(km_radius: int|str) -> str:
    km_r = str(km_radius)
    if km_r not in ALLOWED_RADII:
        raise ValidationError(f"Parameter `km_radius` must belong to {ALLOWED_RADII}, but {km_r} was given")
    return km_r

def validate_zip_code(zip_code: int|str) -> str:
    try:
        zc = str(int(zip_code))
        zc_info = ZipCodeInfo().call(zc)
        zc = zc_info.get("code")
        if not zc:
            raise ValueError
        return zc
    except ValueError:
        raise ValidationError(f"Parameter `zip_code` must be represented by a valid french zip code number, but {zip_code} was given")

def validate_coordinates(
    latitude: float|str,
    longitude: float|str
) -> tuple[str, str]:
    try:
        lat = float(latitude)
        lng = float(longitude)

        if lat > 90.0 or lat < -90.0:
            raise ValueError
        if lng > 180.0 or lng < -180.0:
            raise ValueError
        
        return (f"{lat:.7f}", f"{lng:.7f}")
    except ValueError:
        raise ValidationError(f"Parameters `latitude` and `longitude` must be represent valid geo positional floating point numbers, but ({longitude}, {latitude}) were given")

