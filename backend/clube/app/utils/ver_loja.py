"""
Admin a ver o backoffice de uma loja — ou o dashboard de um POS — em modo de leitura
(Admin → Lojas → "Ver backoffice"; Admin → POS → "Ver POS").

Serve para o superadmin consultar faturas, encomendas, vendas e históricos (ex.: pedidos da DNRE,
provas) sem a password do dono — também de lojas/POS suspensos ou de donos banidos.

- POST /app/admin/lojas/<id>/ver-backoffice/ (ou /app/admin/pos/<id>/ver/) regista o acesso
  (AcessoAdminLoja / AcessoAdminPOS) e devolve um token de acesso curto (DURACAO, sem refresh) com
  ver_loja=<id> ou ver_pos=<id> e so_leitura. O do POS não abre o backoffice da loja ligada (os
  produtos dela chegam pelos endpoints do POS); para a loja há o "Ver backoffice", registado à parte.
- Com esse token, as duas autenticações (autenticacao.JWTContaAtiva e pos.permissions.POSAuthentication)
  chamam validar(): recusa tudo o que não seja leitura e põe aqui (ContextVar, por pedido) o que o
  admin está a ver.
- UtilizadorLoja.obter_membro devolve então, nessa loja, um membro com o papel de dono que não
  existe na base de dados; no POS, pos.permissions.conta_principal devolve o dono do POS. O backoffice
  e o dashboard abrem como o dono os vê. Escrever é impossível — o token não deixa passar nada além de GET.
"""
from contextvars import ContextVar
from datetime import timedelta

DURACAO = timedelta(hours=2)
METODOS_LEITURA = ('GET', 'HEAD', 'OPTIONS')

_atual = ContextVar('ver_loja', default=None)      # (loja_id | None, pos_id | None, user_id)


def definir(loja_id=None, user_id=None, pos_id=None):
    _atual.set((int(loja_id) if loja_id else None, int(pos_id) if pos_id else None, user_id)
               if (loja_id or pos_id) else None)


def a_ver(loja_id, utilizador):
    """A pessoa deste pedido é o admin a ver esta loja com o token de leitura?"""
    v = _atual.get()
    return bool(v and v[0] and utilizador is not None and loja_id is not None
                and v[0] == int(loja_id) and v[2] == utilizador.user_id)


def pos_a_ver(utilizador):
    """Id do POS que o admin deste pedido está a ver com o token de leitura (ou None)."""
    v = _atual.get()
    if v and v[1] and utilizador is not None and v[2] == utilizador.user_id:
        return v[1]
    return None


def validar(request, user, token):
    """Token de leitura do admin: só com a permissão (ainda) e só leitura. As duas autenticações
    chamam isto — um token so_leitura nunca escreve, venha por onde vier."""
    from rest_framework.exceptions import PermissionDenied
    from rest_framework_simplejwt.exceptions import InvalidToken
    definir()           # nunca herda o modo de leitura de outro pedido
    if not token.get('so_leitura'):
        return
    from ..models import Utilizador
    perfil = Utilizador.objects.filter(user_id=user.pk).first()
    if not user.is_staff or not perfil or not perfil.pode_admin('ver_backoffice_lojas'):
        raise InvalidToken('Sem permissão para ver lojas.')
    if request.method not in METODOS_LEITURA:
        raise PermissionDenied('Modo só de leitura — estás a ver como admin.')
    definir(token.get('ver_loja'), user.pk, token.get('ver_pos'))


def _token(user, **claims):
    from rest_framework_simplejwt.tokens import AccessToken
    token = AccessToken.for_user(user)
    token.set_exp(lifetime=DURACAO)
    for k, v in claims.items():
        if v:
            token[k] = v
    token['so_leitura'] = True
    return str(token)


def emitir_token(user, loja):
    return _token(user, ver_loja=loja.id)


def emitir_token_pos(user, pos):
    return _token(user, ver_pos=pos.id)
