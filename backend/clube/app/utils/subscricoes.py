"""
Subscrições das lojas — a alternativa à comissão por venda.

- Na criação o dono escolhe 'comissao' ou 'subscricao' (+ plano). A Subscricao fica 'aguarda'
  até o admin aprovar a loja; aí arranca com o período de teste (ConfiguracaoPlataforma
  .subscricao_dias_teste) e a primeira fatura vence no fim do teste.
- Cada fatura cobre [periodo_inicio, periodo_fim). Pagar estende pago_ate até periodo_fim.
- As encomendas guardam o modelo da loja quando são feitas (Encomenda.modelo_cobranca) —
  as de subscrição não registam comissão (Comissao.registar).
Fase 2 (worker): emitir as faturas seguintes, avisos, carência e suspensão automática.

A subscrição pode ser de uma loja OU de um POS (Subscricao.alvo). O que é só dos POS
(criação, mês grátis, escolher o plano) está em utils/subscricoes_pos.py; aqui ficam as
peças comuns (faturas, pagar, avisos, acções do admin).
"""
import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ..models import ConfiguracaoPlataforma, FaturaSubscricao, Loja, PlanoSubscricao, Subscricao


def hoje():
    from .horarios import agora
    return agora().date()


def _eur(v):
    """1500 → "1.500$00" (como no resto do site)."""
    from .dinheiro import formatar
    return formatar(v)


def mais_meses(d, n):
    """31/01 + 1 mês = 28/02 (ou 29); fica no último dia do mês quando o dia não existe."""
    m = d.month - 1 + n
    ano, mes = d.year + m // 12, m % 12 + 1
    return date(ano, mes, min(d.day, calendar.monthrange(ano, mes)[1]))


def _descricao(plano, inicio, fim):
    ultimo = fim - timedelta(days=1)
    nome = plano.nome if plano else 'Subscrição'
    if plano and plano.tipo == 'servicos' and 'servi' not in nome.lower():
        nome = f'Serviços · {nome}'
    return f'{nome} — {inicio:%d/%m/%Y} a {ultimo:%d/%m/%Y}'


def emitir_fatura(sub, inicio, vencimento=None):
    """
    Fatura do período que começa em `inicio` (preço e duração do contrato da loja).
    Plano de 0$00 → fica logo paga ("Plano gratuito"), sem avisos: nunca há nada para pagar
    nem suspensão por "dívida" de 0$00.
    """
    fim = mais_meses(inicio, sub.meses)
    f = FaturaSubscricao.objects.create(
        loja_id=sub.loja_id or sub.loja_servicos_id, pos_id=sub.pos_id, subscricao=sub, plano=sub.plano,
        descricao=_descricao(sub.plano, inicio, fim),
        periodo_inicio=inicio, periodo_fim=fim, valor=sub.preco, vencimento=vencimento or inicio,
    )
    if not f.valor:
        pagar(f, 'oferta', referencia=f'GRATIS-{f.id}', notas='Plano gratuito', avisar=False)
        f.refresh_from_db()
        sub.refresh_from_db()
    return f


# ── Criar / arrancar ──────────────────────────────────────────

def criar_para_loja_nova(loja, plano):
    """Na criação da loja: fica à espera da aprovação."""
    d = hoje()
    return Subscricao.objects.create(loja=loja, plano=plano, preco=plano.preco, meses=plano.meses,
                                     estado='aguarda', inicio=d, pago_ate=d)


@transaction.atomic
def arrancar(loja, com_teste=True):
    """
    Quando o admin aprova a loja (ou passa uma loja para subscrição): começa o período de teste
    (se houver) e emite a primeira fatura, que vence quando o teste acaba (ou hoje, sem teste).
    """
    sub = Subscricao.objects.select_for_update().filter(loja=loja).first()
    if not sub or sub.estado != 'aguarda':
        return sub
    d = hoje()
    dias = ConfiguracaoPlataforma.atual().subscricao_dias_teste if com_teste else 0
    sub.inicio = d
    sub.pago_ate = d + timedelta(days=dias)
    sub.teste_ate = sub.pago_ate if dias else None
    sub.estado = 'teste' if dias else 'ativa'
    sub.save(update_fields=['inicio', 'pago_ate', 'teste_ate', 'estado', 'data_atualizacao'])
    fatura = emitir_fatura(sub, sub.pago_ate)
    if fatura.estado == 'pendente':
        _avisar_fatura(fatura, nova=True)
    return sub


# ── Pagar ─────────────────────────────────────────────────────

class ErroFatura(Exception):
    pass


# motivo da suspensão automática — pagar só reactiva a loja se o motivo for este
MOTIVO_SUSPENSAO = 'Subscrição por pagar'
DIAS_AVISO = 7          # a fatura seguinte é emitida 7 dias antes do fim do período
DIAS_CARENCIA = 30      # depois do vencimento a loja continua a funcionar 30 dias
# os planos que uma loja pode escolher (o Loja + POS inclui também o POS ligado à loja)
TIPOS_LOJA = ('loja', 'loja_pos')


