"""
Admin → Backups (só quem tem gerir_backups — o super-admin).

  GET  /app/admin/backups/                      → resumo + lista paginada (?tipo=&estado=&de=&ate=&q=&limit=&offset=)
  GET  /app/admin/backups/descargas/            → registo de descargas paginado (?de=&ate=&q=&limit=&offset=)
  POST /app/admin/backups/fazer/                → backup manual agora
  POST /app/admin/backups/<id>/descarregar/     → link de 5 minutos (fica registado quem e de onde)
  POST /app/admin/backups/ensaiar/   {id?}     → ensaio de reposição (o worker repõe numa base temporária e confere)
  GET  /app/admin/backups/ficheiro/<token>/     → só na dev (sem R2): entrega o ficheiro do link assinado

Repor um backup a sério NÃO se faz aqui: apagava a plataforma num clique. O ensaio só usa uma base
temporária; o procedimento para repor está em docs/REPOR_BACKUP.md.
"""
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.db.models import Count, Q, Sum
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import BackupBD, DescargaBackup
from ..utils import backups
from .adminView import _exige_admin
from .faturacaoView import _datas, _paginar

VALIDADE_LINK = 300                 # segundos
SALT_LINK = 'backup-ficheiro'
INTERVALO_MANUAL = timedelta(minutes=1)


def _nome(u):
    if not u:
        return ''
    return u.get_full_name() or u.username


def _item(b):
    return {
        'id': b.id, 'tipo': b.tipo, 'estado': b.estado, 'tamanho': b.tamanho, 'duracao_s': b.duracao_s,
        'erro': b.erro[-500:] if b.estado == 'erro' else '',
        'nome': b.chave.rsplit('/', 1)[-1] if b.chave else '',
        'criado_em': b.criado_em, 'pedido_por': _nome(b.pedido_por),
        'disponivel': b.estado == 'ok' and b.apagado_em is None,
        'apagado_em': b.apagado_em,
        'descargas': getattr(b, 'n_descargas', None),
        'ensaio_em': b.ensaio_em, 'ensaio_ok': b.ensaio_ok,
    }


def _periodo(request, campo):
    """?de=&ate= (AAAA-MM-DD, dias de Cabo Verde) → (Q, erro)."""
    de, ate, erro = _datas(request)
    if erro:
        return None, erro
    if de and ate and de > ate:
        return None, Response({'detail': 'A data inicial é depois da data final.'}, status=status.HTTP_400_BAD_REQUEST)
    filtro = Q()
    if de:
        filtro &= Q(**{f'{campo}__date__gte': de})
    if ate:
        filtro &= Q(**{f'{campo}__date__lte': ate})
    return filtro, None


def _pessoa(prefixo, q):
    return (Q(**{f'{prefixo}__username__icontains': q}) | Q(**{f'{prefixo}__first_name__icontains': q})
            | Q(**{f'{prefixo}__last_name__icontains': q}) | Q(**{f'{prefixo}__email__icontains': q}))


def _resumo():
    vivos = BackupBD.objects.filter(estado='ok', apagado_em__isnull=True)
    ultimo = vivos.order_by('-criado_em').first()
    agora = timezone.localtime()
    proximo = agora.replace(hour=settings.BACKUP_HORA, minute=0, second=0, microsecond=0)
    if backups.backup_devido(agora):
        proximo = agora + timedelta(minutes=5)      # o worker verifica de 5 em 5 minutos
    elif proximo <= agora:
        proximo += timedelta(days=1)
    return {
        'ultimo_ok': ultimo.criado_em if ultimo else None,
        'guardados': vivos.count(),
        'espaco': vivos.aggregate(t=Sum('tamanho'))['t'] or 0,
        'armazenamento': 'Cloudflare R2 (privado)' if settings.BACKUP_R2_BUCKET else 'Disco local (dev)',
        'proximo_automatico': proximo,
        'a_correr': BackupBD.objects.filter(estado='a_correr').exists(),
        'retencao': '7 diários, 4 semanais e 12 mensais; manuais 30 dias',
        'ensaio': _ensaio(),
    }


def _ensaio():
    u = backups.ultimo_ensaio()
    ok = BackupBD.objects.filter(ensaio_ok=True).order_by('-ensaio_em').first()
    proximo = (timezone.localtime(ok.ensaio_em) + timedelta(days=settings.BACKUP_ENSAIO_DIAS)) if ok else None
    return {
        'em_curso': backups.ensaio_em_curso(),
        'ultimo': {'quando': u.ensaio_em, 'ok': u.ensaio_ok, 'backup_id': u.id, **u.ensaio_detalhe} if u else None,
        'proximo': proximo,
        'cada_dias': settings.BACKUP_ENSAIO_DIAS,
    }


