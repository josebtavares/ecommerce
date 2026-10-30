"""
Emails da Bende para clientes e lojas: versão texto + versão HTML com a marca (logótipo, botão, rodapé),
e "Responder para" o suporte (EMAIL_SUPORTE, ex.: suporte@bende.store — Email Routing da Cloudflare).

Os filtros (sobretudo o Outlook) desconfiam de emails só de texto, curtos e com um link comprido à vista:
aqui o link principal vira um botão e o endereço completo fica só numa linha pequena no fim.
Os emails internos (backups, avisos ao admin) continuam só de texto.

    msg = criar(para, assunto, texto, botao=('Confirmar email', url), anexos=[(nome, bytes, mime)])
    msg.send()

`texto` é o corpo em texto simples (parágrafos separados por linha em branco), sem a assinatura —
a assinatura "Bende" é acrescentada aqui. Uma linha só com o URL do botão não aparece no HTML.
"""
import html
import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

COR = '#dc2626'
_URL = re.compile(r'(https?://[^\s<>"]+)')


def _site():
    return (getattr(settings, 'FRONTEND_BASE_URL', '') or 'https://bende.store').rstrip('/')


def suporte():
    return getattr(settings, 'EMAIL_SUPORTE', '') or ''


def saudacao(user):
    """'Olá Ana,' com o primeiro nome; sem nome, só 'Olá,' (o username não é para tratar ninguém)."""
    nome = (getattr(user, 'first_name', '') or '').strip()
    return f'Olá {nome},' if nome else 'Olá,'


def _paragrafo(bloco):
    linhas = []
    for linha in bloco.split('\n'):
        partes = _URL.split(html.escape(linha, quote=False))
        # os URLs ficam clicáveis (escapados de novo dentro do href)
        linhas.append(''.join(
            f'<a href="{p}" style="color:{COR};word-break:break-all">{p}</a>' if i % 2 else p
            for i, p in enumerate(partes)))
    return ('<p style="margin:0 0 16px;font-size:15px;line-height:1.55;color:#27272a">'
            + '<br>'.join(linhas) + '</p>')


def _botao(rotulo, url):
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:4px 0 20px"><tr>'
            f'<td style="border-radius:10px;background:{COR}">'
            f'<a href="{url}" style="display:inline-block;padding:12px 26px;font-size:15px;font-weight:bold;'
            f'color:#ffffff;text-decoration:none;border-radius:10px">{rotulo}</a></td></tr></table>')


def _html(assunto, texto, botao):
    url_botao = botao[1] if botao else None
    blocos, pos_botao = [], None
    for bloco in re.split(r'\n\s*\n', texto.strip()):
        todas = bloco.split('\n')
        linhas = [l for l in todas if l.strip() != url_botao]
        if any(l.strip() for l in linhas):
            blocos.append(_paragrafo('\n'.join(linhas).strip()))
        if len(linhas) < len(todas) and pos_botao is None:
            pos_botao = len(blocos)          # o botão fica onde estava o link
    if botao:
        rotulo, url = html.escape(botao[0]), html.escape(botao[1])
        blocos.insert(len(blocos) if pos_botao is None else pos_botao, _botao(rotulo, url))
        blocos.append(f'<p style="margin:0 0 16px;font-size:12px;line-height:1.5;color:#71717a">Se o botão não funcionar, '
                      f'copia este endereço para o browser:<br><a href="{url}" style="color:#71717a;word-break:break-all">{url}</a></p>')
    corpo = ''.join(blocos)
    site = html.escape(_site())
    sup = html.escape(suporte())
    contacto = (f'Dúvidas? Responde a este email ou escreve para <a href="mailto:{sup}" style="color:#71717a">{sup}</a>.'
                if sup else '')
    return f'''<!doctype html>
<html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(assunto)}</title></head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:Arial,Helvetica,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:24px 12px"><tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px">
<tr><td style="padding:0 4px 16px">
<a href="{site}" style="text-decoration:none"><img src="{site}/icone-192.png" width="40" height="40" alt="Bende"
 style="vertical-align:middle;border:0;border-radius:10px">
<span style="vertical-align:middle;margin-left:8px;font-size:20px;font-weight:bold;color:#18181b">Bende</span></a>
</td></tr>
<tr><td style="background:#ffffff;border:1px solid #e4e4e7;border-radius:14px;padding:28px 26px">
{corpo}
<p style="margin:8px 0 0;font-size:15px;color:#27272a">Bende</p>
</td></tr>
<tr><td style="padding:16px 6px;font-size:12px;line-height:1.5;color:#71717a">
Recebeste este email por causa da tua conta na Bende. {contacto}<br>
<a href="{site}" style="color:#71717a">{site.replace("https://", "")}</a>
</td></tr>
</table></td></tr></table></body></html>'''


def criar(para, assunto, texto, *, botao=None, anexos=()):
    """EmailMultiAlternatives com texto + HTML e Reply-To do suporte. `para`: um email ou uma lista."""
    para = [para] if isinstance(para, str) else list(para)
    texto = texto.strip()
    corpo_texto = texto + '\n\nBende'
    if suporte():
        corpo_texto += f'\nDúvidas? Responde a este email ou escreve para {suporte()}.'
    msg = EmailMultiAlternatives(subject=assunto, body=corpo_texto, from_email=settings.DEFAULT_FROM_EMAIL,
                                 to=para, reply_to=[suporte()] if suporte() else None)
    msg.attach_alternative(_html(assunto, texto, botao), 'text/html')
    for nome, conteudo, mime in anexos:
        msg.attach(nome, conteudo, mime)
    return msg