@transaction.atomic
def pagar(fatura, metodo, referencia='', notas='', quando=None, avisar=True):
    """
    Marca a fatura como paga e estende o serviço até ao fim do período. Reactiva a loja se estava
    suspensa por falta de pagamento. Se for a 1.ª fatura de um pedido de mudança para subscrição
    (subscrição 'aguarda' numa loja activa em comissão), a subscrição começa agora.
    """
    d = quando or hoje()
    if metodo not in dict(FaturaSubscricao.METODOS):
        raise ErroFatura('Método de pagamento inválido.')
    # bloqueios sempre pela mesma ordem do worker (subscrição → fatura → loja): sem impasses
    sub = Subscricao.objects.select_for_update().get(pk=fatura.subscricao_id)
    fatura = FaturaSubscricao.objects.select_for_update().get(pk=fatura.pk)
    if fatura.estado != 'pendente':
        raise ErroFatura('Esta fatura já não está por pagar.')
    loja = Loja.objects.select_for_update().get(pk=fatura.loja_id) if fatura.loja_id else None

    # 1.ª fatura de um pedido de mudança para subscrição (a de Serviços não muda o modelo da loja)
    ativacao = bool(loja) and sub.estado == 'aguarda' and loja.modelo_cobranca == 'comissao' and not sub.servicos
    ativa_servicos = sub.servicos and sub.estado == 'aguarda'
    if ativacao or ativa_servicos:
        # o período conta a partir do dia em que paga (não do dia em que pediu)
        fatura.periodo_inicio, fatura.periodo_fim = d, mais_meses(d, sub.meses)
        fatura.descricao = _descricao(sub.plano, fatura.periodo_inicio, fatura.periodo_fim)
        sub.inicio = d
    fatura.estado, fatura.paga_em, fatura.metodo = 'paga', timezone.now(), metodo
    fatura.referencia, fatura.notas = referencia[:100], (notas or fatura.notas)[:300]
    fatura.save(update_fields=['estado', 'paga_em', 'metodo', 'referencia', 'notas', 'periodo_inicio', 'periodo_fim', 'descricao'])

    if fatura.periodo_fim > sub.pago_ate:
        sub.pago_ate = fatura.periodo_fim
    if ativacao or ativa_servicos:
        sub.estado = 'ativa'
    if ativacao:
        loja.modelo_cobranca, loja.modelo_alterado_em = 'subscricao', timezone.now()
        loja.save(update_fields=['modelo_cobranca', 'modelo_alterado_em', 'data_atualizacao'])
    # pagar durante o teste não o encurta: continua 'teste' até o período pago começar
    elif sub.estado == 'teste' and d >= fatura.periodo_inicio:
        sub.estado = 'ativa'
    sub.save()
    reativou = _reavaliar(sub, d)
    if ativacao:
        from .subscricoes_pos import sincronizar_pos_da_loja
        from ..servicos.cobranca import loja_mudou_modelo
        sincronizar_pos_da_loja(loja.id)           # plano Loja + POS: o POS ligado passa a estar incluído
        loja_mudou_modelo(loja)                    # os Serviços passam a estar incluídos
    if not avisar:
        return fatura

    alvo = sub.alvo
    _avisar_dono(alvo, f'Subscrição paga — {fatura.descricao}',
                 f'{_eur(fatura.valor)} recebidos. Pago até {sub.pago_ate - timedelta(days=1):%d/%m/%Y}.'
                 + (' A loja passou para subscrição — as vendas deixam de pagar comissão.' if ativacao else '')
                 + (' O módulo Serviços está activo.' if ativa_servicos else '')
                 + ((' O módulo Serviços voltou.' if sub.servicos else ' A loja foi reactivada.' if loja
                     else ' O POS foi reactivado.') if reativou else ''),
                 tipo='subscricao_paga')
    _avisar_admins(alvo, f'Subscrição paga — {nome_alvo(alvo)}',
                   f'Fatura #{fatura.id} · {_eur(fatura.valor)} · {fatura.get_metodo_display()}.'
                   + (' Passou de comissão para subscrição.' if ativacao else ''),
                   tipo='subscricao_paga')
    return fatura


def _reavaliar(sub, d=None):
    """
    Depois de pagar / oferecer / adiar / anular: se já não há faturas vencidas, a subscrição
    volta a 'ativa' e, se a loja estava suspensa por falta de pagamento, a loja volta.
    Se passou a haver uma vencida, fica 'em_atraso'. Devolve True se reactivou a loja.
    """
    d = d or hoje()
    if sub.estado in ('aguarda', 'cancelada'):
        return False
    vencidas = sub.faturas.filter(estado='pendente', vencimento__lt=d).exists()
    reativou = False
    if not vencidas and sub.estado in ('em_atraso', 'suspensa'):
        era_suspensa = sub.estado == 'suspensa'
        sub.estado = 'teste' if (sub.teste_ate and d < sub.teste_ate) else 'ativa'
        sub.save(update_fields=['estado', 'data_atualizacao'])
        if sub.pos_id:
            from ..pos.models import ConfiguracaoPOS
            return era_suspensa and reativar_pos(ConfiguracaoPOS.objects.get(pk=sub.pos_id))
        if sub.servicos:
            return era_suspensa                        # só o módulo estava suspenso, a loja nunca
        loja = Loja.objects.get(pk=sub.loja_id)
        if era_suspensa and loja.estado == 'suspensa' and loja.estado_motivo.startswith(MOTIVO_SUSPENSAO):
            loja.mudar_estado('ativa')
            reativou = True
        if era_suspensa:
            from .subscricoes_pos import sincronizar_pos_da_loja
            sincronizar_pos_da_loja(sub.loja_id)       # o POS incluído no plano da loja volta com ela
    elif vencidas and sub.estado in ('teste', 'ativa'):
        sub.estado = 'em_atraso'
        sub.save(update_fields=['estado', 'data_atualizacao'])
    return reativou


def _avisar_fatura(fatura, nova=False):
    _avisar_dono(fatura.alvo,
                 f'Nova fatura da subscrição — {_eur(fatura.valor)}' if nova else f'Fatura por pagar — {_eur(fatura.valor)}',
                 f'{fatura.descricao}. Vence a {fatura.vencimento:%d/%m/%Y}.')


# ── Mudar o modelo (admin) ────────────────────────────────────

