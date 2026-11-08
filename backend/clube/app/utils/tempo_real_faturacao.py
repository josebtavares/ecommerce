"""
Tempo real da faturação das vendas (como utils/tempo_real_subscricoes.py): quando a fatura de uma venda é registada,
substituída ou anulada (utils/fiscal.py grava sempre fatura_numero/fatura_registada_em), ou quando uma venda passa
a faturável ou deixa de o ser (encomenda paga/cancelada, marcação concluída/falta paga, conta do POS fechada),
avisa pelo WebSocket das notificações (grupo notif_<user>):

• os admins com gerir_faturacao (Admin → Faturação: ficha, vendas, "por faturar" nas abas);
• quem gere a faturação da loja (Backoffice → Faturação: dono, gestor, contabilista);
• o dono do POS (POS → Faturação; a página do POS não tem WebSocket: verifica de tempos a tempos).

Só quando mudam os campos que contam para a faturação (não a cada gravação de uma encomenda) e só com ids
({origem, id, loja_id, pos_id}): a página aberta vai buscar o resto com as suas permissões. Depois do commit.
"""
from django.db import transaction
from django.db.models.signals import post_init, post_save

# campos que mudam o que a Faturação mostra (estado faturável, valor, fatura em vigor)
CAMPOS = {
    'loja':      ('status', 'valor_total', 'fatura_numero', 'fatura_registada_em', 'cliente_nif'),   # NIF: "NIF em falta"
    'marcacoes': ('estado', 'pago', 'preco_final', 'valor_pago', 'valor_reembolsado', 'fatura_numero', 'fatura_registada_em'),
    'pos':       ('status', 'total', 'gorjeta', 'loja_id', 'fatura_numero', 'fatura_registada_em'),
}


def _destinatarios(loja_id, pos_id):
    from ..models import Utilizador, UtilizadorLoja
    roles_admin = [k for k, v in Utilizador.PERMISSOES_ADMIN.items() if 'gerir_faturacao' in v]
    ids = set(Utilizador.objects.filter(user__is_staff=True, role_admin__in=roles_admin)
              .values_list('user_id', flat=True))
    if loja_id:
        roles = [k for k, v in UtilizadorLoja.PERMISSOES.items() if 'gerir_faturacao' in v]
        ids |= set(UtilizadorLoja.objects.filter(loja_id=loja_id, ativo=True, role__in=roles)
                   .values_list('utilizador__user_id', flat=True))
    if pos_id:
        from ..pos.models import ConfiguracaoPOS
        dono = ConfiguracaoPOS.objects.filter(pk=pos_id).values_list('dono__user_id', flat=True).first()
        if dono:
            ids.add(dono)
    ids.discard(None)
    return ids


def _enviar(aviso):
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        camada = get_channel_layer()
        if camada is None:
            return
        evento = {'type': 'faturacao.atualizada', 'faturacao': aviso}
        for uid in _destinatarios(aviso.get('loja_id'), aviso.get('pos_id')):
            async_to_sync(camada.group_send)(f'notif_{uid}', evento)
        if aviso.get('pos_id'):                  # quem está no POS (dono e equipa) — utils/tempo_real_pos.py
            from . import tempo_real_pos
            tempo_real_pos._enviar(aviso['pos_id'], [{'tipo': 'faturacao', 'id': aviso.get('id'), 'pos_id': aviso['pos_id']}])
    except Exception:
        pass        # sem Redis/WebSocket: as páginas actualizam ao voltar a abri-las


def emitir(origem, id_, loja_id=None, pos_id=None):
    """origem: 'loja' | 'marcacoes' | 'pos'. Avisa depois do commit (desfeita → não avisa)."""
    if not id_ or not (loja_id or pos_id):
        return
    aviso = {'origem': origem, 'id': id_, 'loja_id': loja_id, 'pos_id': pos_id}
    transaction.on_commit(lambda: _enviar(aviso))
    from . import tempo_real_painel             # as vendas também mudam o Dashboard e os Relatórios
    tempo_real_painel.emitir('venda')


def _foto(origem, obj):
    # __dict__ e não getattr: num objecto carregado com .only()/.defer() o getattr de um campo adiado iria à base
    # de dados (uma consulta por linha de cada lista — e o refresh cria outro objecto, que voltava a passar aqui)
    d = obj.__dict__
    return tuple(d.get(c) for c in CAMPOS[origem])


def _ligar(origem, modelo, alvo, faturavel_ao_criar):
    def ao_iniciar(sender, instance, **kwargs):
        instance._faturacao_antes = _foto(origem, instance) if instance.pk else None

    def ao_gravar(sender, instance, created=False, raw=False, **kwargs):
        if raw:
            return
        antes = getattr(instance, '_faturacao_antes', None)
        agora = _foto(origem, instance)
        instance._faturacao_antes = agora
        if created or antes is None:
            if not faturavel_ao_criar(instance):
                return
        elif antes == agora:
            return
        emitir(origem, instance.pk, *alvo(instance))

    post_init.connect(ao_iniciar, sender=modelo, weak=False, dispatch_uid=f'faturacao_init_{modelo.__name__}')
    post_save.connect(ao_gravar, sender=modelo, weak=False, dispatch_uid=f'faturacao_{modelo.__name__}')


def ligar():
    from ..models import Encomenda
    from ..pos.models import ContaMesa
    from ..servicos.models import Marcacao
    from . import fiscal
    _ligar('loja', Encomenda, lambda e: (e.loja_id, None), lambda e: e.status in fiscal.ESTADOS_FATURAVEIS)
    _ligar('marcacoes', Marcacao, lambda m: (m.loja_id, None), lambda m: m.estado in ('concluida', 'falta', 'cancelada'))
    _ligar('pos', ContaMesa, lambda c: (c.loja_id, c.pos_id), lambda c: c.status == 'fechada')
