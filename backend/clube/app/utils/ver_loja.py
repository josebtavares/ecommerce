"""
Admin a ver o backoffice de uma loja em modo de leitura (Admin → Lojas → "Ver backoffice").

Serve para o superadmin consultar faturas, encomendas e históricos de qualquer loja (ex.: pedidos
da DNRE, provas) sem a password do dono — também de lojas suspensas ou de donos banidos.

- POST /app/admin/lojas/<id>/ver-backoffice/ regista o acesso (AcessoAdminLoja) e devolve um token
  de acesso curto (DURACAO, sem refresh) com ver_loja=<id> e so_leitura.
- Com esse token, autenticacao.JWTContaAtiva recusa tudo o que não seja leitura e põe aqui
  (ContextVar, por pedido) a loja e quem a está a ver.
- UtilizadorLoja.obter_membro devolve então, nessa loja, um membro com o papel de dono que não
  existe na base de dados: o backoffice abre como o dono o vê. Escrever é impossível — o token
  não deixa passar nada além de GET.
"""
from contextvars import ContextVar
from datetime import timedelta

DURACAO = timedelta(hours=2)
METODOS_LEITURA = ('GET', 'HEAD', 'OPTIONS')

_atual = ContextVar('ver_loja', default=None)


def definir(loja_id=None, user_id=None):
    _atual.set((int(loja_id), user_id) if loja_id else None)


def a_ver(loja_id, utilizador):
    """A pessoa deste pedido é o admin a ver esta loja com o token de leitura?"""
    v = _atual.get()
    return bool(v and utilizador is not None and loja_id is not None
                and v[0] == int(loja_id) and v[1] == utilizador.user_id)


def emitir_token(user, loja):
    from rest_framework_simplejwt.tokens import AccessToken
    token = AccessToken.for_user(user)
    token.set_exp(lifetime=DURACAO)
    token['ver_loja'] = loja.id
    token['so_leitura'] = True
    return str(token)