@transaction.atomic
def mudar_modelo(loja, modelo, plano=None):
    """
    O admin força o modelo de uma loja. Para subscrição: (re)começa sem período de teste, com a
    primeira fatura a vencer hoje. Para comissão: a subscrição fica cancelada e as faturas por
    pagar anuladas (não se apagam). As encomendas já feitas mantêm o modelo que tinham.
    """
    sub = Subscricao.objects.select_for_update().filter(loja_id=loja.pk).first()     # subscrição → loja
    loja = Loja.objects.select_for_update().get(pk=loja.pk)
    if modelo == 'subscricao':
        if plano is None:
            raise ErroFatura('Escolhe o plano.')
        if sub and sub.estado != 'cancelada' and loja.modelo_cobranca == 'subscricao':
            raise ErroFatura('A loja já está em subscrição.')
        d = hoje()
        if sub:
            sub.faturas.filter(estado='pendente').update(estado='anulada', notas='Anulada: a plataforma mudou o modelo da loja.')
            sub.plano, sub.preco, sub.meses = plano, plano.preco, plano.meses
            sub.estado, sub.inicio, sub.pago_ate, sub.teste_ate = 'aguarda', d, d, None
            sub.fim_agendado, sub.plano_seguinte = None, None
            sub.save()
        else:
            sub = Subscricao.objects.create(loja=loja, plano=plano, preco=plano.preco, meses=plano.meses,
                                            estado='aguarda', inicio=d, pago_ate=d)
        loja.modelo_cobranca, loja.modelo_alterado_em = 'subscricao', timezone.now()
        loja.save(update_fields=['modelo_cobranca', 'modelo_alterado_em', 'data_atualizacao'])
        if loja.estado == 'ativa':
            arrancar(loja, com_teste=False)
    elif modelo == 'comissao':
        if loja.modelo_cobranca == 'comissao':
            raise ErroFatura('A loja já está em comissão.')
        if sub:
            sub.estado, sub.fim_agendado, sub.plano_seguinte = 'cancelada', None, None
            sub.save(update_fields=['estado', 'fim_agendado', 'plano_seguinte', 'data_atualizacao'])
            sub.faturas.filter(estado='pendente').update(estado='anulada', notas='Anulada: a loja passou para comissão.')
        loja.modelo_cobranca, loja.modelo_alterado_em = 'comissao', timezone.now()
        loja.save(update_fields=['modelo_cobranca', 'modelo_alterado_em', 'data_atualizacao'])
    else:
        raise ErroFatura('Modelo inválido.')
    from .subscricoes_pos import sincronizar_pos_da_loja
    from ..servicos.cobranca import loja_mudou_modelo
    sincronizar_pos_da_loja(loja.id)
    loja_mudou_modelo(loja)
    return loja


# ── Payloads ──────────────────────────────────────────────────

def plano_payload(p):
    return {'id': p.id, 'nome': p.nome, 'tipo': p.tipo, 'tipo_nome': p.get_tipo_display(),
            'periodicidade': p.periodicidade, 'periodicidade_nome': p.get_periodicidade_display(),
            'meses': p.meses, 'preco': str(p.preco), 'preco_mes': str((p.preco / p.meses).quantize(Decimal('0.01'))),
            'descricao': p.descricao, 'ativo': p.ativo, 'ordem': p.ordem,
            'limite_marcacoes_mes': p.limite_marcacoes_mes, 'limite_profissionais': p.limite_profissionais}


def fatura_payload(f):
    return {'id': f.id, 'descricao': f.descricao, 'periodo_inicio': f.periodo_inicio.isoformat(),
            'periodo_fim': (f.periodo_fim - timedelta(days=1)).isoformat(), 'valor': str(f.valor),
            'estado': f.estado, 'estado_nome': f.get_estado_display(), 'vencimento': f.vencimento.isoformat(),
            'atrasada': f.estado == 'pendente' and f.vencimento < hoje(),
            'paga_em': f.paga_em.isoformat() if f.paga_em else None, 'metodo': f.metodo,
            'metodo_nome': f.get_metodo_display() if f.metodo else '', 'notas': f.notas, 'loja_id': f.loja_id,
            'pos_id': f.pos_id, 'loja_nome': nome_alvo(f.alvo), 'paga': f.estado == 'paga',
            'servicos': bool(f.plano_id) and f.plano.tipo == 'servicos'}


def plano_em_curso(sub, d=None):
    """O plano do período pago que está a decorrer (pode ser outro se o dono mudou de plano)."""
    d = d or hoje()
    f = sub.faturas.filter(estado='paga', periodo_inicio__lte=d, periodo_fim__gt=d).select_related('plano').order_by('-periodo_inicio').first()
    return f.plano if f else None


def subscricao_payload(sub):
    if not sub:
        return None
    atual = plano_em_curso(sub)
    return {'id': sub.id, 'plano': plano_payload(sub.plano) if sub.plano_id else None,
            'preco': str(sub.preco), 'meses': sub.meses,
            # mudou de plano a meio: o período em curso foi pago noutro plano (o novo começa em pago_ate)
            'plano_em_curso': plano_payload(atual) if atual and atual.id != sub.plano_id else None,
            'estado': sub.estado, 'estado_nome': sub.get_estado_display(), 'inicio': sub.inicio.isoformat(),
            # último dia pago (pago_ate é o dia em que deixa de estar)
            'pago_ate': (sub.pago_ate - timedelta(days=1)).isoformat() if sub.pago_ate > sub.inicio else None,
            'teste_ate': (sub.teste_ate - timedelta(days=1)).isoformat() if sub.teste_ate else None,
            # passa para comissão neste dia (o 1.º já sem subscrição)
            'fim_agendado': sub.fim_agendado.isoformat() if sub.fim_agendado else None,
            'plano_seguinte': plano_payload(sub.plano_seguinte) if sub.plano_seguinte_id else None,
            'auto_renovar': sub.auto_renovar, 'servicos': sub.servicos}


def planos_ativos(tipos=TIPOS_LOJA):
    return list(PlanoSubscricao.objects.filter(ativo=True, tipo__in=tipos))


def nome_alvo(alvo):
    """Nome para mostrar: a loja ou "POS <nome> (<código>)"."""
    if isinstance(alvo, Loja):
        return alvo.nome
    return f'POS {alvo.nome} ({alvo.codigo_pos})' if alvo else ''


# ── Ciclo automático (worker: processar_videos, a cada 10 minutos) ───────────

