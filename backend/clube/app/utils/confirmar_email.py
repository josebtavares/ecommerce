"""
Confirmação do email (decisões de 2026-10-30, contra contas de bots com emails falsos):
- conta nova (registo da Bende ou do POS) começa por confirmar e recebe um link por email (vale 3 dias);
- sem o email confirmado navega e entra, mas não encomenda, não marca nem cria loja (exigir());
- entrar com o Google confirma (o Google já verificou o email); mudar o email volta a pedir confirmação;
- as contas que já existiam ficaram confirmadas (migração 0083);
- contas por confirmar há mais de 7 dias, sem nada ligado, são apagadas pelo worker (apagar_abandonadas()).

O link é assinado (django.core.signing) com o id e o email: deixa de valer se o email mudar.
Emails descartáveis (mailinator, 10minutemail...) são recusados no registo: app/dados/emails_descartaveis.txt
(lista pública github.com/disposable-email-domains — actualizar de vez em quando).
"""
import logging
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

log = logging.getLogger(__name__)

SAL = 'confirmar-email'
VALIDADE = timedelta(days=3)
DIAS_ABANDONO = 7
MSG = {
    'encomendar': 'Confirma o teu email para encomendar — enviámos-te um link quando criaste a conta.',
    'marcar': 'Confirma o teu email para marcar — enviámos-te um link quando criaste a conta.',
    'loja': 'Confirma o teu email antes de criar uma loja — enviámos-te um link quando criaste a conta.',
}


# ── emails descartáveis ───────────────────────────────────────

@lru_cache(maxsize=1)
def _descartaveis():
    ficheiro = Path(__file__).resolve().parent.parent / 'dados' / 'emails_descartaveis.txt'
    try:
        return frozenset(l.strip().lower() for l in ficheiro.read_text(encoding='utf-8').splitlines()
                         if l.strip() and not l.startswith('#'))
    except OSError:
        log.error('confirmar email: lista de emails descartáveis em falta (%s)', ficheiro)
        return frozenset()


def descartavel(email):
    """mailinator.com, sub.mailinator.com... → True."""
    dominio = (email or '').rsplit('@', 1)[-1].strip().lower().rstrip('.')
    partes = dominio.split('.')
    lista = _descartaveis()
    return any('.'.join(partes[i:]) in lista for i in range(len(partes) - 1))


MSG_DESCARTAVEL = 'Não aceitamos emails temporários. Usa o teu email de todos os dias.'


# ── link ──────────────────────────────────────────────────────

def gerar_token(user):
    return signing.dumps({'u': user.pk, 'e': (user.email or '').lower()}, salt=SAL, compress=True)


def link(user):
    return f'{settings.FRONTEND_BASE_URL.rstrip("/")}/confirmar_email?token={gerar_token(user)}'


def enviar(utilizador_id):
    """Envia o link (fora da transacção — usar com transaction.on_commit). Uma falha fica no log."""
    from ..models import Utilizador
    u = Utilizador.objects.select_related('user').filter(pk=utilizador_id).first()
    if not u or u.email_confirmado or not u.user.email:
        return False
    user = u.user
    try:
        EmailMessage(
            subject='Confirma o teu email — Bende',
            body=(f'Olá {user.first_name or user.username},\n\n'
                  f'Para confirmares que este email é teu, abre o link:\n\n{link(user)}\n\n'
                  f'O link vale {VALIDADE.days} dias. Até confirmares podes ver as lojas, mas não encomendar, '
                  f'marcar serviços nem criar uma loja. Se não foste tu a criar a conta, ignora este email: '
                  f'a conta é apagada ao fim de {DIAS_ABANDONO} dias.\n\nBende'),
            from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email],
        ).send()
        return True
    except Exception:
        log.exception('confirmar email: falhou o envio')
        return False


def enviar_depois(utilizador):
    transaction.on_commit(lambda: enviar(utilizador.pk))


def marcar_confirmado(utilizador):
    if utilizador.email_confirmado:
        return False
    utilizador.email_confirmado, utilizador.email_confirmado_em = True, timezone.now()
    utilizador.save(update_fields=['email_confirmado', 'email_confirmado_em'])
    return True


