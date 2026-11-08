"""
Tempo real do POS: quem está no POS (dono, membros da equipa, admin a ver) recebe pelo WebSocket ws/pos/ (grupo
pos_<id>) um aviso quando algo muda — mesa aberta/fechada, conta (itens, cozinha, pagamento, cancelamento),
turno de caixa, produtos/stock, equipa (permissões, desactivação), definições/suspensão do POS, faturas e
mensalidades (utils/tempo_real_faturacao.py e tempo_real_subscricoes.py também avisam aqui).

Só leva ids ({tipo, id, ...}): cada aba vai buscar o resto com as suas permissões. Depois do commit; numa
transacção que grava muitas linhas (fechar uma conta grava a conta, os itens, os pagamentos e a mesa) sai um só
aviso por (tipo, id).
"""
from django.db import transaction
from django.db.models.signals import post_delete, post_save


def grupo(pos_id):
    return f'pos_{pos_id}'


def _enviar(pos_id, avisos):
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        camada = get_channel_layer()
        if camada is None:
            return
        async_to_sync(camada.group_send)(grupo(pos_id), {'type': 'pos.evento', 'avisos': avisos})
    except Exception:
        pass        # sem Redis/WebSocket: as abas do POS verificam sozinhas de tempos a tempos


def emitir(pos_id, tipo, id_=None, **extra):
    """tipo: 'mesa' | 'conta' | 'turno' | 'produto' | 'equipa' | 'pos' | 'faturacao' | 'subscricao'."""
    if not pos_id:
        return
    aviso = {'tipo': tipo, 'id': id_, **extra}
    ligacao = transaction.get_connection()
    if not ligacao.in_atomic_block:
        _enviar(pos_id, [aviso])
        return
    # junta os avisos da transacção: um só envio por POS, sem repetir (tipo, id). Se a transacção (ou o
    # savepoint onde o envio foi marcado) for desfeita, o Django tira o _enviar_pendentes da lista do commit:
    # os avisos guardados até aí são deitados fora e começa-se de novo.
    # (Um aviso marcado num savepoint desfeito dentro de uma transacção que segue pode ainda sair: só faz a aba
    # recarregar sem mudança — inofensivo.)
    if not any(f is _enviar_pendentes for _, f, _ in ligacao.run_on_commit):
        ligacao._pos_tempo_real = {}
        transaction.on_commit(_enviar_pendentes)
    ligacao._pos_tempo_real.setdefault(pos_id, {})[(tipo, id_)] = aviso


def _enviar_pendentes():
    juntos = transaction.get_connection().__dict__.pop('_pos_tempo_real', None) or {}
    for pos_id, avisos in juntos.items():
        _enviar(pos_id, list(avisos.values()))


def _ao_mudar(tipo, pos_de, id_de=lambda o: o.pk, extra=lambda o: {}):
    def sinal(sender, instance, raw=False, **kwargs):
        if raw:
            return
        try:
            pos_id = pos_de(instance)
        except Exception:
            return
        if pos_id:
            emitir(pos_id, tipo, id_de(instance), **extra(instance))
    return sinal


def _ligar(modelo, sinal, nome):
    post_save.connect(sinal, sender=modelo, weak=False, dispatch_uid=f'pos_tr_save_{nome}')
    post_delete.connect(sinal, sender=modelo, weak=False, dispatch_uid=f'pos_tr_delete_{nome}')


def _pos_da_loja(loja_id):
    from ..pos.models import ConfiguracaoPOS
    if not loja_id:
        return []
    return list(ConfiguracaoPOS.objects.filter(loja_vinculada_id=loja_id).values_list('id', flat=True))


def _produto_loja(sender, instance, raw=False, **kwargs):
    # produto da loja ligada (preço, stock, variantes): os POS ligados a essa loja vendem-no
    if raw:
        return
    try:
        loja_id = instance.loja_id if hasattr(instance, 'loja_id') else instance.produto.loja_id
        produto_id = instance.pk if sender.__name__ == 'Produto' else instance.produto_id
    except Exception:
        return
    for pos_id in _pos_da_loja(loja_id):
        emitir(pos_id, 'produto', produto_id, origem='loja')


def ligar():
    from ..models import Produto, Inventario, VarianteProduto
    from ..pos import models as m

    conta = lambda c: {'mesa_id': c.mesa_id, 'status': c.status}
    _ligar(m.Mesa, _ao_mudar('mesa', lambda o: o.pos_id), 'mesa')
    _ligar(m.ContaMesa, _ao_mudar('conta', lambda o: o.pos_id, extra=conta), 'conta')
    _ligar(m.ItemContaMesa, _ao_mudar('conta', lambda o: o.conta.pos_id, id_de=lambda o: o.conta_id,
                                      extra=lambda o: conta(o.conta)), 'item')
    _ligar(m.PagamentoDividido, _ao_mudar('conta', lambda o: o.conta.pos_id, id_de=lambda o: o.conta_id,
                                          extra=lambda o: conta(o.conta)), 'pagamento')
    _ligar(m.TurnoPOS, _ao_mudar('turno', lambda o: o.pos_id), 'turno')
    _ligar(m.UtilizadorPOS, _ao_mudar('equipa', lambda o: o.pos_id), 'equipa')
    _ligar(m.ConfiguracaoPOS, _ao_mudar('pos', lambda o: o.pk), 'pos')
    _ligar(m.ProdutoPOS, _ao_mudar('produto', lambda o: o.pos_id), 'produto')
    _ligar(m.VarianteProdutoPOS, _ao_mudar('produto', lambda o: o.produto.pos_id, id_de=lambda o: o.produto_id),
           'variante')
    for modelo in (m.ComponenteConjuntoPOS, m.GrupoEscolhaPOS):
        _ligar(modelo, _ao_mudar('produto', lambda o: o.conjunto.pos_id, id_de=lambda o: o.conjunto_id),
               modelo.__name__)
    _ligar(m.OpcaoEscolhaPOS, _ao_mudar('produto', lambda o: o.grupo.conjunto.pos_id,
                                        id_de=lambda o: o.grupo.conjunto_id), 'opcao')
    for modelo in (Produto, Inventario, VarianteProduto):
        post_save.connect(_produto_loja, sender=modelo, weak=False, dispatch_uid=f'pos_tr_loja_{modelo.__name__}')
