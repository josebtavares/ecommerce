"""
Envio por transportadora — a loja manda a encomenda pelos correios/transportadora e indica o código de rastreio.

Regras (decididas com o dono, 2026-11-12):
- Só Cabo Verde. Cada OpcaoEntrega 'envio' tem preço fixo e as ilhas onde serve (OpcaoEntrega.ilhas).
- Só com pagamento antecipado: cartão pago ou transferência confirmada. Dinheiro nunca vai por transportadora.
- A loja indica a transportadora (lista do admin ou "Outra"), 1+ códigos (volumes) e, se quiser, a foto do talão.
  A encomenda passa a "enviado" e a Entrega (tipo 'envio', sem condutor) fica 'a_caminho'.
- Os códigos podem ser corrigidos enquanto está a caminho (fica no histórico e o cliente é avisado de novo).
- Fecha-se como as outras: a loja conclui (ou, na fase 2/3, o cliente "Recebi" / fecho automático aos 10 dias).
- Devolvida pela transportadora → a encomenda volta a "em preparação": a loja reenvia (novo código, sem pagar de
  novo) ou cancela (stock e reembolso pelo caminho normal do cancelamento).
- Depois de enviada não se cancela (a loja marca primeiro como devolvida).
"""
from django.utils import timezone

from . import fila_emails as FE

MSG_SEM_DINHEIRO = ('O envio por transportadora só aceita pagamento antecipado (cartão ou transferência). '
                    'Escolhe outro método de pagamento.')
CODIGO_MAX = 60
CODIGOS_MAX = 10
NOTA_MAX = 200
OUTRA_MAX = 80


class ErroEnvio(Exception):
    pass


# ── transportadoras ────────────────────────────────────────────────────────────

def link_rastreio(url_rastreio, codigo):
    """O link da transportadora para este código ('' se ela não tem rastreio online)."""
    from urllib.parse import quote
    if not url_rastreio or '{codigo}' not in url_rastreio or not codigo:
        return ''
    return url_rastreio.replace('{codigo}', quote(str(codigo), safe=''))


def validar_url(url):
    url = (url or '').strip()
    if not url:
        return ''
    if not url.startswith('https://') or '{codigo}' not in url or len(url) > 300:
        raise ErroEnvio('O link de rastreio tem de começar por https:// e ter {codigo} no sítio do código.')
    return url


# ── opções de entrega ──────────────────────────────────────────────────────────

def limpar_ilhas(valor):
    """Lista de ilhas válidas, sem repetidas, pela ordem de geografia.ILHAS."""
    from .geografia import ILHAS
    if valor in (None, ''):
        return []
    if isinstance(valor, str):
        import json
        try:
            valor = json.loads(valor)
        except ValueError:
            valor = [valor]
    if not isinstance(valor, (list, tuple)):
        raise ErroEnvio('Ilhas inválidas.')
    pedidas = {str(v).strip() for v in valor}
    erradas = pedidas - set(ILHAS)
    if erradas:
        raise ErroEnvio(f'Ilha desconhecida: {", ".join(sorted(erradas))}.')
    return [i for i in ILHAS if i in pedidas]


def serve_ilha(opcao, ilha):
    """A opção serve esta ilha? (sem ilhas = todas; sem ilha do cliente = não se sabe → só as que servem todas)"""
    if not opcao.ilhas:
        return True
    return bool(ilha) and ilha in opcao.ilhas


def nome_transportadora(transportadora, outra):
    return transportadora.nome if transportadora else (outra or '').strip()[:OUTRA_MAX]


def validar_checkout(opcao, concelho, metodo=None, agendada=False):
    """Entrega ao domicílio no checkout → (concelho limpo, mensagem de erro ou None).
    O concelho é obrigatório; a opção tem de servir a ilha; o envio não aceita dinheiro nem hora marcada."""
    from .geografia import concelho as achar, ilha
    codigo = str(concelho or '').strip().upper()
    if not achar(codigo):
        return '', 'Escolhe o concelho da morada de entrega.'
    if opcao and not serve_ilha(opcao, ilha(codigo)):
        return codigo, f'A opção "{opcao.nome}" não entrega em {ilha(codigo)}. Escolhe outra opção de entrega.'
    if opcao and opcao.tipo == 'envio':
        if metodo == 'dinheiro':
            return codigo, MSG_SEM_DINHEIRO
        if agendada:
            return codigo, 'O envio por transportadora não tem dia e hora marcados.'
    return codigo, None


# ── encomenda ──────────────────────────────────────────────────────────────────

