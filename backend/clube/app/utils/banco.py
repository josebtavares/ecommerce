"""
Dados bancários da loja (models.DadosBancarios): a conta para onde vai o dinheiro das vendas quando
os pagamentos online estiverem activos. A loja nunca configura um fornecedor de pagamento — só diz o banco.

NIB de Cabo Verde: 21 dígitos (banco 4 + balcão 4 + conta 11 + controlo 2). O IBAN é CV64 + NIB e os
dígitos de controlo do NIB fazem o IBAN bater certo (mod 97 = 1) — a mesma conta valida o NIB.
Aceita-se um ou outro, com ou sem espaços/pontos/traços.
"""
import re

BANCOS = [
    'Banco Comercial do Atlântico (BCA)',
    'Caixa Económica de Cabo Verde (CECV)',
    'Banco Interatlântico (BI)',
    'Banco Cabo-verdiano de Negócios (BCN)',
    'BAI Cabo Verde',
    'Ecobank Cabo Verde',
    'International Investment Bank (IIB)',
    'Outro',
]


def _mod97(iban):
    texto = iban[4:] + iban[:4]
    return int(''.join(str(int(c, 36)) for c in texto)) % 97


def normalizar_nib(valor):
    """'CV64 0003 0000 4547 0691 1017 6' ou o NIB → ('000300004547069110176', None) | (None, erro)."""
    texto = re.sub(r'[\s.\-]', '', str(valor or '')).upper()
    if not texto:
        return None, 'Indica o NIB ou o IBAN da conta.'
    if texto.startswith('CV'):
        if not re.fullmatch(r'CV\d{23}', texto):
            return None, 'O IBAN de Cabo Verde tem CV e 23 dígitos (ex.: CV64 0003 0000 4547 0691 1017 6).'
        iban = texto
    elif re.fullmatch(r'\d{21}', texto):
        iban = 'CV64' + texto
    else:
        return None, 'O NIB tem 21 dígitos (ou cola o IBAN, que começa por CV64).'
    if _mod97(iban) != 1:
        return None, 'Este NIB/IBAN não é válido — confirma os dígitos no extracto ou na app do banco.'
    return iban[4:], None


def iban(nib):
    return f'CV64{nib}' if nib else ''


def formatar_iban(nib):
    """CV64 0003 0000 4547 0691 1017 6"""
    t = iban(nib)
    return ' '.join(t[i:i + 4] for i in range(0, len(t), 4))


def mascarado(nib):
    return f'CV64 •••• •••• •••• •••• {nib[-4:]}' if nib else ''


def validar(dados):
    """{banco, nib|iban, titular} → (limpos, erros)."""
    erros = {}
    banco = (dados.get('banco') or '').strip()
    if banco not in BANCOS:
        erros['banco'] = 'Escolhe o banco da lista.'
    nib, erro = normalizar_nib(dados.get('nib') or dados.get('iban'))
    if erro:
        erros['nib'] = erro
    titular = re.sub(r'\s+', ' ', (dados.get('titular') or '')).strip()
    if not 3 <= len(titular) <= 120:
        erros['titular'] = 'Indica o nome do titular da conta, como aparece no banco.'
    return {'banco': banco, 'nib': nib, 'titular': titular}, erros


def payload(d, completo=True):
    if d is None:
        return None
    return {
        'banco': d.banco,
        'titular': d.titular,
        'iban': formatar_iban(d.nib) if completo else mascarado(d.nib),
        'nib': d.nib if completo else '',
        'final': d.nib[-4:],
        'atualizado_em': d.atualizado_em.isoformat() if d.atualizado_em else None,
    }
