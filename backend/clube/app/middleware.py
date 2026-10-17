"""
IP real do cliente atrás do proxy do Railway.

Na produção o REMOTE_ADDR é sempre o proxy interno do Railway (100.64.x.x): todos os visitantes
pareciam vir de meia dúzia de IPs. Consequências:
- django-axes (bloqueio por username + IP): 5 passwords erradas de QUALQUER pessoa bloqueavam a
  conta para toda a gente durante 1 hora (dava para bloquear o admin de propósito);
- limites por IP (login do POS, verificação de username/email…) eram partilhados por todos.

O proxy do Railway acrescenta o IP de quem lhe ligou ao fim do X-Forwarded-For. Só esse último
valor (fora da rede interna) é de confiança (os anteriores podem ser inventados pelo cliente), e só quando o pedido vem
mesmo do proxy — na dev (ou sem proxy) nada muda.
"""
import ipaddress

from django.conf import settings

_PROXIES = [ipaddress.ip_network(r) for r in getattr(settings, 'PROXIES_CONFIAVEIS', ['100.64.0.0/10'])]


def _de_proxy(ip):
    try:
        endereco = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(endereco in rede for rede in _PROXIES)


def ip_do_cliente(meta):
    remoto = meta.get('REMOTE_ADDR', '')
    encaminhado = meta.get('HTTP_X_FORWARDED_FOR', '')
    if not encaminhado or not _de_proxy(remoto):
        return remoto
    # da direita para a esquerda, salta saltos internos do próprio Railway
    for valor in reversed(encaminhado.split(',')):
        valor = valor.strip()
        try:
            ip = str(ipaddress.ip_address(valor))
        except ValueError:
            return remoto
        if not _de_proxy(ip):
            return ip
    return remoto


class IPRealMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.META['REMOTE_ADDR'] = ip_do_cliente(request.META)
        return self.get_response(request)
