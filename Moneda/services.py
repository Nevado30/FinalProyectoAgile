from datetime import date
from decimal import Decimal
import requests
from django.db import transaction
from .models import TipoCambio

EXCHANGERATE_HOST = "https://api.exchangerate.host/latest"   
FRANKFURTER = "https://api.frankfurter.app/latest"           
OPEN_ERAPI = "https://open.er-api.com/v6/latest"             

def _fetch_exchangerate_host(base: str, destino: str):
    try:
        r = requests.get(EXCHANGERATE_HOST, params={"base": base, "symbols": destino}, timeout=8)
        r.raise_for_status()
        data = r.json()
        rate = data.get("rates", {}).get(destino)
        return Decimal(str(rate)) if rate is not None else None
    except Exception:
        return None

def _fetch_frankfurter(base: str, destino: str):
    try:
        r = requests.get(FRANKFURTER, params={"from": base, "to": destino}, timeout=8)
        r.raise_for_status()
        data = r.json()
        rate = data.get("rates", {}).get(destino)
        return Decimal(str(rate)) if rate is not None else None
    except Exception:
        return None

def _fetch_open_erapi(base: str, destino: str):
    try:
        # esta API devuelve todas las tasas desde "base"
        r = requests.get(f"{OPEN_ERAPI}/{base}", timeout=8)
        r.raise_for_status()
        data = r.json()
        rate = data.get("rates", {}).get(destino)
        return Decimal(str(rate)) if rate is not None else None
    except Exception:
        return None

def _fetch_remote_rate(base: str, destino: str) -> Decimal:
    # intenta varios proveedores en cadena
    for provider in (_fetch_exchangerate_host, _fetch_frankfurter, _fetch_open_erapi):
        rate = provider(base, destino)
        if rate is not None:
            return rate
    raise ValueError(f"No se obtuvo tasa {base}->{destino} de los proveedores públicos")

def obtener_tipo_cambio(base: str = "USD", destino: str = "PEN", para_fecha: date | None = None) -> Decimal:
    if para_fecha is None:
        para_fecha = date.today()
    base = base.upper(); destino = destino.upper()

    try:
        tc = TipoCambio.objects.get(fecha=para_fecha, base=base, destino=destino)
        return tc.valor
    except TipoCambio.DoesNotExist:
        valor = _fetch_remote_rate(base, destino)
        with transaction.atomic():
            tc, _ = TipoCambio.objects.get_or_create(
                fecha=para_fecha, base=base, destino=destino,
                defaults={"valor": valor}
            )
        return tc.valor