def _marcar(fatura, chave):
    """True se o aviso `chave` ainda não tinha sido dado (e regista-o)."""
    if chave in (fatura.avisos or []):
        return False
    fatura.avisos = [*(fatura.avisos or []), chave]
    fatura.save(update_fields=['avisos'])
    return True


def _avisar_dono(alvo, titulo, mensagem, tipo='subscricao_fatura'):
    """Notifica o dono da loja (backoffice) ou do POS (painel do POS)."""
    from ..Views.notificacaoView import notificar, notificar_staff
    if isinstance(alvo, Loja):
        notificar_staff(loja=alvo, roles=['dono'], tipo=tipo, titulo=titulo, mensagem=mensagem,
                        link=f'/loja/{alvo.id}/backoffice')
    else:
        notificar(utilizador=alvo.dono, tipo=tipo, titulo=titulo, mensagem=mensagem, link='/pos/dashboard')


def _avisar_admins(alvo, titulo, mensagem, tipo='subscricao_fatura'):
    from ..Views.notificacaoView import notificar_admins
    notificar_admins(tipo=tipo, titulo=titulo, mensagem=mensagem,
                     loja=alvo if isinstance(alvo, Loja) else None, link='/admin')


def suspensao_em(fatura):
    """Dia em que a loja é suspensa se esta fatura não for paga."""
    return fatura.vencimento + timedelta(days=DIAS_CARENCIA)


def processar(quando=None):
    """
    Uma volta do ciclo para todas as subscrições activas (lojas primeiro, depois os POS).
    Idempotente: os avisos ficam registados na fatura (FaturaSubscricao.avisos) e cada passo
    só acontece uma vez.
      1. fim do teste → 'ativa'
      2. fatura do período seguinte emitida 7 dias antes (ao preço actual do plano)
      3. avisos 3 dias antes e no dia
      4. no dia: pagamento automático (simulado) se estiver ligado
      5. depois do vencimento: 'em_atraso' + avisos aos 7, 14, 21 e 28 dias
      6. 30 dias depois do vencimento: loja / POS suspenso (MOTIVO_SUSPENSAO)
    Os POS têm ainda o fim do período grátis sem plano e o plano Loja + POS (subscricoes_pos).
    Devolve um resumo {'emitidas', 'pagas_auto', 'em_atraso', 'suspensas'}.
    """
    from .subscricoes_pos import processar_pos
    d = quando or hoje()
    resumo = {'emitidas': 0, 'pagas_auto': 0, 'em_atraso': 0, 'suspensas': 0}
    lojas = Subscricao.objects.filter(estado__in=['teste', 'ativa', 'em_atraso'], loja__modelo_cobranca='subscricao')
    # os suspensos também: deixam de o estar se passarem a estar incluídos no plano da loja
    pos = Subscricao.objects.filter(pos__isnull=False, estado__in=['teste', 'ativa', 'em_atraso', 'suspensa'])
    servicos = Subscricao.objects.filter(loja_servicos__isnull=False, estado__in=['teste', 'ativa', 'em_atraso'])
    from ..servicos.cobranca import processar as processar_servicos
    for pk in [*lojas.order_by('pk').values_list('pk', flat=True), *pos.order_by('pk').values_list('pk', flat=True),
               *servicos.order_by('pk').values_list('pk', flat=True)]:
        try:
            with transaction.atomic():
                sub = Subscricao.objects.select_for_update(of=('self',)).select_related(
                    'loja', 'pos', 'loja_servicos', 'plano').get(pk=pk)
                (_processar_uma if sub.loja_id else processar_servicos if sub.servicos else processar_pos)(sub, d, resumo)
        except Exception as e:          # uma loja com problemas não pára as outras
            import logging
            logging.getLogger(__name__).exception('subscrição %s: %s', pk, e)
    return resumo


def textos(alvo, sub=None):
    """As palavras que mudam entre loja, POS e o módulo Serviços nos avisos."""
    if sub is not None and sub.servicos:
        from ..servicos.cobranca import TEXTOS
        return {**TEXTOS, 'nome': f'Serviços de {alvo.nome}'}
    if isinstance(alvo, Loja):
        return {'o': 'a loja', 'O': 'A loja', 'suspenso': 'suspensa', 'reactivado': 'reactivada',
                'onde': 'Backoffice → Subscrição', 'nome': alvo.nome}
    return {'o': 'o POS', 'O': 'O POS', 'suspenso': 'suspenso', 'reactivado': 'reactivado',
            'onde': 'POS → Subscrição', 'nome': nome_alvo(alvo)}


def suspender(alvo, motivo):
    """Suspende a loja ou o POS por falta de pagamento (se ainda estiver a funcionar)."""
    if isinstance(alvo, Loja):
        if alvo.estado == 'ativa':
            alvo.mudar_estado('suspensa', motivo)
        return
    if not alvo.suspenso:
        alvo.suspenso, alvo.suspenso_motivo, alvo.suspenso_em = True, motivo[:300], timezone.now()
        alvo.save(update_fields=['suspenso', 'suspenso_motivo', 'suspenso_em'])


def reativar_pos(pos):
    """Levanta a suspensão do POS só se foi por falta de pagamento. True se levantou."""
    if pos.suspenso and pos.suspenso_motivo.startswith(MOTIVO_SUSPENSAO):
        pos.suspenso, pos.suspenso_motivo, pos.suspenso_em = False, '', None
        pos.save(update_fields=['suspenso', 'suspenso_motivo', 'suspenso_em'])
        return True
    return False