def e_envio(encomenda):
    """A encomenda foi pedida com uma opção de envio (ou já saiu por transportadora)."""
    ent = _entrega(encomenda)
    if ent and ent.tipo == 'envio':
        return True
    op = encomenda.opcao_entrega
    return bool(op and op.tipo == 'envio')


def _entrega(encomenda):
    from django.core.exceptions import ObjectDoesNotExist
    try:
        return encomenda.entrega
    except ObjectDoesNotExist:
        return None


def em_transito(encomenda):
    ent = _entrega(encomenda)
    return bool(ent and ent.tipo == 'envio' and ent.status == 'a_caminho')


def pago_antecipado(encomenda):
    p = getattr(encomenda, 'pagamento', None)
    return bool(p and p.status == 'aprovado')


def pode_enviar(encomenda):
    """None se a loja pode enviar agora; senão a razão."""
    from .encomendas import transferencia_por_confirmar
    if encomenda.tipo_entrega != 'entrega':
        return 'Esta encomenda é para levantar na loja.'
    if encomenda.status not in ('pago', 'preparando'):
        return {'enviado': 'A encomenda já foi enviada.', 'concluido': 'A encomenda já está concluída.',
                'cancelado': 'A encomenda foi cancelada.', 'pendente': 'A encomenda ainda não foi paga.'
                }.get(encomenda.status, 'Não é possível enviar esta encomenda agora.')
    if transferencia_por_confirmar(encomenda):
        return 'Confirma primeiro que a transferência chegou: a encomenda não sai sem estar paga.'
    if not pago_antecipado(encomenda):
        return 'Só se envia por transportadora uma encomenda já paga (cartão ou transferência confirmada).'
    ent = _entrega(encomenda)
    if ent and ent.status in ('atribuido', 'a_caminho'):
        return 'Esta encomenda já tem uma entrega em curso.'
    from .devolucoes import ativo
    r = ativo(encomenda)
    if r and r.tipo == 'cancelamento' and r.estado in ('pedido', 'em_disputa'):
        return 'O cliente pediu para cancelar: responde ao pedido antes de enviar.'
    return None


def limpar_codigos(codigos):
    if isinstance(codigos, str):
        import json
        try:
            codigos = json.loads(codigos)
        except ValueError:
            codigos = [codigos]
    if not isinstance(codigos, (list, tuple)):
        raise ErroEnvio('Códigos de rastreio inválidos.')
    vistos, out = set(), []
    for c in codigos:
        c = ' '.join(str(c or '').split()).upper()
        if not c:
            continue
        if len(c) > CODIGO_MAX:
            raise ErroEnvio(f'Cada código tem no máximo {CODIGO_MAX} caracteres.')
        if c not in vistos:
            vistos.add(c)
            out.append(c)
    if not out:
        raise ErroEnvio('Indica o código de rastreio.')
    if len(out) > CODIGOS_MAX:
        raise ErroEnvio(f'No máximo {CODIGOS_MAX} códigos por envio.')
    return out


def escolher_transportadora(transportadora_id, outra):
    from ..models import Transportadora
    if transportadora_id not in (None, ''):
        t = Transportadora.objects.filter(id=transportadora_id, ativa=True).first()
        if not t:
            raise ErroEnvio('Escolhe uma transportadora da lista.')
        return t, ''
    outra = (outra or '').strip()[:OUTRA_MAX]
    if len(outra) < 2:
        raise ErroEnvio('Escolhe a transportadora (ou escreve o nome em "Outra").')
    return None, outra


def _historico(entrega, acao, quem, nota=''):
    h = list(entrega.historico_envio or [])
    h.append({'em': timezone.now().isoformat(), 'acao': acao, 'por': quem.id if quem else None,
              'por_nome': (quem.nome or quem.user.username) if quem else '',
              'transportadora': entrega.transportadora_nome, 'codigos': list(entrega.codigos or []),
              'nota': (nota or '')[:NOTA_MAX]})
    entrega.historico_envio = h[-50:]


def _texto_codigos(entrega):
    return ', '.join(entrega.codigos or [])


def _avisar_cliente(encomenda, titulo, mensagem, importante=True):
    from ..Views.notificacaoView import notificar
    notificar(utilizador=encomenda.comprador, tipo='encomenda_enviada', titulo=titulo, mensagem=mensagem,
              loja=encomenda.loja, link=f'/encomendas/{encomenda.id}',
              email=FE.IMPORTANTE if importante else None)


