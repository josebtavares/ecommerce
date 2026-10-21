"""
Operações sobre marcações (backoffice — etapa 2; o cliente usa as mesmas na etapa 3).

Concorrência: as operações bloqueiam a linha do(s) profissional(is) envolvidos antes de verificar
a agenda, e a restrição de exclusão da base de dados é a última barreira (IntegrityError →
"já está ocupado"). Nunca se apaga uma marcação: cancela-se.
"""
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from ..utils.dinheiro import formatar
from ..utils.horarios import fuso
from . import cobranca
from .agenda import Indisponivel, verificar
from .models import Marcacao, Profissional, ReatribuicaoMarcacao


class ErroMarcacao(Exception):
    pass


def quando_texto(dt):
    return dt.astimezone(fuso()).strftime('%d/%m às %H:%M')


def _bloquear(*profs):
    ids = sorted({p.id for p in profs if p})
    return {p.id: p for p in Profissional.objects.select_for_update().filter(id__in=ids)}


def _limite_mes(loja, inicio, excluir=None):
    lim = cobranca.limites(loja)['marcacoes_mes']
    if not lim:
        return
    local = inicio.astimezone(fuso())
    de = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ate = (de + timedelta(days=32)).replace(day=1)
    qs = Marcacao.objects.filter(loja=loja, inicio__gte=de, inicio__lt=ate).exclude(estado__in=('cancelada', 'expirada'))
    if excluir:
        qs = qs.exclude(pk=excluir)
    if qs.count() >= lim:
        raise ErroMarcacao(f'O teu plano de Serviços inclui até {lim} marcações por mês — já chegaste ao limite em '
                           f'{local:%m/%Y}. Muda de plano em Subscrição.')


def exige_disponivel(loja):
    cfg = getattr(loja, 'config_servicos', None)
    if not (cfg and cfg.ativo):
        raise ErroMarcacao('O módulo Serviços está desligado.')
    if not cobranca.tem_acesso(loja):
        raise ErroMarcacao('As marcações novas estão paradas: a subscrição de Serviços está por pagar.')


def _avisar(m, titulo, mensagem, cliente=True, profissional=True, excluir_user=None):
    from ..Views.notificacaoView import notificar
    if cliente and m.cliente_id and m.cliente_id != excluir_user:
        notificar(utilizador=m.cliente, tipo='marcacao_atualizada', titulo=titulo, mensagem=mensagem,
                  loja=m.loja, link='/minhas-marcacoes')
    prof = m.profissional
    if profissional and prof.membro_id and prof.membro.ativo and prof.membro.utilizador_id != excluir_user:
        notificar(utilizador=prof.membro.utilizador, tipo='marcacao_atualizada', titulo=titulo, mensagem=mensagem,
                  loja=m.loja, link=f'/loja/{m.loja_id}/backoffice?seccao=servicos')


def _escolher(servico, inicio, ocupado_ate, ignorar_horario):
    """'Qualquer um': o primeiro profissional do serviço livre a essa hora (o com menos marcações nesse dia)."""
    profs = list(servico.profissionais.filter(ativo=True))
    if not profs:
        raise ErroMarcacao('Este serviço ainda não tem profissionais.')
    _bloquear(*profs)
    dia = inicio.astimezone(fuso()).date()
    carga = {p.id: Marcacao.objects.filter(profissional=p, estado__in=Marcacao.ATIVOS,
                                           inicio__date=dia).count() for p in profs}
    for p in sorted(profs, key=lambda x: (carga[x.id], x.ordem, x.id)):
        try:
            verificar(p, inicio, ocupado_ate, ignorar_horario)
            return p
        except Indisponivel:
            continue
    raise ErroMarcacao('Não há nenhum profissional livre a essa hora.')