def _processar_uma(sub, d, resumo):
    loja = sub.loja
    if loja.estado not in ('ativa', 'fechada'):
        return

    # 0. o dono pediu para passar a comissão e o período pago acabou
    if sub.fim_agendado and d >= sub.fim_agendado:
        sub.faturas.filter(estado='pendente').update(estado='anulada', notas='Anulada: a loja passou para comissão.')
        sub.estado, sub.fim_agendado = 'cancelada', None
        sub.save(update_fields=['estado', 'fim_agendado', 'data_atualizacao'])
        loja.modelo_cobranca, loja.modelo_alterado_em = 'comissao', timezone.now()
        loja.save(update_fields=['modelo_cobranca', 'modelo_alterado_em', 'data_atualizacao'])
        _avisar_dono(loja, 'A loja passou para comissão',
                     f'A partir de hoje pagas {loja.percentagem_comissao}% por venda e deixas de ter mensalidade.')
        from ..servicos.cobranca import loja_mudou_modelo
        loja_mudou_modelo(loja)
        return
    if ciclo_faturas(sub, loja, d, resumo):
        from .subscricoes_pos import sincronizar_pos_da_loja
        sincronizar_pos_da_loja(loja.id)          # o POS incluído no plano da loja vai com ela


def ciclo_faturas(sub, alvo, d, resumo):
    """Passos 1–6 para uma loja, um POS com plano ou o módulo Serviços. Devolve True se suspendeu a loja/POS."""
    t = textos(alvo, sub)

    # 1. fim do teste
    if sub.estado == 'teste' and sub.teste_ate and d >= sub.teste_ate:
        sub.estado = 'ativa'
        sub.save(update_fields=['estado', 'data_atualizacao'])

    # 2. fatura do período seguinte, 7 dias antes de o período pago acabar
    tem_seguinte = sub.faturas.filter(periodo_inicio=sub.pago_ate).exclude(estado='anulada').exists()
    if not tem_seguinte and not sub.fim_agendado and d >= sub.pago_ate - timedelta(days=DIAS_AVISO):
        if sub.plano_seguinte_id:                                             # o dono mudou de plano
            sub.plano, sub.plano_seguinte = sub.plano_seguinte, None
            sub.save(update_fields=['plano', 'plano_seguinte', 'data_atualizacao'])
        if sub.preco != sub.plano.preco or sub.meses != sub.plano.meses:      # renova ao preço actual do plano
            sub.preco, sub.meses = sub.plano.preco, sub.plano.meses
            sub.save(update_fields=['preco', 'meses', 'data_atualizacao'])
        f = emitir_fatura(sub, sub.pago_ate)
        _marcar(f, 'emitida')
        if f.estado == 'pendente':
            _avisar_fatura(f, nova=True)
        resumo['emitidas'] += 1

    for f in sub.faturas.filter(estado='pendente').order_by('vencimento'):
        falta = (f.vencimento - d).days
        # 3. lembretes
        if falta == 3 and _marcar(f, 'd3'):
            _avisar_dono(alvo, f'A fatura da subscrição vence daqui a 3 dias — {_eur(f.valor)}',
                         f'{f.descricao}. Vence a {f.vencimento:%d/%m/%Y}.')
        # 4. no dia (ou depois, se o worker esteve parado): pagamento automático
        if falta <= 0 and sub.auto_renovar and 'auto' not in (f.avisos or []):
            _marcar(f, 'auto')
            pagar(f, 'simulado', referencia=f'AUTO-{f.id}', notas='Pagamento automático', quando=d)
            resumo['pagas_auto'] += 1
            sub.refresh_from_db()
            continue
        if falta == 0 and _marcar(f, 'd0'):
            _avisar_dono(alvo, f'A fatura da subscrição vence hoje — {_eur(f.valor)}',
                         f'{f.descricao}. Paga hoje em {t["onde"]}.')
        if falta >= 0:
            continue

        # 5. em atraso
        atraso = -falta
        limite = suspensao_em(f)
        if sub.estado != 'em_atraso' and sub.estado != 'suspensa':
            sub.estado = 'em_atraso'
            sub.save(update_fields=['estado', 'data_atualizacao'])
            resumo['em_atraso'] += 1
        if _marcar(f, 'atraso'):
            _avisar_dono(alvo, f'Subscrição em atraso — {_eur(f.valor)}',
                         f'{f.descricao} venceu a {f.vencimento:%d/%m/%Y}. '
                         f'Se não for paga, {t["o"]} é {t["suspenso"]} a {limite:%d/%m/%Y}.')
            _avisar_admins(alvo, f'Subscrição em atraso — {t["nome"]}',
                           f'Fatura #{f.id} · {_eur(f.valor)} · venceu a {f.vencimento:%d/%m/%Y}.')
        for dias in (7, 14, 21, 28):
            if atraso >= dias and atraso < DIAS_CARENCIA and _marcar(f, f'a{dias}'):
                faltam = (limite - d).days
                _avisar_dono(alvo, f'Subscrição em atraso há {dias} dias — {_eur(f.valor)}',
                             f'Faltam {faltam} dia(s): {t["o"]} é {t["suspenso"]} a {limite:%d/%m/%Y} se a fatura não for paga.')

        # 6. fim da carência → suspensa
        if d >= limite and _marcar(f, 'suspensa'):
            sub.estado = 'suspensa'
            sub.save(update_fields=['estado', 'data_atualizacao'])
            if not sub.servicos:                      # Serviços: o módulo pára (sub suspensa), a loja não
                suspender(alvo, f'{MOTIVO_SUSPENSAO} (fatura #{f.id}, {_eur(f.valor)}).')
            _avisar_dono(alvo, f'{t["O"]} foi {t["suspenso"]} — subscrição por pagar',
                         f'A fatura de {_eur(f.valor)} venceu a {f.vencimento:%d/%m/%Y}. '
                         f'Paga em {t["onde"]} e {t["o"]} volta logo.')
            _avisar_admins(alvo, f'{"Serviços suspensos" if sub.servicos else "Loja suspensa" if isinstance(alvo, Loja) else "POS suspenso"}'
                                 f' automaticamente — {t["nome"]}',
                           f'Subscrição por pagar: fatura #{f.id}, {_eur(f.valor)}, vencida a {f.vencimento:%d/%m/%Y}.')
            resumo['suspensas'] += 1
            return not sub.servicos
    return False


