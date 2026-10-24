"""
Dados fiscais de quem vende (loja ou POS) e faturas registadas nas encomendas.

O Bende ainda não emite faturas pelo e-Fatura: cada vendedor emite as suas (Emissor Público da DNRE
ou o seu programa) e regista o número/PDF na encomenda. Aqui fica:
- NIF + regime ('particular' = vendas ocasionais, 'atividade' = atividade declarada) + a declaração
  de responsabilidade aceite no registo;
- a validação do registo de uma fatura numa encomenda.
"""
import re

from django.db import transaction
from django.utils import timezone

REGIMES = [
    ('particular', 'Particular — vendas ocasionais'),
    ('atividade',  'Com atividade declarada'),
]
REGIMES_VALIDOS = {r for r, _ in REGIMES}

FATURA_PDF_MAX_MB = 5
# a fatura só se regista numa venda que aconteceu (não pendente de pagamento, nem cancelada)
ESTADOS_FATURAVEIS = ('pago', 'preparando', 'enviado', 'concluido')


def _verdadeiro(v):
    # FormData manda strings ('true', 'on', '1')
    return v is True or str(v).strip().lower() in ('true', '1', 'on', 'sim')


def validar_dados_fiscais(data):
    """data: request.data com nif, regime_fiscal, declaracao_fiscal. Devolve (dados, erros)."""
    erros = {}
    nif = re.sub(r'\D', '', str(data.get('nif') or ''))
    if len(nif) != 9:
        erros['nif'] = 'O NIF tem 9 dígitos.'
    regime = str(data.get('regime_fiscal') or '').strip()
    if regime not in REGIMES_VALIDOS:
        erros['regime_fiscal'] = 'Escolhe se vendes como particular ou com atividade declarada.'
    if not _verdadeiro(data.get('declaracao_fiscal')):
        erros['declaracao_fiscal'] = 'Tens de aceitar a declaração de responsabilidade fiscal.'
    if erros:
        return None, erros
    return {'nif': nif, 'regime_fiscal': regime}, {}


def aplicar_dados_fiscais(obj, dados, user=None, aceites_em=None):
    """Grava NIF/regime na Loja ou ConfiguracaoPOS; a data da declaração é a deste momento (ou a da loja, num
    POS que segue a loja). Fica no histórico. Numa loja, os POS ligados que seguem a loja acompanham."""
    from ..models import HistoricoDadosFiscais
    obj.nif = dados['nif']
    obj.regime_fiscal = dados['regime_fiscal']
    obj.dados_fiscais_aceites_em = aceites_em or timezone.now()
    with transaction.atomic():
        obj.save(update_fields=['nif', 'regime_fiscal', 'dados_fiscais_aceites_em'])
        e_loja = obj._meta.model_name == 'loja'
        HistoricoDadosFiscais.objects.create(
            loja=obj if e_loja else None, pos=None if e_loja else obj, nome=obj.nome[:200],
            nif=obj.nif, regime_fiscal=obj.regime_fiscal, aceites_em=obj.dados_fiscais_aceites_em,
            alterado_por=user if getattr(user, 'is_authenticated', False) else None)
        if e_loja:
            for pos in obj.pos_vinculados.filter(fiscal_da_loja=True):
                copiar_da_loja(pos, user)


def _completos(obj):
    return bool(obj and obj.nif and obj.regime_fiscal and obj.dados_fiscais_aceites_em)


def pos_segue_loja(pos):
    return bool(pos.fiscal_da_loja and pos.loja_vinculada_id)


def copiar_da_loja(pos, user=None):
    """POS que segue a loja: copia o NIF/regime dela (se os tiver e forem diferentes dos do POS)."""
    loja = pos.loja_vinculada
    if not _completos(loja):
        return
    if (pos.nif, pos.regime_fiscal, pos.dados_fiscais_aceites_em) == (loja.nif, loja.regime_fiscal, loja.dados_fiscais_aceites_em):
        return
    aplicar_dados_fiscais(pos, {'nif': loja.nif, 'regime_fiscal': loja.regime_fiscal}, user,
                          aceites_em=loja.dados_fiscais_aceites_em)