@transaction.atomic
def criar(loja, servico, inicio, profissional=None, *, cliente=None, cliente_nome='', cliente_telefone='',
          notas_cliente='', notas_internas='', preco=None, estado='confirmada', pagamento='local',
          ignorar_horario=False, por='', expira_em=None):
    exige_disponivel(loja)
    if servico.loja_id != loja.id or not servico.ativo:
        raise ErroMarcacao('Serviço inválido.')
    fim = inicio + timedelta(minutes=servico.duracao_min)
    ocupado_ate = fim + timedelta(minutes=servico.intervalo_min)
    _limite_mes(loja, inicio)
    if profissional is None:
        profissional = _escolher(servico, inicio, ocupado_ate, ignorar_horario)
    else:
        if profissional.loja_id != loja.id or not profissional.ativo:
            raise ErroMarcacao('Profissional inválido.')
        _bloquear(profissional)
        try:
            verificar(profissional, inicio, ocupado_ate, ignorar_horario)
        except Indisponivel as e:
            raise ErroMarcacao(str(e))
    try:
        with transaction.atomic():
            m = Marcacao.objects.create(
                loja=loja, servico=servico, profissional=profissional, cliente=cliente,
                cliente_nome=cliente_nome[:120], cliente_telefone=cliente_telefone[:30],
                servico_nome=servico.nome, duracao_min=servico.duracao_min, tipo_preco=servico.tipo_preco,
                inicio=inicio, fim=fim, ocupado_ate=ocupado_ate, estado=estado,
                preco_indicado=servico.preco if preco is None else preco, pagamento=pagamento,
                notas_cliente=notas_cliente[:500], notas_internas=notas_internas[:500], criada_por=por[:100],
                expira_em=expira_em)
    except IntegrityError:
        raise ErroMarcacao(f'{profissional.nome} já está ocupado(a) a essa hora.')
    return m


def _exige_ativa(m):
    if m.estado not in Marcacao.ATIVOS:
        raise ErroMarcacao(f'Esta marcação está {m.get_estado_display().lower()} — já não se pode mudar.')


@transaction.atomic
def remarcar(m, inicio, por='', motivo='', ignorar_horario=False):
    m = Marcacao.objects.select_for_update().select_related('profissional', 'loja').get(pk=m.pk)
    _exige_ativa(m)
    _bloquear(m.profissional)
    duracao = m.fim - m.inicio
    extra = m.ocupado_ate - m.fim
    if m.inicio.astimezone(fuso()).strftime('%Y-%m') != inicio.astimezone(fuso()).strftime('%Y-%m'):
        _limite_mes(m.loja, inicio, excluir=m.pk)
    try:
        verificar(m.profissional, inicio, inicio + duracao + extra, ignorar_horario, excluir=m.pk)
    except Indisponivel as e:
        raise ErroMarcacao(str(e))
    antes = m.inicio
    m.inicio, m.fim, m.ocupado_ate = inicio, inicio + duracao, inicio + duracao + extra
    try:
        with transaction.atomic():
            m.save(update_fields=['inicio', 'fim', 'ocupado_ate', 'data_atualizacao'])
    except IntegrityError:
        raise ErroMarcacao(f'{m.profissional.nome} já está ocupado(a) a essa hora.')
    nota = f'{m.servico_nome}: passou de {quando_texto(antes)} para {quando_texto(inicio)}.' + (f' {motivo}' if motivo else '')
    _avisar(m, 'Marcação remarcada', nota)
    return m


@transaction.atomic
def reatribuir(m, novo, por='', motivo='', ignorar_horario=False):
    """
    Passa a marcação para outro profissional da loja (mesmo que o cliente tenha escolhido um).
    Avisa se o profissional não faz este serviço (aviso, não erro); a sobreposição é sempre recusada.
    Devolve (marcacao, avisos).
    """
    m = Marcacao.objects.select_for_update().select_related('profissional', 'loja', 'servico').get(pk=m.pk)
    _exige_ativa(m)
    if novo.loja_id != m.loja_id or not novo.ativo:
        raise ErroMarcacao('Profissional inválido.')
    if novo.id == m.profissional_id:
        raise ErroMarcacao('A marcação já é deste profissional.')
    _bloquear(m.profissional, novo)
    try:
        verificar(novo, m.inicio, m.ocupado_ate, ignorar_horario)
    except Indisponivel as e:
        raise ErroMarcacao(str(e))
    avisos = []
    if not m.servico.profissionais.filter(pk=novo.pk).exists():
        avisos.append(f'{novo.nome} não está associado(a) ao serviço "{m.servico_nome}".')
    antigo = m.profissional
    m.profissional = novo
    try:
        with transaction.atomic():
            m.save(update_fields=['profissional', 'data_atualizacao'])
    except IntegrityError:
        raise ErroMarcacao(f'{novo.nome} já está ocupado(a) a essa hora.')
    ReatribuicaoMarcacao.objects.create(marcacao=m, de=antigo, para=novo, por=por[:100], motivo=motivo[:200])
    texto = f'{m.servico_nome} a {quando_texto(m.inicio)}: agora com {novo.nome}.'
    _avisar(m, 'Mudámos o profissional da tua marcação', texto, profissional=False)
    from ..Views.notificacaoView import notificar
    for p, t in ((antigo, f'Já não tens a marcação {m.servico_nome} a {quando_texto(m.inicio)} (passou para {novo.nome}).'),
                 (novo, f'Nova marcação: {m.servico_nome} a {quando_texto(m.inicio)}.')):
        if p.membro_id and p.membro.ativo:
            notificar(utilizador=p.membro.utilizador, tipo='marcacao_atualizada', titulo='Agenda alterada', mensagem=t,
                      loja=m.loja, link=f'/loja/{m.loja_id}/backoffice?seccao=servicos')
    return m, avisos