def aviso_loja(sub, pendentes, quando=None):
    """
    A faixa do backoffice: None, ou {'tipo': 'suspensa'|'atraso'|'vence', 'texto', 'suspensao_em'}.
    `pendentes` = faturas por pagar da loja.
    """
    if not sub or sub.estado in ('aguarda', 'cancelada'):
        return None
    d = quando or hoje()
    pend = sorted(pendentes, key=lambda f: f.vencimento)
    serv = sub.servicos
    if sub.estado == 'suspensa':
        return {'tipo': 'suspensa', 'suspensao_em': None, 'servicos': serv,
                'texto': 'O módulo Serviços está suspenso porque a subscrição não foi paga. Paga a fatura e volta logo.'
                if serv else 'A loja está suspensa porque a subscrição não foi paga. Paga a fatura e a loja volta logo.'}
    vencidas = [f for f in pend if f.vencimento < d]
    if vencidas:
        limite = suspensao_em(vencidas[0])
        return {'tipo': 'atraso', 'suspensao_em': limite.isoformat(), 'servicos': serv,
                'texto': f'Subscrição {"de Serviços " if serv else ""}em atraso ({_eur(sum(f.valor for f in vencidas))}). '
                         f'Paga até {limite - timedelta(days=1):%d/%m/%Y} '
                         f'— a {limite:%d/%m/%Y} {"o módulo Serviços é suspenso" if serv else "a loja é suspensa"}.'}
    breve = [f for f in pend if (f.vencimento - d).days <= 3]
    if breve and not sub.auto_renovar:
        f = breve[0]
        quando_txt = 'hoje' if f.vencimento == d else f'a {f.vencimento:%d/%m/%Y}'
        return {'tipo': 'vence', 'suspensao_em': None, 'servicos': serv,
                'texto': f'A fatura da subscrição {"de Serviços " if serv else ""}({_eur(f.valor)}) vence {quando_txt}.'}
    return None


# ── Trocas pedidas pelo dono ──────────────────────────────────

DIAS_ENTRE_TROCAS = 90
MAX_PEDIDOS_DIA = 3
NOTA_PEDIDO_CANCELADO = 'Anulada: pedido de mudança cancelado'


def proxima_troca(loja):
    """Data a partir da qual o dono pode voltar a mudar de modelo (None = já pode)."""
    if not loja.modelo_alterado_em:
        return None
    livre = (loja.modelo_alterado_em + timedelta(days=DIAS_ENTRE_TROCAS)).date()
    return livre if livre > timezone.now().date() else None


def _exige_troca_livre(loja):
    livre = proxima_troca(loja)
    if livre:
        raise ErroFatura(f'Só podes mudar de modelo uma vez a cada 3 meses — a partir de {livre:%d/%m/%Y}.')


@transaction.atomic
def pedir_subscricao(loja, plano):
    """
    Loja em comissão pede para passar a subscrição: emite a 1.ª fatura (vence hoje). A loja
    continua em comissão até a pagar — aí a subscrição começa (ver pagar()). Sem período de teste.
    """
    Subscricao.objects.select_for_update().filter(loja_id=loja.pk).first()           # subscrição → loja
    loja = Loja.objects.select_for_update().get(pk=loja.pk)
    if loja.modelo_cobranca != 'comissao':
        raise ErroFatura('A loja já está em subscrição.')
    if loja.estado != 'ativa':
        raise ErroFatura('A loja tem de estar activa.')
    _exige_troca_livre(loja)
    # pedir e cancelar em ciclo só enche a lista de faturas anuladas
    cancelados = FaturaSubscricao.objects.filter(loja=loja, notas__startswith=NOTA_PEDIDO_CANCELADO,
                                                 data_criacao__gte=timezone.now() - timedelta(days=1)).count()
    if cancelados >= MAX_PEDIDOS_DIA:
        raise ErroFatura('Já pediste e cancelaste a mudança várias vezes hoje — tenta outra vez amanhã.')
    d = hoje()
    sub = Subscricao.objects.select_for_update().filter(loja=loja).first()
    if sub and sub.estado == 'aguarda':
        raise ErroFatura('Já tens um pedido de mudança — paga a fatura ou cancela o pedido.')
    if sub:
        sub.plano, sub.preco, sub.meses, sub.estado = plano, plano.preco, plano.meses, 'aguarda'
        sub.inicio, sub.pago_ate, sub.teste_ate, sub.fim_agendado, sub.plano_seguinte = d, d, None, None, None
        sub.save()
    else:
        sub = Subscricao.objects.create(loja=loja, plano=plano, preco=plano.preco, meses=plano.meses,
                                        estado='aguarda', inicio=d, pago_ate=d)
    f = emitir_fatura(sub, d)
    _marcar(f, 'emitida')
    return sub, f


@transaction.atomic
def cancelar_pedido(loja):
    sub = Subscricao.objects.select_for_update().filter(loja=loja, estado='aguarda').first()
    if not sub or loja.modelo_cobranca != 'comissao':
        raise ErroFatura('Não há nenhum pedido de mudança para cancelar.')
    sub.faturas.filter(estado='pendente').update(estado='anulada', notas=NOTA_PEDIDO_CANCELADO + '.')
    sub.estado = 'cancelada'
    sub.save(update_fields=['estado', 'data_atualizacao'])


@transaction.atomic
def agendar_comissao(loja):
    """Subscrição → comissão no fim do período pago (sem reembolso). Não com faturas em atraso."""
    sub = Subscricao.objects.select_for_update().filter(loja_id=loja.pk).first()     # subscrição → loja
    loja = Loja.objects.select_for_update().get(pk=loja.pk)
    if loja.modelo_cobranca != 'subscricao' or not sub or sub.estado not in ('teste', 'ativa', 'em_atraso'):
        raise ErroFatura('A loja não está numa subscrição activa.')
    if sub.fim_agendado:
        raise ErroFatura(f'Já está agendado: passa para comissão a {sub.fim_agendado:%d/%m/%Y}.')
    if sub.faturas.filter(estado='pendente', vencimento__lt=hoje()).exists():
        raise ErroFatura('Tens faturas em atraso — paga-as primeiro.')
    _exige_troca_livre(loja)
    sub.fim_agendado, sub.plano_seguinte = sub.pago_ate, None
    sub.save(update_fields=['fim_agendado', 'plano_seguinte', 'data_atualizacao'])
    # a renovação já emitida (ainda por pagar) deixa de fazer sentido
    sub.faturas.filter(estado='pendente', periodo_inicio__gte=sub.pago_ate).update(
        estado='anulada', notas='Anulada: a loja vai passar para comissão.')
    return sub


