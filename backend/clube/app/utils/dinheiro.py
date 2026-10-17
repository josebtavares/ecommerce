"""
Dinheiro da plataforma (escudo cabo-verdiano, settings.MOEDA).

Tudo é guardado em CVE; o formato é o tradicional: 1250 → "1.250$00", 12.5 → "12$50".
Só os gateways que ainda não aceitam CVE (settings.MOEDA_COBRANCA) recebem o valor
convertido em euros, ao câmbio fixo.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings


def _decimal(v):
    try:
        return Decimal(str(v if v is not None else 0))
    except Exception:
        return Decimal('0')


def formatar(v):
    """1250 → "1.250$00"; -3.5 → "-3$50"."""
    d = _decimal(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    sinal = '-' if d < 0 else ''
    inteiro, centavos = f'{abs(d):.2f}'.split('.')
    inteiro = f'{int(inteiro):,}'.replace(',', '.')
    return f'{sinal}{inteiro}${centavos}'


def cambio_eur():
    return Decimal(str(getattr(settings, 'CAMBIO_EUR', '110.265')))


def eur_para_cve(v, casas='0.01'):
    """Converte um valor em euros para escudos (arredondado a `casas`)."""
    return (_decimal(v) * cambio_eur()).quantize(Decimal(casas), rounding=ROUND_HALF_UP)


def moeda_cobranca(gateway):
    return getattr(settings, 'MOEDA_COBRANCA', {}).get(gateway, settings.MOEDA)


def valor_cobranca(valor, gateway):
    """(valor, moeda) a enviar ao gateway: em CVE, ou convertido para EUR se o gateway não aceita CVE."""
    moeda = moeda_cobranca(gateway)
    d = _decimal(valor)
    if moeda == 'EUR' and settings.MOEDA == 'CVE':
        d = (d / cambio_eur()).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return d, moeda