@transaction.atomic
def confirmar(m, por=''):
    m = Marcacao.objects.select_for_update().get(pk=m.pk)
    if m.estado != 'pendente':
        raise ErroMarcacao('Só se confirmam marcações pendentes.')
    if m.pagamento == 'antecipado' and not m.pago:
        raise ErroMarcacao('Esta marcação ainda não foi paga.')
    m.estado, m.expira_em = 'confirmada', None
    m.save(update_fields=['estado', 'expira_em', 'data_atualizacao'])
    _avisar(m, 'Marcação confirmada', f'{m.servico_nome} a {quando_texto(m.inicio)} com {m.profissional.nome}.', profissional=False)
    return m


@transaction.atomic
def cancelar(m, por='', motivo='', pela_loja=True):
    m = Marcacao.objects.select_for_update().get(pk=m.pk)
    _exige_ativa(m)
    m.estado, m.cancelada_em = 'cancelada', timezone.now()
    m.cancelada_por, m.cancelada_motivo = por[:100], motivo[:200]
    m.save(update_fields=['estado', 'cancelada_em', 'cancelada_por', 'cancelada_motivo', 'data_atualizacao'])
    if pela_loja:
        _avisar(m, 'A loja cancelou a tua marcação',
                f'{m.servico_nome} a {quando_texto(m.inicio)}.' + (f' Motivo: {motivo}' if motivo else ''), profissional=True)
    return m


def marcacao_payload(m, completo=False):
    tz = fuso()
    d = {
        'id': m.id, 'servico_id': m.servico_id, 'servico_nome': m.servico_nome, 'duracao_min': m.duracao_min,
        'profissional_id': m.profissional_id, 'profissional_nome': m.profissional.nome,
        'cliente_id': m.cliente_id,
        'cliente_nome': (m.cliente.nome if m.cliente_id else '') or m.cliente_nome,
        'cliente_telefone': (getattr(m.cliente, 'telefone', '') if m.cliente_id else '') or m.cliente_telefone,
        'inicio': m.inicio.astimezone(tz).isoformat(), 'fim': m.fim.astimezone(tz).isoformat(),
        'ocupado_ate': m.ocupado_ate.astimezone(tz).isoformat(),
        'estado': m.estado, 'estado_nome': m.get_estado_display(),
        'tipo_preco': m.tipo_preco, 'preco_indicado': str(m.preco_indicado),
        'preco_final': str(m.preco_final) if m.preco_final is not None else None,
        'preco_texto': ('a partir de ' if m.tipo_preco == 'a_partir' and m.preco_final is None else '') + formatar(m.preco),
        'pagamento': m.pagamento, 'pago': m.pago,
        'notas_cliente': m.notas_cliente, 'notas_internas': m.notas_internas, 'criada_por': m.criada_por,
        'cancelada_por': m.cancelada_por, 'cancelada_motivo': m.cancelada_motivo,
    }
    if completo:
        d['reatribuicoes'] = [{'de': r.de.nome, 'para': r.para.nome, 'por': r.por, 'motivo': r.motivo,
                               'em': r.data_criacao.astimezone(tz).isoformat()}
                              for r in m.reatribuicoes.select_related('de', 'para')]
        d['criada_em'] = m.data_criacao.astimezone(tz).isoformat()
    return d