def enviar(encomenda, quem, transportadora_id=None, outra='', codigos=(), talao=None, nota=''):
    """encomenda bloqueada (select_for_update). talao: ContentFile de prova_entrega.preparar() ou None.
    Primeiro envio ou reenvio depois de devolvida. Devolve a Entrega."""
    from ..models import Entrega
    from . import devolucoes
    erro = pode_enviar(encomenda)
    if erro:
        raise ErroEnvio(erro)
    t, outra = escolher_transportadora(transportadora_id, outra)
    codigos = limpar_codigos(codigos)
    agora = timezone.now()
    ent = _entrega(encomenda)
    reenvio = bool(ent and ent.tipo == 'envio' and ent.status == 'devolvida')
    if ent is None:
        ent = Entrega(encomenda=encomenda, opcao_entrega=encomenda.opcao_entrega)
    # uma entrega de condutor falhada/cancelada passa a envio (OneToOne: a mesma linha)
    ent.tipo, ent.condutor, ent.status = 'envio', None, 'a_caminho'
    ent.motivo_falha = ent.nota_falha = ''
    ent.transportadora, ent.transportadora_nome = t, nome_transportadora(t, outra)
    ent.codigos, ent.data_envio = codigos, agora
    ent.nao_recebido_em, ent.nao_recebido_nota = None, ''
    if talao:
        ent.comprovativo_envio.save(talao.name, talao, save=False)
    _historico(ent, 'reenviado' if reenvio else 'enviado', quem, nota)
    ent.save()

    encomenda.status = 'enviado'
    encomenda.save(update_fields=['status'])
    devolucoes.ao_avancar_encomenda(encomenda, quem)
    plural = 'Códigos' if len(codigos) > 1 else 'Código'
    _avisar_cliente(
        encomenda,
        f'Encomenda {"reenviada" if reenvio else "enviada"} #{encomenda.id}',
        f'{encomenda.loja.nome} {"voltou a enviar" if reenvio else "enviou"} a tua encomenda por '
        f'{ent.transportadora_nome}. {plural} de rastreio: {_texto_codigos(ent)}.')
    return ent


def corrigir(encomenda, quem, transportadora_id=None, outra='', codigos=(), nota=''):
    """Corrige a transportadora/códigos de um envio a caminho (engano da loja)."""
    ent = _entrega(encomenda)
    if not ent or ent.tipo != 'envio' or ent.status != 'a_caminho':
        raise ErroEnvio('Só se corrige um envio que está a caminho.')
    t, outra = escolher_transportadora(transportadora_id, outra)
    codigos = limpar_codigos(codigos)
    nome = nome_transportadora(t, outra)
    if nome == ent.transportadora_nome and codigos == list(ent.codigos or []):
        raise ErroEnvio('Não mudaste nada.')
    ent.transportadora, ent.transportadora_nome, ent.codigos = t, nome, codigos
    ent.nao_recebido_em, ent.nao_recebido_nota = None, ''
    _historico(ent, 'corrigido', quem, nota)
    ent.save(update_fields=['transportadora', 'transportadora_nome', 'codigos', 'historico_envio', 'nao_recebido_em',
                            'nao_recebido_nota'])
    _avisar_cliente(encomenda, f'Código de rastreio corrigido — Encomenda #{encomenda.id}',
                    f'{encomenda.loja.nome} corrigiu os dados do envio: {ent.transportadora_nome}, '
                    f'{_texto_codigos(ent)}.')
    return ent


def devolvida(encomenda, quem, nota=''):
    """A transportadora devolveu a encomenda à loja → volta a "em preparação" (reenviar ou cancelar)."""
    ent = _entrega(encomenda)
    if not ent or ent.tipo != 'envio' or ent.status != 'a_caminho':
        raise ErroEnvio('Só um envio a caminho pode ser marcado como devolvido.')
    nota = (nota or '').strip()
    if len(nota) < 5:
        raise ErroEnvio('Diz o que aconteceu (pelo menos 5 caracteres).')
    ent.status = 'devolvida'
    ent.nao_recebido_em, ent.nao_recebido_nota = None, ''
    _historico(ent, 'devolvido', quem, nota)
    ent.save(update_fields=['status', 'historico_envio', 'nao_recebido_em', 'nao_recebido_nota'])
    if encomenda.status == 'enviado':
        encomenda.status = 'preparando'
        encomenda.save(update_fields=['status'])
    _avisar_cliente(encomenda, f'Envio devolvido à loja — Encomenda #{encomenda.id}',
                    f'A transportadora devolveu a tua encomenda a {encomenda.loja.nome}. A loja vai voltar a '
                    f'enviá-la ou contactar-te.')
    return ent


# ── cliente: recebi / não recebi ───────────────────────────────────────────────