def confirmar(token):
    """Token do link → (utilizador, None) ou (None, mensagem de erro)."""
    from ..models import Utilizador
    try:
        dados = signing.loads(token or '', salt=SAL, max_age=VALIDADE)
    except signing.SignatureExpired:
        return None, 'Este link expirou. Entra na tua conta e pede um novo.'
    except signing.BadSignature:
        return None, 'Link inválido.'
    u = Utilizador.objects.select_related('user').filter(user_id=dados.get('u')).first()
    # o email mudou depois de o link ser enviado: o link era para o email antigo
    if not u or (u.user.email or '').lower() != dados.get('e'):
        return None, 'Este link já não é válido. Entra na tua conta e pede um novo.'
    marcar_confirmado(u)
    return u, None


def exigir(utilizador, acao):
    """None se pode; senão o corpo da resposta 403 (codigo email_por_confirmar)."""
    if utilizador.email_confirmado:
        return None
    return {'detail': MSG[acao], 'codigo': 'email_por_confirmar'}


# ── limpeza ───────────────────────────────────────────────────

# o que pode ir com a conta: se o apagar levasse mais alguma coisa (encomendas, lojas, POS, mensagens...)
# a conta fica — não é lixo de um bot
# (a caixa de chat pessoal é criada sozinha; com conversas, as conversas também contavam e a conta ficava)
_PODE_IR = {'auth.user', 'app.utilizador', 'app.carrinho', 'app.itemcarrinho', 'app.notificacao', 'app.favorito',
            'chat.caixa', 'token_blacklist.outstandingtoken', 'token_blacklist.blacklistedtoken',
            'auth.user_groups', 'auth.user_user_permissions'}


def apagar_abandonadas(limite=50):
    """Worker: apaga contas por confirmar há mais de 7 dias que não têm nada ligado. Devolve quantas."""
    from django.contrib.auth.models import User
    from django.db import router
    from django.db.models.deletion import Collector, ProtectedError, RestrictedError
    antes = timezone.now() - timedelta(days=DIAS_ABANDONO)
    n = 0
    from django.db.models import Exists, OuterRef
    from ..models import Loja, UtilizadorLoja, Encomenda
    from ..pos.models import ConfiguracaoPOS
    from ..servicos.models import Marcacao
    u = OuterRef('utilizador')
    # quem é de uma loja (staff criado pelo dono, que nunca confirma), tem POS ou comprou nunca é lixo:
    # fica logo de fora, para não encher a lista de candidatos que o Collector ia recusar sempre
    candidatos = (User.objects.filter(utilizador__email_confirmado=False, date_joined__lt=antes,
                                      is_staff=False, is_superuser=False)
                  .exclude(Exists(UtilizadorLoja.objects.filter(utilizador=u)))
                  .exclude(Exists(Loja.objects.filter(dono=u)))
                  .exclude(Exists(ConfiguracaoPOS.objects.filter(dono=u)))
                  .exclude(Exists(Encomenda.objects.filter(comprador=u)))
                  .exclude(Exists(Marcacao.objects.filter(cliente=u)))
                  .order_by('date_joined'))
    for user in list(candidatos[:500]):
        if n >= limite:
            break
        try:
            with transaction.atomic():
                c = Collector(using=router.db_for_write(User))
                c.collect([user])
                # só o que existe mesmo (o Collector junta também as consultas vazias); SET_NULL também conta
                levaria = ({m._meta.label_lower for m, objs in c.data.items() if objs}
                           | {qs.model._meta.label_lower for qs in c.fast_deletes if qs.exists()}
                           | {campo.model._meta.label_lower for (campo, _), lotes in c.field_updates.items()
                              if any(lote.exists() if hasattr(lote, 'exists') else lote for lote in lotes)})
                if not levaria <= _PODE_IR:
                    continue
                foto = getattr(user.utilizador.foto, 'name', '') or ''
                user.delete()
            if foto and foto != 'utilizadores/default.png':
                from django.core.files.storage import default_storage
                try:
                    default_storage.delete(foto)
                except Exception:
                    log.warning('confirmar email: não apagou a foto %s', foto)
            n += 1
        except (ProtectedError, RestrictedError):
            continue                    # tem coisas que não podem ir: fica
        except Exception:
            log.exception('confirmar email: falhou apagar a conta %s', user.pk)
    return n