@transaction.atomic
def cancelar_agendamento(loja):
    sub = Subscricao.objects.select_for_update().filter(loja=loja).exclude(fim_agendado=None).first()
    if not sub:
        raise ErroFatura('Não há nenhuma mudança para comissão agendada.')
    sub.fim_agendado = None
    sub.save(update_fields=['fim_agendado', 'data_atualizacao'])   # o ciclo volta a emitir a renovação


@transaction.atomic
def mudar_plano(loja, plano):
    """
    Muda de plano a partir da renovação. Se a renovação já foi emitida e ainda está por pagar,
    é substituída já pelo plano novo (mantém o vencimento — não dá mais prazo).
    """
    sub = Subscricao.objects.select_for_update().filter(loja=loja, estado__in=['teste', 'ativa', 'em_atraso']).first()
    if not sub or loja.modelo_cobranca != 'subscricao':
        raise ErroFatura('A loja não está numa subscrição activa.')
    if sub.fim_agendado:
        raise ErroFatura('A loja vai passar para comissão — cancela isso primeiro.')
    return mudar_plano_sub(sub, plano)


def mudar_plano_sub(sub, plano):
    """O núcleo de mudar_plano (loja ou POS); `sub` já vem bloqueada, dentro de uma transacção."""
    if sub.estado not in ('teste', 'ativa', 'em_atraso'):
        raise ErroFatura('A subscrição não está activa.')
    if plano.id == sub.plano_id and not sub.plano_seguinte_id:
        raise ErroFatura('Já estás neste plano.')
    renovacao = sub.faturas.filter(estado='pendente', periodo_inicio=sub.pago_ate).first()
    if renovacao:
        renovacao.estado, renovacao.notas = 'anulada', f'Substituída: mudança para o plano {plano.nome}.'
        renovacao.save(update_fields=['estado', 'notas'])
        sub.plano, sub.preco, sub.meses, sub.plano_seguinte = plano, plano.preco, plano.meses, None
        sub.save()
        nova = emitir_fatura(sub, sub.pago_ate, vencimento=renovacao.vencimento)
        nova.avisos = list(renovacao.avisos or [])
        nova.save(update_fields=['avisos'])
        return sub, nova
    sub.plano_seguinte = None if plano.id == sub.plano_id else plano
    sub.save(update_fields=['plano_seguinte', 'data_atualizacao'])
    return sub, None


# ── Acções do admin ───────────────────────────────────────────

@transaction.atomic
def oferecer(sub, meses, motivo=''):
    """
    Oferece `meses` de serviço: as faturas por pagar do período actual/seguinte são anuladas e
    fica uma fatura de 0$00 (paga, "Oferta da plataforma") a cobrir esses meses.
    """
    sub = Subscricao.objects.select_for_update().get(pk=sub.pk)
    if sub.estado in ('aguarda', 'cancelada'):
        raise ErroFatura('Esta subscrição não está activa.')
    sub.faturas.filter(estado='pendente', periodo_inicio__gte=sub.pago_ate).update(
        estado='anulada', notas='Anulada: meses oferecidos pela plataforma.')
    if sub.coberta_por_id:
        raise ErroFatura('Este POS está incluído no plano da loja — oferece os meses à loja.')
    # POS sem plano com o período grátis acabado: o tempo sem plano não se cobrou, a oferta conta a partir de hoje
    inicio = sub.pago_ate if sub.plano_id else max(sub.pago_ate, hoje())
    fim = mais_meses(inicio, meses)
    f = FaturaSubscricao.objects.create(
        loja_id=sub.loja_id or sub.loja_servicos_id, pos_id=sub.pos_id, subscricao=sub, plano=sub.plano,
        descricao=f'Oferta — {_descricao(sub.plano, inicio, fim)}',
        periodo_inicio=inicio, periodo_fim=fim, valor=0, estado='paga', vencimento=inicio, paga_em=timezone.now(),
        metodo='oferta', notas=(motivo or 'Oferta da plataforma')[:300], avisos=['emitida'])
    sub.pago_ate = fim
    if not sub.plano_id:
        sub.avisos = []                      # os lembretes do fim do período grátis voltam a contar
    if sub.fim_agendado:
        sub.fim_agendado = fim
    sub.save()
    _reavaliar(sub)
    _avisar_dono(sub.alvo, f'A plataforma ofereceu-te {meses} mês(es) de subscrição',
                 f'Não pagas nada até {fim - timedelta(days=1):%d/%m/%Y}.' + (f' {motivo}' if motivo else ''))
    return f


@transaction.atomic
def adiar(fatura, dias):
    """Dá mais prazo a uma fatura por pagar (os avisos de atraso recomeçam a contar)."""
    Subscricao.objects.select_for_update().get(pk=fatura.subscricao_id)              # subscrição → fatura
    fatura = FaturaSubscricao.objects.select_for_update().get(pk=fatura.pk)
    if fatura.estado != 'pendente':
        raise ErroFatura('Só se adiam faturas por pagar.')
    fatura.vencimento = max(fatura.vencimento, hoje()) + timedelta(days=dias)
    fatura.avisos = [a for a in (fatura.avisos or []) if a in ('emitida',)]
    fatura.save(update_fields=['vencimento', 'avisos'])
    _reavaliar(fatura.subscricao)
    _avisar_dono(fatura.alvo, 'Tens mais prazo para pagar a subscrição',
                 f'{fatura.descricao}: vence agora a {fatura.vencimento:%d/%m/%Y}.')
    return fatura


