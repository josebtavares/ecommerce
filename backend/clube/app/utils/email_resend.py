"""
Backend de email do Django que envia pela API HTTP do Resend (https://resend.com/docs/api-reference/emails/send-email).

Usa HTTPS em vez de SMTP porque o Railway bloqueia o SMTP de saída nos planos mais baixos.
Ativa-se com EMAIL_BACKEND=app.utils.email_resend.ResendBackend e RESEND_API_KEY no ambiente;
o remetente vem de DEFAULT_FROM_EMAIL (tem de ser de um domínio verificado no Resend, ex.: noreply@bende.store).
"""
import logging
import os

import requests
from django.core.mail.backends.base import BaseEmailBackend

log = logging.getLogger(__name__)

URL = 'https://api.resend.com/emails'
TIMEOUT = 10


class ResendBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = os.environ.get('RESEND_API_KEY', '')

    def send_messages(self, email_messages):
        if not self.api_key:
            if not self.fail_silently:
                raise RuntimeError('RESEND_API_KEY não definido')
            return 0
        enviados = 0
        for msg in email_messages:
            try:
                self._enviar(msg)
                enviados += 1
            except Exception:
                log.exception('Resend: falhou o envio de "%s"', msg.subject)
                if not self.fail_silently:
                    raise
        return enviados

    def _enviar(self, msg):
        corpo = {
            'from':    msg.from_email,
            'to':      msg.to,
            'subject': msg.subject,
            'text':    msg.body,
        }
        if msg.cc:
            corpo['cc'] = msg.cc
        if msg.bcc:
            corpo['bcc'] = msg.bcc
        if msg.reply_to:
            corpo['reply_to'] = msg.reply_to
        # EmailMultiAlternatives: a versão HTML vai no campo html
        for conteudo, tipo in getattr(msg, 'alternatives', []):
            if tipo == 'text/html':
                corpo['html'] = conteudo
        resp = requests.post(URL, json=corpo, timeout=TIMEOUT,
                             headers={'Authorization': f'Bearer {self.api_key}'})
        if resp.status_code >= 300:
            # a resposta do Resend explica o erro (domínio não verificado, chave inválida...) e não traz segredos
            raise RuntimeError(f'Resend respondeu {resp.status_code}: {resp.text[:300]}')