def concluir(encomenda, por='cliente'):
    """Fecha um envio a caminho como entregue (por='cliente': "Recebi"; 'auto': fecho automático — fase 3).
    encomenda bloqueada. Conta como a loja a concluir: data de conclusão (prazo de devolução) e entrega fechada."""
    from .devolucoes import ao_avancar_encomenda
    from .encomendas import fechar_entrega
    from ..Views.notificacaoView import notificar, notificar_staff
    if not em_transito(encomenda) or encomenda.status != 'enviado':
        raise ErroEnvio('Esta encomenda não está a caminho.')
    encomenda.status, encomenda.data_conclusao = 'concluido', timezone.now()
    encomenda.save(update_fields=['status', 'data_conclusao'])
    fechar_entrega(encomenda)
    ao_avancar_encomenda(encomenda, None)
    quem = 'O cliente confirmou que recebeu' if por == 'cliente' else 'Fechada automaticamente (sem resposta do cliente)'
    notificar_staff(loja=encomenda.loja, roles=['dono', 'gestor'], tipo='encomenda_concluida_loja',
                    titulo=f'Encomenda #{encomenda.id} concluída ✓', mensagem=f'{quem} — envio por transportadora.',
                    link=f'/loja/{encomenda.loja_id}/backoffice/encomendas/{encomenda.id}')
    if por != 'cliente':
        notificar(utilizador=encomenda.comprador, tipo='encomenda_concluida', titulo=f'Encomenda concluída #{encomenda.id}',
                  mensagem='Demos a encomenda como entregue. Se houver algum problema, podes pedir ajuda na encomenda.',
                  loja=encomenda.loja, link=f'/encomendas/{encomenda.id}', email=FE.INFORMATIVO)


def nao_recebi(encomenda, nota=''):
    """O cliente diz que não recebeu: a loja é avisada (email) e o fecho automático fica parado até ela agir."""
    from ..Views.notificacaoView import notificar_staff
    ent = _entrega(encomenda)
    if not em_transito(encomenda):
        raise ErroEnvio('Esta encomenda não está a caminho.')
    if ent.nao_recebido_em:
        raise ErroEnvio('Já avisaste a loja. Espera pela resposta ou fala com ela no chat da encomenda.')
    nota = ' '.join((nota or '').split())[:300]
    ent.nao_recebido_em, ent.nao_recebido_nota = timezone.now(), nota
    ent.save(update_fields=['nao_recebido_em', 'nao_recebido_nota'])
    notificar_staff(loja=encomenda.loja, roles=['dono', 'gestor'], tipo='encomenda_atualizada',
                    titulo=f'O cliente não recebeu a encomenda #{encomenda.id}',
                    mensagem=(f'Envio por {ent.transportadora_nome} ({_texto_codigos(ent)}). '
                              + (f'O cliente diz: "{nota}". ' if nota else '')
                              + 'Confirma com a transportadora: corrige o código, marca-a como devolvida ou conclui-a '
                                'se já foi entregue.'),
                    link=f'/loja/{encomenda.loja_id}/backoffice/encomendas/{encomenda.id}', email=FE.IMPORTANTE)
    return ent


# ── para os serializers ────────────────────────────────────────────────────────

def dados(entrega, request=None, loja=False):
    """Bloco 'envio' da encomenda (cliente e loja). None se não é envio. loja=True junta histórico e talão."""
    if not entrega or entrega.tipo != 'envio':
        return None
    t = entrega.transportadora
    url = t.url_rastreio if t else ''
    out = {
        'transportadora': entrega.transportadora_nome,
        'transportadora_id': entrega.transportadora_id,
        'contacto': t.contacto if t else '',
        'codigos': [{'codigo': c, 'link': link_rastreio(url, c)} for c in (entrega.codigos or [])],
        'data_envio': entrega.data_envio,
        'estado': entrega.status,
        'data_entrega': entrega.data_entrega,
        'nao_recebido_em': entrega.nao_recebido_em,
        'nao_recebido_nota': entrega.nao_recebido_nota,
    }
    if loja:
        out['historico'] = entrega.historico_envio or []
        out['talao'] = None
        u = getattr(getattr(request, 'user', None), 'utilizador', None) if request else None
        if entrega.comprovativo_envio and u:
            from .prova_entrega import assinar
            from .ver_loja import a_ver
            admin = bool(a_ver(entrega.encomenda.loja_id, u))
            out['talao'] = request.build_absolute_uri(
                f'/app/entregas/{entrega.id}/prova/talao/?t={assinar(entrega.id, "talao", u.id, admin)}')
    return out