def ao_ligar_loja(pos, user=None):
    """Depois de ligar o POS a uma loja: sem dados próprios (ou com o mesmo NIF) passa a seguir a loja.
    Com outro NIF fica com o seu — o dono pode mudar na configuração."""
    loja = pos.loja_vinculada
    if not loja:
        return
    if not pos.fiscal_da_loja and (not pos.nif or pos.nif == loja.nif):
        pos.fiscal_da_loja = True
        pos.save(update_fields=['fiscal_da_loja'])
    if pos.fiscal_da_loja:
        copiar_da_loja(pos, user)


def historico_dados_fiscais(obj):
    """Loja ou POS: do mais recente (em vigor) para o mais antigo."""
    qs = obj.historico_fiscal.select_related('alterado_por')
    return [{'nif': h.nif, 'regime_fiscal': h.regime_fiscal, 'aceites_em': h.aceites_em, 'nome': h.nome,
             'alterado_por': _quem(h.alterado_por), 'atual': i == 0} for i, h in enumerate(qs)]


def dados_fiscais_payload(obj, detalhe=False):
    """Só para o dono/backoffice — o NIF nunca vai nos dados públicos da loja.
    POS: da_loja (segue a loja ligada). detalhe (configuração): POS + loja {id, nome, completos};
    loja + nomes dos POS que a seguem."""
    d = {
        'nif': obj.nif,
        'regime_fiscal': obj.regime_fiscal,
        'completos': _completos(obj),
        'aceites_em': obj.dados_fiscais_aceites_em,
    }
    e_loja = obj._meta.model_name == 'loja'
    if not e_loja:
        d['da_loja'] = pos_segue_loja(obj)
    if detalhe and e_loja:
        d['pos_seguem'] = list(obj.pos_vinculados.filter(fiscal_da_loja=True).values_list('nome', flat=True))
    elif detalhe:
        loja = obj.loja_vinculada
        d['loja'] = {'id': loja.id, 'nome': loja.nome, 'completos': _completos(loja)} if loja else None
    return d


def fatura_resumo(obj, request=None):
    """Fatura registada (encomenda, mensalidade ou comissões do mês) — None se ainda não há."""
    if not obj or not obj.fatura_registada_em:
        return None
    pdf = None
    if obj.fatura_pdf:
        pdf = request.build_absolute_uri(obj.fatura_pdf.url) if request else obj.fatura_pdf.url
    return {'numero': obj.fatura_numero, 'pdf_url': pdf, 'registada_em': obj.fatura_registada_em}


# ── Faturas registadas: em vigor nos campos fatura_* do documento + arquivo HistoricoFatura ──────────────

def _quem(user):
    if not user:
        return None
    return {'id': user.id, 'nome': user.get_full_name() or user.username, 'email': user.email}


def referencia(obj):
    """Referência do documento interno (a mesma do comprovativo/extrato em PDF)."""
    nome = obj._meta.model_name
    if nome == 'encomenda':
        return f'E-{obj.id}'
    if nome == 'faturasubscricao':
        return f'S-{obj.id}'
    return f'C-{obj.loja_id}-{obj.mes:%Y%m}'


def _ligacao(obj):
    """Campos do HistoricoFatura que identificam o documento."""
    nome = obj._meta.model_name
    if nome == 'encomenda':
        return {'tipo': 'encomenda', 'encomenda_id': obj.id}
    if nome == 'faturasubscricao':
        return {'tipo': 'mensalidade', 'fatura_subscricao_id': obj.id}
    return {'tipo': 'comissoes', 'loja_id': obj.loja_id, 'mes': obj.mes}


def historico_do_documento(obj):
    from ..models import HistoricoFatura
    return HistoricoFatura.objects.filter(**_ligacao(obj))


