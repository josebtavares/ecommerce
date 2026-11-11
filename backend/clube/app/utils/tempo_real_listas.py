"""
Tempo real das listas que ainda só se actualizavam ao recarregar:

• backoffice — Produtos e Inventário (o stock muda com as vendas no site, no POS, nas devoluções…): avisa os
  membros activos da loja;
• admin — Lojas, Produtos, Catálogo, Encomendas, Utilizadores, POS e Denúncias: avisa os admins com a permissão
  dessa secção.

Pelo WebSocket das notificações (grupo notif_<user>), só com {origem, loja_id}: a página aberta espera um pouco
(juntam-se vários avisos seguidos) e recarrega em silêncio, com as suas permissões. Vários avisos iguais na mesma
transacção (ex.: uma encomenda com 5 produtos baixa 5 stocks) saem como um só, depois do commit — se a transacção
for desfeita não se avisa.
"""
from django.db import transaction
from django.db.models.signals import post_delete, post_save

# origem → permissão de admin que vê essa lista (None = só a loja)
ADMIN = {
    'produto':    ('gerir_produtos', 'gerir_lojas'),      # Admin → Produtos e Catálogo
    'inventario': (),
    'loja':       ('gerir_lojas', 'gerir_produtos'),      # Admin → Lojas e Catálogo
    'utilizador': ('gerir_utilizadores',),
    'pos':        ('ver_pos',),
    'encomenda':  ('gerir_encomendas',),
    'denuncia':   ('moderar_chat',),
    'cartao':     (),                                     # o admin já recebe pelo painel (tempo_real_painel)
}
# também para a equipa da loja (e o dono): 'loja' = dados da loja, documentos e adesão vinti4 — a secção
# "Pagamento com cartão (vinti4)" e os Documentos das Configurações recarregam sozinhos
# 'cartao' = backoffice → Pagamentos: transacções vinti4 da loja e ficheiros VBVT do contrato dela
DA_LOJA = ('produto', 'inventario', 'loja', 'cartao')


def _admins(permissoes):
    from ..models import Utilizador
    roles = [r for r, perms in Utilizador.PERMISSOES_ADMIN.items() if any(p in perms for p in permissoes)]
    return set(Utilizador.objects.filter(user__is_staff=True, user__is_active=True, role_admin__in=roles)
               .values_list('user_id', flat=True))


def _enviar(itens):
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from ..models import Loja, UtilizadorLoja
        camada = get_channel_layer()
        if camada is None:
            return
        admins = {}
        for origem, loja_id in itens:
            ids = set()
            perms = ADMIN.get(origem) or ()
            if perms:
                if perms not in admins:
                    admins[perms] = _admins(perms)
                ids |= admins[perms]
            if origem in DA_LOJA and loja_id:
                ids |= set(UtilizadorLoja.objects.filter(loja_id=loja_id, ativo=True)
                           .values_list('utilizador__user_id', flat=True))
                ids |= {u for u in Loja.objects.filter(pk=loja_id).values_list('dono__user_id', flat=True) if u}
            evento = {'type': 'lista.atualizada', 'lista': {'origem': origem, 'loja_id': loja_id}}
            for uid in ids:
                async_to_sync(camada.group_send)(f'notif_{uid}', evento)
    except Exception:
        pass        # sem Redis/WebSocket: as páginas verificam sozinhas de tempos a tempos


def emitir(origem, loja_id=None):
    """Junta os avisos da transacção em curso e envia-os uma vez, depois do commit."""
    con = transaction.get_connection()
    pend = getattr(con, '_bendi_listas', None)
    # a transacção anterior foi desfeita (o callback já não está na fila): começa de novo
    if pend is None or not any(f is pend['fn'] for _, f, *_ in con.run_on_commit):
        pend = {'itens': {(origem, loja_id)}}

        def fn():
            con._bendi_listas = None
            _enviar(pend['itens'])
        pend['fn'] = fn
        con._bendi_listas = pend
        transaction.on_commit(fn)        # fora de uma transacção corre já
        return
    pend['itens'].add((origem, loja_id))


def _ao_mudar(origem, loja_de=lambda o: getattr(o, 'loja_id', None), so_campos=None):
    """so_campos: numa gravação com update_fields, só avisa se mudar um destes (gravações frequentes)."""
    def handler(sender, instance, created=False, raw=False, update_fields=None, **kwargs):
        if raw:
            return
        if so_campos and not created and update_fields is not None and not (set(update_fields) & so_campos):
            return
        try:
            emitir(origem, loja_de(instance))
        except Exception:
            pass
    return handler


def ligar():
    from django.contrib.auth.models import User
    from ..models import (AdesaoVinti4, DocumentoLoja, Encomenda, FicheiroVBVT, Inventario, Loja, Produto,
                          Reembolso, TransacaoVinti4, Utilizador, VarianteProduto)
    from ..chat.models import Denuncia
    from ..pos.models import ConfiguracaoPOS, ContaMesa

    def ligar_modelo(origem, modelo, **kw):
        h = _ao_mudar(origem, **kw)
        post_save.connect(h, sender=modelo, weak=False, dispatch_uid=f'listas_{modelo.__name__}_s')
        post_delete.connect(h, sender=modelo, weak=False, dispatch_uid=f'listas_{modelo.__name__}_d')

    ligar_modelo('produto', Produto)
    ligar_modelo('inventario', Inventario)
    ligar_modelo('inventario', VarianteProduto,          # stock por variação
                 loja_de=lambda o: Produto.objects.filter(pk=o.produto_id).values_list('loja_id', flat=True).first())
    ligar_modelo('loja', Loja, loja_de=lambda o: o.pk)
    ligar_modelo('loja', DocumentoLoja)              # envio / aprovação / recusa dos documentos
    ligar_modelo('loja', AdesaoVinti4)               # pedido, credenciais e decisões da Bendi
    ligar_modelo('utilizador', Utilizador, loja_de=lambda o: None)
    # o login grava só o last_login: não conta
    ligar_modelo('utilizador', User, loja_de=lambda o: None,
                 so_campos={'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff'})
    ligar_modelo('encomenda', Encomenda, so_campos={'status', 'valor_total'})
    ligar_modelo('denuncia', Denuncia, loja_de=lambda o: None)
    ligar_modelo('pos', ConfiguracaoPOS, loja_de=lambda o: None)
    ligar_modelo('pos', ContaMesa, loja_de=lambda o: None, so_campos={'status'})
    # só o que se vê na lista (estado, VBVT, estorno) — as respostas e consultas gravadas não avisam
    ligar_modelo('cartao', TransacaoVinti4, so_campos={'estado', 'reconciliada_em', 'estornada_em'})

    def loja_do_ficheiro(f):
        from ..pagamentos.vbvt import lojas_do_mid
        return f.loja_id or next(iter(lojas_do_mid(f.merchant_id)), None)
    ligar_modelo('cartao', FicheiroVBVT, loja_de=loja_do_ficheiro)

    def loja_se_cartao(r):
        """Pedido de reembolso de uma encomenda paga com cartão vinti4: a ficha da transacção mostra-o."""
        if TransacaoVinti4.objects.filter(referencia__startswith=f'enc-{r.encomenda_id}-', estado='paga').exists():
            return r.loja_id
        return None
    ligar_modelo('cartao', Reembolso, loja_de=loja_se_cartao, so_campos={'estado', 'referencia', 'data_reembolso', 'entregue_em',
                                                                      'devolvido_como', 'confirmado_sisp_em'})
