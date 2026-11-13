"""
Sentry: erros do servidor (API, WebSockets) e do worker. Só liga com SENTRY_DSN (Railway / .env.dev).

Privacidade (lei de protecção de dados de CV + SISP):
- send_default_pii=False → sem IP, cookies, cabeçalhos de autenticação nem utilizador;
- o corpo dos pedidos nunca é enviado (senhas, IBAN, NIF, dados de cartão);
- sem valores das variáveis locais (include_local_variables=False): nas bibliotecas (ex.: requests) estão os
  corpos dos pedidos já em texto (posAuthCode da SISP…), que nenhum filtro por nome apanha. Fica a linha e a pilha;
- o resto (dados extra, breadcrumbs) passa pelo EventScrubber com os nomes sensíveis do Bendi.
"""
import os
import re

_EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')

# nomes (em minúsculas) cujo valor nunca sai do servidor — juntam-se aos do Sentry (password, token, secret…)
SENSIVEIS = [
    'senha', 'password1', 'password2', 'nova_senha', 'senha_atual', 'senha_nova', 'confirmar_senha',
    'nib', 'iban', 'swift', 'conta_bancaria', 'dados_bancarios',
    'posautcode', 'pos_aut_code', 'pos_auth_code', 'posauthcode', 'chave', 'chave_cifrada', 'chave_credenciais',
    'fingerprint', 'merchantsession', 'portal_senha', 'portal_password',
    'pan', 'cvv', 'cvc', 'numero_cartao', 'cartao_numero',
    'otp', 'pin', 'codigo_verificacao', 'codigo_confirmacao', 'refresh', 'access', 'access_token', 'refresh_token', 'ticket',
    'resend_api_key', 'voyage_api_key', 'turnstile_secret', 'r2_secret', 'aws_secret_access_key',
    'database_url', 'dsn',
]

# barulho que não é um erro nosso
IGNORAR_LOGGERS = ['django.security.DisallowedHost']


def _limpar(valor, nomes):
    if isinstance(valor, dict):
        return {k: ('[Filtered]' if str(k).lower() in nomes else _limpar(v, nomes)) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_limpar(v, nomes) for v in valor]
    return valor


def _sem_emails(texto):
    return _EMAIL.sub('[email]', texto) if isinstance(texto, str) else texto


def _filtro(nomes):
    """before_send: o EventScrubber não passa pelos 'contexts' nem pelas 'tags' — limpa-os também;
    e tira os emails das mensagens (erros e logs, ex.: "falhou o envio para alguém@…")."""
    def antes_de_enviar(evento, _hint):
        for parte in ('contexts', 'tags'):
            if evento.get(parte):
                evento[parte] = _limpar(evento[parte], nomes)
        for ex in (evento.get('exception') or {}).get('values') or []:
            ex['value'] = _sem_emails(ex.get('value'))
        le = evento.get('logentry') or {}
        for k in ('message', 'formatted'):
            if k in le:
                le[k] = _sem_emails(le[k])
        if 'params' in le:
            le['params'] = [_sem_emails(p) for p in le['params'] or []]
        evento['message'] = _sem_emails(evento.get('message'))
        for b in (evento.get('breadcrumbs') or {}).get('values') or []:
            b['message'] = _sem_emails(b.get('message'))
        return evento
    return antes_de_enviar


def iniciar(debug):
    dsn = os.environ.get('SENTRY_DSN', '').strip()
    if not dsn:
        return False
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import ignore_logger
    from sentry_sdk.scrubber import DEFAULT_DENYLIST, DEFAULT_PII_DENYLIST, EventScrubber

    commit = (os.environ.get('RAILWAY_GIT_COMMIT_SHA') or '')[:12]
    nomes = {n.lower() for n in DEFAULT_DENYLIST + SENSIVEIS}
    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get('SENTRY_AMBIENTE') or ('dev' if debug else 'producao'),
        release=commit or None,
        integrations=[DjangoIntegration()],
        send_default_pii=False,
        max_request_body_size='never',
        include_local_variables=False,
        event_scrubber=EventScrubber(denylist=DEFAULT_DENYLIST + SENSIVEIS,
                                     pii_denylist=DEFAULT_PII_DENYLIST, recursive=True),
        # desempenho por amostragem (o plano grátis tem limite): 5 % dos pedidos por defeito
        before_send=_filtro(nomes),
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES', '0.05') or 0),
    )
    sentry_sdk.set_tag('servico', os.environ.get('RAILWAY_SERVICE_NAME') or os.environ.get('SENTRY_SERVICO') or 'local')
    for nome in IGNORAR_LOGGERS:
        ignore_logger(nome)
    return True