@transaction.atomic
def anular(fatura, motivo):
    """Anula uma fatura por pagar (nunca se apaga). O ciclo volta a emitir a do período, se for preciso."""
    Subscricao.objects.select_for_update().get(pk=fatura.subscricao_id)              # subscrição → fatura
    fatura = FaturaSubscricao.objects.select_for_update().get(pk=fatura.pk)
    if fatura.estado != 'pendente':
        raise ErroFatura('Só se anulam faturas por pagar.')
    fatura.estado, fatura.notas = 'anulada', (f'Anulada: {motivo}' if motivo else 'Anulada pela plataforma.')[:300]
    fatura.save(update_fields=['estado', 'notas'])
    _reavaliar(fatura.subscricao)
    return fatura


# ── Resumo por período (admin) ────────────────────────────────

def resumo_periodo(inicio, fim):
    """Receita de subscrições (faturas pagas) e de comissões (registadas) entre duas datas (inclusive)."""
    from datetime import datetime, time
    from django.db.models import Count, Q, Sum
    from ..models import Comissao
    from .horarios import fuso
    tz = fuso()
    de = datetime.combine(inicio, time(0), tzinfo=tz)
    ate = datetime.combine(fim + timedelta(days=1), time(0), tzinfo=tz)
    pagas = FaturaSubscricao.objects.filter(estado='paga', paga_em__gte=de, paga_em__lt=ate)
    receita_sub = pagas.exclude(metodo='oferta').aggregate(v=Sum('valor'), n=Count('id'))
    por_plano = list(pagas.exclude(metodo='oferta').values('plano__nome').annotate(v=Sum('valor'), n=Count('id')).order_by('-v'))
    por_metodo = list(pagas.values('metodo').annotate(v=Sum('valor'), n=Count('id')).order_by('-n'))
    com = Comissao.objects.filter(data_criacao__gte=de, data_criacao__lt=ate).aggregate(
        v=Sum('valor_comissao'), n=Count('id'),
        liquidada=Sum('valor_comissao', filter=Q(status='liquidada')),
        pendente=Sum('valor_comissao', filter=Q(status='pendente')))
    d = hoje()
    pend = FaturaSubscricao.objects.filter(estado='pendente')
    atraso = pend.filter(vencimento__lt=d).aggregate(v=Sum('valor'), n=Count('id'))
    a_receber = pend.filter(vencimento__gte=max(inicio, d), vencimento__lte=fim).aggregate(v=Sum('valor'), n=Count('id'))
    lojas = Loja.objects.exclude(estado='pendente')
    zero = Decimal('0')
    d2 = lambda v: str((v or zero).quantize(Decimal('0.01')))         # sempre "0.00"
    metodos = dict(FaturaSubscricao.METODOS)
    return {
        'inicio': inicio.isoformat(), 'fim': fim.isoformat(),
        'subscricoes': {
            'valor': d2(receita_sub['v']), 'faturas': receita_sub['n'],
            'ofertas': pagas.filter(metodo='oferta').count(),
            'por_plano': [{'plano': x['plano__nome'], 'valor': d2(x['v']), 'faturas': x['n']} for x in por_plano],
            'por_metodo': [{'metodo': x['metodo'], 'nome': metodos.get(x['metodo'], x['metodo']),
                            'valor': d2(x['v']), 'faturas': x['n']} for x in por_metodo],
        },
        'comissoes': {'valor': d2(com['v']), 'encomendas': com['n'],
                      'liquidada': d2(com['liquidada']), 'pendente': d2(com['pendente'])},
        'total': d2((receita_sub['v'] or zero) + (com['v'] or zero)),
        'em_atraso': {'valor': d2(atraso['v']), 'faturas': atraso['n']},
        'a_receber': {'valor': d2(a_receber['v']), 'faturas': a_receber['n']},
        'lojas': {'comissao': lojas.filter(modelo_cobranca='comissao').count(),
                  'subscricao': lojas.filter(modelo_cobranca='subscricao').count()},
        'por_estado': dict(Subscricao.objects.filter(loja__modelo_cobranca='subscricao')
                           .values_list('estado').annotate(n=Count('id'))),
        # lojas vs POS: receita do período e como estão os POS hoje
        'por_alvo': {chave: {'valor': d2(x['v']), 'faturas': x['n']} for chave, x in (
            ('lojas', pagas.exclude(metodo='oferta').filter(loja__isnull=False, subscricao__loja_servicos__isnull=True)
             .aggregate(v=Sum('valor'), n=Count('id'))),
            ('servicos', pagas.exclude(metodo='oferta').filter(subscricao__loja_servicos__isnull=False)
             .aggregate(v=Sum('valor'), n=Count('id'))),
            ('pos', pagas.exclude(metodo='oferta').filter(pos__isnull=False).aggregate(v=Sum('valor'), n=Count('id'))))},
        'pos': _resumo_pos(),
    }


def _resumo_pos():
    from django.db.models import Count
    from ..pos.models import ConfiguracaoPOS
    s = Subscricao.objects.filter(pos__isnull=False)
    proprios = s.filter(coberta_por__isnull=True)
    return {'total': ConfiguracaoPOS.objects.count(),
            'incluidos': s.filter(coberta_por__isnull=False).count(),
            'sem_plano': proprios.filter(plano__isnull=True).count(),
            'suspensos': ConfiguracaoPOS.objects.filter(suspenso=True).count(),
            'por_estado': dict(proprios.values_list('estado').annotate(n=Count('id')))}


def plano_ativo(valor, tipos=TIPOS_LOJA):
    """
    O plano activo com este id (vindo do pedido) e de um destes tipos, ou None — nunca rebenta
    com lixo ('abc', None, listas). Uma loja não pode escolher um plano de POS e vice-versa.
    """
    try:
        pid = int(valor)
    except (TypeError, ValueError):
        return None
    return PlanoSubscricao.objects.filter(id=pid, ativo=True, tipo__in=tipos).first()
