"""
Dinheiro da plataforma (escudo cabo-verdiano, settings.MOEDA).

Tudo é guardado em CVE; o formato é o tradicional: 1250 → "1.250$00", 12.5 → "12$50".
Só os gateways que ainda não aceitam CVE (settings.MOEDA_COBRANCA) recebem o valor
convertido em euros, ao câmbio fixo.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings


VALOR_MAX = Decimal('99999999.99')   # numeric(10, 2) — o máximo que a base de dados guarda


def _decimal(v):
    try:
        return Decimal(str(v if v is not None else 0))
    except Exception:
        return Decimal('0')


def ler_valor(v, nome='O valor', obrigatorio=True):
    """
    Valor vindo do cliente → (Decimal com 2 casas, None) ou (None, mensagem de erro).
    Recusa texto, NaN/Infinity, negativos e valores acima do que a base de dados guarda
    (antes "NaN" ou 1e12 davam erro 500 ou ficavam gravados).
    """
    if v in (None, ''):
        return (None, f'{nome} é obrigatório.') if obrigatorio else (None, None)
    try:
        d = Decimal(str(v).strip().replace(',', '.'))
    except Exception:
        return None, f'{nome} não é um número válido.'
    if not d.is_finite():
        return None, f'{nome} não é um número válido.'
    if d < 0:
        return None, f'{nome} não pode ser negativo.'
    d = d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if d > VALOR_MAX:
        return None, f'{nome} é demasiado alto (máximo {formatar(VALOR_MAX)}).'
    return d, None


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