ESTADOS = {
    'ok': Q(estado='ok', apagado_em__isnull=True),
    'erro': Q(estado='erro'),
    'a_correr': Q(estado='a_correr'),
    'apagado': Q(apagado_em__isnull=False),     # saíram pela retenção: ficam no histórico, sem ficheiro
}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_backups(request):
    erro = _exige_admin(request, 'gerir_backups')
    if erro:
        return erro
    periodo, erro = _periodo(request, 'criado_em')
    if erro:
        return erro
    qs = BackupBD.objects.filter(periodo)
    estado = request.GET.get('estado', '')
    if estado in ESTADOS:
        qs = qs.filter(ESTADOS[estado])
    elif estado != 'todos':                         # por omissão: os que ainda existem
        qs = qs.filter(apagado_em__isnull=True)
    tipo = request.GET.get('tipo', '')
    if tipo in ('automatico', 'manual'):
        qs = qs.filter(tipo=tipo)
    q = request.GET.get('q', '').strip()[:100]
    if q:
        qs = qs.filter(Q(chave__icontains=q) | _pessoa('pedido_por', q))
    qs = qs.select_related('pedido_por').annotate(n_descargas=Count('descargas')).order_by('-criado_em', '-id')
    pagina, total = _paginar(request, qs)
    return Response({'resumo': _resumo(), 'count': total, 'results': [_item(b) for b in pagina]})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_backup_descargas(request):
    erro = _exige_admin(request, 'gerir_backups')
    if erro:
        return erro
    periodo, erro = _periodo(request, 'data_criacao')
    if erro:
        return erro
    qs = DescargaBackup.objects.filter(periodo)
    q = request.GET.get('q', '').strip()[:100]
    if q:
        qs = qs.filter(_pessoa('utilizador', q) | Q(backup__chave__icontains=q) | Q(ip__startswith=q))
    qs = qs.select_related('backup', 'utilizador').order_by('-data_criacao', '-id')
    pagina, total = _paginar(request, qs)
    return Response({'count': total, 'results': [{
        'id': d.id, 'backup': d.backup.chave.rsplit('/', 1)[-1], 'por': _nome(d.utilizador),
        'email': d.utilizador.email if d.utilizador else '', 'ip': d.ip, 'quando': d.data_criacao,
    } for d in pagina]})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_backup_ensaiar(request):
    erro = _exige_admin(request, 'gerir_backups')
    if erro:
        return erro
    qs = BackupBD.objects.filter(estado='ok', apagado_em__isnull=True)
    bid = request.data.get('id')
    b = qs.filter(pk=bid).first() if bid else qs.order_by('-criado_em').first()
    if not b:
        return Response({'detail': 'Backup não encontrado ou já não disponível.'}, status=status.HTTP_404_NOT_FOUND)
    try:
        backups.pedir_ensaio(b.id)
    except backups.EnsaioEmCurso as e:
        return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)
    return Response({'backup_id': b.id, 'nome': b.chave.rsplit('/', 1)[-1]}, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_backup_fazer(request):
    erro = _exige_admin(request, 'gerir_backups')
    if erro:
        return erro
    recente = BackupBD.objects.filter(tipo='manual', criado_em__gte=timezone.now() - INTERVALO_MANUAL).exists()
    if recente:
        return Response({'detail': 'Acabou de ser feito um backup manual. Espera um minuto.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS)
    try:
        b = backups.fazer_backup('manual', request.user)
    except backups.BackupEmCurso:
        return Response({'detail': 'Já há um backup a correr. Tenta daqui a pouco.'}, status=status.HTTP_409_CONFLICT)
    return Response(_item(b), status=status.HTTP_201_CREATED if b.estado == 'ok' else status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_backup_descarregar(request, backup_id):
    erro = _exige_admin(request, 'gerir_backups')
    if erro:
        return erro
    b = BackupBD.objects.filter(pk=backup_id).first()
    if not b:
        return Response({'detail': 'Backup não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    if b.estado != 'ok' or b.apagado_em or not b.chave:
        return Response({'detail': 'Este backup já não está disponível.'}, status=status.HTTP_410_GONE)
    arm = backups.armazenamento()
    if not arm.existe(b.chave):     # apagado à mão no armazenamento
        b.apagado_em = timezone.now()
        b.save(update_fields=['apagado_em'])
        return Response({'detail': 'O ficheiro deste backup já não existe no armazenamento.'}, status=status.HTTP_410_GONE)
    url = arm.url(b.chave, VALIDADE_LINK)
    if url is None:     # dev: o próprio servidor entrega o ficheiro
        token = signing.dumps({'id': b.id}, salt=SALT_LINK)
        url = request.build_absolute_uri(f'/app/admin/backups/ficheiro/{token}/')
    DescargaBackup.objects.create(backup=b, utilizador=request.user, ip=request.META.get('REMOTE_ADDR') or None)
    return Response({'url': url, 'expira_em_s': VALIDADE_LINK, 'nome': b.chave.rsplit('/', 1)[-1]})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def admin_backup_ficheiro(request, token):
    """Só existe para o armazenamento em disco (dev); no R2 o link vai direto ao bucket."""
    try:
        dados = signing.loads(token, salt=SALT_LINK, max_age=VALIDADE_LINK)
    except signing.BadSignature:
        raise Http404
    b = BackupBD.objects.filter(pk=dados.get('id'), estado='ok', apagado_em__isnull=True).first()
    caminho = backups.armazenamento().caminho(b.chave) if b else None
    if not caminho or not caminho.exists():
        raise Http404
    return FileResponse(open(caminho, 'rb'), as_attachment=True, filename=caminho.name,
                        content_type='application/octet-stream')