def _arquivar(obj, user):
    """Linha em vigor no arquivo para a fatura que está agora no documento."""
    from ..models import HistoricoFatura
    return HistoricoFatura.objects.create(**{
        'loja_id': obj.loja_id, 'pos_id': getattr(obj, 'pos_id', None), **_ligacao(obj),
        'referencia': referencia(obj), 'numero': obj.fatura_numero,
        'pdf': obj.fatura_pdf.name if obj.fatura_pdf else '', 'registada_em': obj.fatura_registada_em,
        'registada_por': user if getattr(user, 'is_authenticated', False) else None})


def _anular_em_vigor(obj, user, motivo):
    linha = historico_do_documento(obj).filter(anulada_em__isnull=True).first()
    if not linha and obj.fatura_registada_em:
        linha = _arquivar(obj, None)       # registada antes do arquivo existir
    if linha:
        linha.anulada_em = timezone.now()
        linha.anulada_por = user if getattr(user, 'is_authenticated', False) else None
        linha.motivo = motivo[:300]
        linha.save(update_fields=['anulada_em', 'anulada_por', 'motivo'])


def _gravar(obj):
    if obj.pk:
        obj.save(update_fields=['fatura_numero', 'fatura_pdf', 'fatura_registada_em'])
    else:
        obj.save()


def registar_fatura(obj, numero, pdf, user=None, motivo=''):
    """
    Regista (ou substitui) a fatura de uma encomenda, mensalidade ou FaturaComissoes e grava o documento.
    Substituir anula a anterior com o motivo (validado por quem chama) — o PDF antigo fica no arquivo.
    Sem PDF novo, a substituta fica com o PDF da anterior (corrigir só o número).
    """
    with transaction.atomic():
        if obj.pk and obj.fatura_registada_em:
            _anular_em_vigor(obj, user, motivo)
        if pdf:
            obj.fatura_pdf = pdf
        obj.fatura_numero = numero
        obj.fatura_registada_em = timezone.now()
        _gravar(obj)
        _arquivar(obj, user)


def anular_fatura(obj, user, motivo):
    """A fatura deixa de estar em vigor (registo errado, fatura anulada no e-Fatura…). Nada se apaga."""
    with transaction.atomic():
        _anular_em_vigor(obj, user, motivo)
        if obj._meta.model_name == 'faturacomissoes':
            obj.delete()     # o PDF continua referido no arquivo → a limpeza não lhe toca
            return
        obj.fatura_numero, obj.fatura_pdf, obj.fatura_registada_em = '', '', None
        _gravar(obj)


def validar_motivo(motivo):
    """Devolve (motivo_limpo, erro)."""
    motivo = (motivo or '').strip()
    if len(motivo) < 3:
        return None, 'Indica o motivo (fica no histórico da fatura).'
    return motivo[:300], None


def historico_payload(qs, request=None):
    def url(f):
        return (request.build_absolute_uri(f.url) if request else f.url) if f else None
    return [{'id': h.id, 'referencia': h.referencia, 'numero': h.numero, 'pdf_url': url(h.pdf),
             'registada_em': h.registada_em, 'registada_por': _quem(h.registada_por),
             'anulada_em': h.anulada_em, 'anulada_por': _quem(h.anulada_por), 'motivo': h.motivo}
            for h in qs.select_related('registada_por', 'anulada_por')]


def validar_fatura(numero, pdf):
    """Devolve (numero_limpo, erro)."""
    numero = (numero or '').strip()
    if not numero:
        return None, 'Indica o número da fatura.'
    if len(numero) > 60:
        return None, 'O número da fatura tem no máximo 60 caracteres.'
    if pdf:
        if not pdf.name.lower().endswith('.pdf') or (pdf.content_type or '') not in ('application/pdf', 'application/octet-stream'):
            return None, 'A fatura tem de ser um PDF.'
        if pdf.size > FATURA_PDF_MAX_MB * 1024 * 1024:
            return None, f'O PDF tem no máximo {FATURA_PDF_MAX_MB} MB.'
        if pdf.read(5) != b'%PDF-':
            return None, 'O ficheiro não é um PDF válido.'
        pdf.seek(0)
    return numero, None
