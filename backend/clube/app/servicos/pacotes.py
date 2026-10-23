"""
Pacotes de serviços: um serviço (Servico.e_pacote) feito de vários serviços da loja (ComponentePacote),
pelo mesmo profissional e numa só marcação. O pacote tem a sua duração, preço e profissionais — com
preco_auto / duracao_auto seguem a soma dos serviços e são actualizados quando estes mudam.

Os serviços do pacote têm de existir à parte (o dono pode escondê-los: Servico.visivel=False). Um pacote
só se marca com todos os seus serviços activos; a marcação guarda a lista do que incluía (Marcacao.componentes).
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Q

from .models import ComponentePacote, Servico

MIN_COMPONENTES = 2
MAX_COMPONENTES = 10


def ler_componentes(loja, ids, pacote=None):
    """Lista de ids → serviços (pela ordem dada) ou (None, mensagem de erro)."""
    if not isinstance(ids, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
        return None, 'Lista de serviços do pacote inválida.'
    if len(set(ids)) != len(ids):
        return None, 'O mesmo serviço está repetido no pacote.'
    if not MIN_COMPONENTES <= len(ids) <= MAX_COMPONENTES:
        return None, f'Um pacote tem de {MIN_COMPONENTES} a {MAX_COMPONENTES} serviços.'
    por_id = {s.id: s for s in Servico.objects.filter(loja=loja, id__in=ids)}
    if len(por_id) != len(ids):
        return None, 'Há serviços que não são desta loja.'
    if pacote is not None and pacote.id in por_id:
        return None, 'Um pacote não se pode incluir a si próprio.'
    if any(s.e_pacote for s in por_id.values()):
        return None, 'Um pacote não pode ter outros pacotes dentro.'
    return [por_id[i] for i in ids], None


def somas(servicos):
    """(preço, duração, tipo de preço) da soma dos serviços."""
    preco = sum((s.preco for s in servicos), Decimal('0'))
    duracao = min(max(sum(s.duracao_min for s in servicos), 5), 720)
    tipo = 'a_partir' if any(s.tipo_preco == 'a_partir' for s in servicos) else 'fixo'
    return preco, duracao, tipo


def servicos_de(pacote):
    return [c.servico for c in pacote.componentes.select_related('servico')]


def aplicar_somas(pacote, servicos=None):
    """Põe no pacote o preço / a duração da soma (os que estão em automático). Não grava."""
    preco, duracao, tipo = somas(servicos if servicos is not None else servicos_de(pacote))
    if pacote.preco_auto:
        pacote.preco, pacote.tipo_preco = preco, tipo
    if pacote.duracao_auto:
        pacote.duracao_min = duracao


@transaction.atomic
def guardar_componentes(pacote, servicos):
    pacote.componentes.all().delete()
    ComponentePacote.objects.bulk_create(
        [ComponentePacote(pacote=pacote, servico=s, ordem=i) for i, s in enumerate(servicos)])


def atualizar_pacotes_de(servico):
    """Um serviço mudou de preço/duração: os pacotes em automático acompanham."""
    for pacote in (Servico.objects.filter(componentes__servico=servico)
                   .filter(Q(preco_auto=True) | Q(duracao_auto=True)).distinct()):
        aplicar_somas(pacote)
        pacote.save(update_fields=['preco', 'tipo_preco', 'duracao_min', 'data_atualizacao'])


def pacotes_com(servico, so_ativos=True):
    qs = Servico.objects.filter(componentes__servico=servico).distinct()
    return qs.filter(ativo=True) if so_ativos else qs


def reservaveis(qs):
    """Serviços activos que se podem marcar (um pacote precisa de todos os seus serviços activos)."""
    return qs.filter(ativo=True).exclude(e_pacote=True, componentes__servico__ativo=False)


def marcaveis(qs):
    """O que o cliente vê e marca: reservável e visível sozinho."""
    return reservaveis(qs).filter(visivel=True)


def em_falta(pacote):
    """Nomes dos serviços inactivos de um pacote (o pacote fica indisponível)."""
    return [s.nome for s in servicos_de(pacote) if not s.ativo] if pacote.e_pacote else []


def snapshot(servico):
    if not servico.e_pacote:
        return []
    return [{'id': s.id, 'nome': s.nome, 'duracao_min': s.duracao_min, 'preco': str(s.preco)} for s in servicos_de(servico)]


def profissionais_comuns(servicos):
    """Profissionais activos que fazem todos os serviços (sugestão para o pacote)."""
    comuns = None
    for s in servicos:
        ids = {p.id for p in s.profissionais.all() if p.ativo}
        comuns = ids if comuns is None else comuns & ids
    return comuns or set()
