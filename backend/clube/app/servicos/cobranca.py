"""
Quem pode usar o módulo Serviços e como se paga (doc "Serviços e Marcações — Fase 1", Cobrança).

- Loja em subscrição: Serviços incluídos, sem custo extra.
- Loja em comissão: paga a subscrição de Serviços (Subscricao.loja_servicos, planos tipo 'servicos');
  os produtos continuam por comissão. A 1.ª vez tem o período de teste da plataforma.
- Suspender a subscrição de Serviços só desliga o módulo (nunca a loja).
- A loja passa para subscrição → a de Serviços acaba no fim do período pago (sem reembolso).
  Passa para comissão → o módulo precisa de uma subscrição de Serviços para continuar.
O ciclo (faturas, avisos, carência) é o de utils/subscricoes.py.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from ..models import ConfiguracaoPlataforma, Loja, Subscricao, UtilizadorLoja
from ..utils import subscricoes as subs
from .models import ConfigServicos, Marcacao, Profissional

ESTADOS_COM_ACESSO = ('teste', 'ativa', 'em_atraso')
TEXTOS = {'o': 'o módulo Serviços', 'O': 'O módulo Serviços', 'suspenso': 'suspenso', 'reactivado': 'reactivado',
          'onde': 'Backoffice → Subscrição'}


class ErroServicos(Exception):
    pass


def config(loja):
    cfg, _ = ConfigServicos.objects.get_or_create(loja=loja)
    return cfg


def sub_servicos(loja):
    return Subscricao.objects.select_related('plano').filter(loja_servicos=loja).first()


def tem_acesso(loja, sub=None):
    """A loja tem direito ao módulo (independentemente de o ter ligado)."""
    if loja.modelo_cobranca == 'subscricao':
        return True
    sub = sub if sub is not None else sub_servicos(loja)
    return bool(sub) and sub.estado in ESTADOS_COM_ACESSO


def disponivel(loja):
    """O módulo está ligado e pago: aparece ao público e aceita marcações novas."""
    cfg = getattr(loja, 'config_servicos', None)
    return bool(cfg and cfg.ativo) and loja.estado == 'ativa' and tem_acesso(loja)


def limites(loja, sub=None):
    """{'marcacoes_mes', 'profissionais'} do plano de Serviços (None = sem limite)."""
    if loja.modelo_cobranca == 'subscricao':
        return {'marcacoes_mes': None, 'profissionais': None}
    sub = sub if sub is not None else sub_servicos(loja)
    plano = sub.plano if sub and sub.plano_id else None
    return {'marcacoes_mes': plano.limite_marcacoes_mes if plano else None,
            'profissionais': plano.limite_profissionais if plano else None}


def garantir_dono(loja):
    """O dono é o primeiro profissional (um negócio de uma pessoa não configura nada)."""
    if loja.profissionais.exists():
        return None
    membro = UtilizadorLoja.objects.filter(loja=loja, role='dono', ativo=True).select_related('utilizador').first()
    nome = (membro.utilizador.nome if membro else '') or loja.nome
    return Profissional.objects.create(loja=loja, nome=nome[:100],
                                       membro=membro if membro and not hasattr(membro, 'profissional') else None)


def _marcacoes_futuras(loja):
    return Marcacao.objects.filter(loja=loja, estado__in=Marcacao.ATIVOS, inicio__gte=timezone.now()).count()


@transaction.atomic
def ativar(loja, plano=None):
    """
    Liga o módulo. Em comissão: sem subscrição → cria-a (com teste na 1.ª vez; depois a 1.ª fatura
    vence hoje e o módulo só abre quando for paga). Devolve (cfg, fatura_por_pagar | None).
    """
    sub = Subscricao.objects.select_for_update().filter(loja_servicos=loja).first()    # subscrição → loja
    loja = Loja.objects.select_for_update().get(pk=loja.pk)
    cfg = config(loja)
    fatura = None
    if loja.modelo_cobranca == 'comissao':
        if loja.estado not in ('ativa', 'fechada'):
            raise ErroServicos('A loja tem de estar aprovada para activar os Serviços.')
        if sub and sub.estado == 'suspensa':
            raise ErroServicos('A subscrição de Serviços está suspensa — paga a fatura em atraso.')
        if sub and sub.estado in ESTADOS_COM_ACESSO:
            if sub.fim_agendado:                       # tinha desligado e volta antes de o período acabar
                sub.fim_agendado = None
                sub.save(update_fields=['fim_agendado', 'data_atualizacao'])
        elif sub and sub.estado == 'aguarda':
            fatura = sub.faturas.filter(estado='pendente').first()
        else:
            if plano is None:
                raise ErroServicos('Escolhe um plano de Serviços.')
            d = subs.hoje()
            dias = ConfiguracaoPlataforma.atual().subscricao_dias_teste if not sub else 0
            if sub:                                    # já teve (cancelada): sem novo teste
                sub.plano, sub.preco, sub.meses = plano, plano.preco, plano.meses
                sub.estado, sub.inicio, sub.pago_ate, sub.teste_ate = 'aguarda', d, d, None
                sub.fim_agendado, sub.plano_seguinte = None, None
                sub.save()
            else:
                sub = Subscricao.objects.create(
                    loja_servicos=loja, plano=plano, preco=plano.preco, meses=plano.meses,
                    estado='teste' if dias else 'aguarda', inicio=d, pago_ate=d + timedelta(days=dias),
                    teste_ate=d + timedelta(days=dias) if dias else None)
            f = subs.emitir_fatura(sub, sub.pago_ate)
            subs._marcar(f, 'emitida')
            sub.refresh_from_db()
            if f.estado == 'pendente':
                if sub.estado == 'aguarda':
                    fatura = f
                else:
                    subs._avisar_fatura(f, nova=True)
    cfg.ativo = True
    cfg.ativado_em = cfg.ativado_em or timezone.now()
    cfg.save(update_fields=['ativo', 'ativado_em', 'data_atualizacao'])
    garantir_dono(loja)
    return cfg, fatura


@transaction.atomic
def desativar(loja):
    """Desliga o módulo. A subscrição de Serviços acaba no fim do período pago (sem reembolso)."""
    sub = Subscricao.objects.select_for_update().filter(loja_servicos=loja).first()
    loja = Loja.objects.select_for_update().get(pk=loja.pk)
    n = _marcacoes_futuras(loja)
    if n:
        raise ErroServicos(f'Tens {n} marcação(ões) futura(s) — conclui-as ou cancela-as primeiro.')
    cfg = config(loja)
    cfg.ativo = False
    cfg.save(update_fields=['ativo', 'data_atualizacao'])
    if sub:
        _terminar(sub, 'Anulada: o módulo Serviços foi desligado.')
    return cfg


def _terminar(sub, nota):
    """Sem renovação: 'aguarda' cancela já; activa acaba no fim do período pago."""
    if sub.estado == 'aguarda':
        sub.faturas.filter(estado='pendente').update(estado='anulada', notas=nota)
        sub.estado = 'cancelada'
        sub.save(update_fields=['estado', 'data_atualizacao'])
    elif sub.estado in ESTADOS_COM_ACESSO and not sub.fim_agendado:
        sub.fim_agendado, sub.plano_seguinte = sub.pago_ate, None
        sub.save(update_fields=['fim_agendado', 'plano_seguinte', 'data_atualizacao'])
        sub.faturas.filter(estado='pendente', periodo_inicio__gte=sub.pago_ate).update(estado='anulada', notas=nota)


def loja_mudou_modelo(loja):
    """
    Chamado quando a loja muda de modelo (pagar o pedido, o fim agendado, o admin).
    Subscrição → a de Serviços deixa de ser precisa. Comissão → avisa se o módulo fica sem acesso.
    """
    sub = Subscricao.objects.select_for_update().filter(loja_servicos_id=loja.pk).first()
    if loja.modelo_cobranca == 'subscricao':
        if sub:
            # as faturas em atraso também deixam de ser devidas: os Serviços já vêm na subscrição
            sub.faturas.filter(estado='pendente', vencimento__lt=subs.hoje()).update(
                estado='anulada', notas='Anulada: os Serviços passaram a estar incluídos na subscrição da loja.')
            if sub.estado == 'suspensa':
                sub.estado = 'cancelada'
                sub.save(update_fields=['estado', 'data_atualizacao'])
            _terminar(sub, 'Anulada: os Serviços passaram a estar incluídos na subscrição da loja.')
        return
    cfg = getattr(loja, 'config_servicos', None)
    if cfg and cfg.ativo and not tem_acesso(loja, sub):
        subs._avisar_dono(loja, 'Os Serviços precisam de uma subscrição própria',
                          'A loja passou para comissão. Para continuar a receber marcações escolhe um plano de '
                          'Serviços em Backoffice → Subscrição. As marcações já confirmadas mantêm-se.')


def processar(sub, d, resumo):
    """Uma volta do ciclo para a subscrição de Serviços (worker, via subscricoes.processar)."""
    loja = sub.loja_servicos
    if loja.estado not in ('ativa', 'fechada'):
        return
    if loja.modelo_cobranca == 'subscricao' and not sub.fim_agendado:
        _terminar(sub, 'Anulada: os Serviços passaram a estar incluídos na subscrição da loja.')
    if sub.fim_agendado and d >= sub.fim_agendado:
        sub.faturas.filter(estado='pendente').update(estado='anulada', notas='Anulada: a subscrição de Serviços terminou.')
        sub.estado, sub.fim_agendado = 'cancelada', None
        sub.save(update_fields=['estado', 'fim_agendado', 'data_atualizacao'])
        if loja.modelo_cobranca == 'subscricao':
            subs._avisar_dono(loja, 'Os Serviços passaram a estar incluídos na subscrição da loja',
                              'A subscrição de Serviços terminou — não tens de a pagar mais.')
        else:
            subs._avisar_dono(loja, 'A subscrição de Serviços terminou',
                              'O módulo Serviços está desligado. Podes voltar a ligá-lo em Backoffice → Serviços.')
        return
    subs.ciclo_faturas(sub, loja, d, resumo)


def resumo(loja):
    """O estado do módulo para o backoffice."""
    sub = sub_servicos(loja)
    cfg = getattr(loja, 'config_servicos', None)
    pendente = sub.faturas.filter(estado='pendente').order_by('vencimento').first() if sub else None
    return {
        'ativo': bool(cfg and cfg.ativo),
        'incluido': loja.modelo_cobranca == 'subscricao',
        'acesso': tem_acesso(loja, sub),
        'disponivel': disponivel(loja),
        'subscricao': subs.subscricao_payload(sub) if sub and sub.estado != 'cancelada' else None,
        'fatura_pendente': subs.fatura_payload(pendente) if pendente else None,
        'ja_teve_teste': bool(sub),
        'dias_teste': ConfiguracaoPlataforma.atual().subscricao_dias_teste,
        'limites': limites(loja, sub),
        'planos': [subs.plano_payload(p) for p in subs.planos_ativos(('servicos',))]
        if loja.modelo_cobranca == 'comissao' else [],
    }
