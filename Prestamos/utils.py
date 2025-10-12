from datetime import date
from dateutil.relativedelta import relativedelta 

def add_months(base_date: date, months: int) -> date:
    """Suma meses a una fecha respetando fin de mes."""
    return base_date + relativedelta(months=+months)
