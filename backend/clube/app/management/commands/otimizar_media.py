"""manage.py otimizar_media — converte as fotos e vídeos que já existiam para as versões leves
(utils/versoes_media.py). As fotos novas já são convertidas no upload; os vídeos novos pelo worker.

  manage.py otimizar_media --simular      só conta o que seria feito
  manage.py otimizar_media                fotos: converte já; vídeos: põe na fila do worker
  manage.py otimizar_media --so-fotos | --so-videos

Fotos: WebP com no máximo 1600 px (banners 1920) + miniatura 600 px; os registos passam a apontar para o
ficheiro novo e o antigo vai para a fila de limpeza (o worker só o apaga se já ninguém o usar). A cópia de
segurança das fotos (utils/backup_media.py) guarda os antigos 30 dias.
Vídeos: voltam a ser convertidos pelo worker (720p, 480p e poster WebP). Até acabar, a loja mostra o vídeo
atual sem poster.
"""
import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from app.utils import limpeza, versoes_media, video

FOTOS = {'jpg', 'jpeg', 'png', 'webp', 'avif'}


class Command(BaseCommand):
    help = 'Converte as fotos e vídeos antigos para as versões leves (WebP, miniaturas, 720p/480p).'

    def add_arguments(self, parser):
        parser.add_argument('--simular', action='store_true')
        parser.add_argument('--so-fotos', action='store_true')
        parser.add_argument('--so-videos', action='store_true')

    def handle(self, *args, **o):
        if not o['so_videos']:
            self._fotos(o['simular'])
        if not o['so_fotos']:
            self._videos(o['simular'])

    # ── fotos ─────────────────────────────────────────────────────
    def _campos_fotos(self):
        """(Modelo, campo) públicos que podem ter fotos (os de storage próprio — privado — ficam de fora)."""
        for Modelo, campo in limpeza.campos_ficheiro():
            f = Modelo._meta.get_field(campo)
            if f.storage is default_storage and not campo.endswith('_poster'):
                yield Modelo, campo

    def _fotos(self, simular):
        campos = list(self._campos_fotos())
        nomes = {}
        for Modelo, campo in campos:
            for nome in Modelo.objects.exclude(**{campo: ''}).exclude(**{f'{campo}__isnull': True}) \
                    .values_list(campo, flat=True).distinct():
                ext = os.path.splitext(nome)[1].lower().lstrip('.')
                if ext not in FOTOS or versoes_media.PRINCIPAL.match(nome) or limpeza.protegido(nome):
                    continue
                nomes.setdefault(nome, (Modelo._meta.model_name, campo))
        self.stdout.write(f'Fotos por converter: {len(nomes)}')
        if simular:
            return
        feitas = falhas = antes = depois = 0
        for nome, (modelo, campo) in sorted(nomes.items()):
            try:
                with default_storage.open(nome, 'rb') as f:
                    dados = f.read()
                from io import BytesIO
                if versoes_media.animada(BytesIO(dados)):
                    continue
                foto, mini = versoes_media.converter_imagem(BytesIO(dados), versoes_media.lado_de(modelo, campo))
                pasta = os.path.dirname(nome)
                novo = f'{pasta}/{versoes_media.nome_novo("webp")}' if pasta else versoes_media.nome_novo('webp')
                novo = default_storage.save(novo, ContentFile(foto))
                default_storage.save(versoes_media.variante(novo, '__600'), ContentFile(mini))
                for Modelo, c in campos:                       # todos os registos que usam este ficheiro
                    Modelo.objects.filter(**{c: nome}).update(**{c: novo})
                limpeza.agendar_apagar([nome], 'otimizar_media')
                feitas += 1
                antes += len(dados)
                depois += len(foto)
            except Exception as e:
                falhas += 1
                self.stderr.write(f'  {nome}: {e}')
        self.stdout.write(self.style.SUCCESS(
            f'Fotos convertidas: {feitas} ({antes / 1e6:.1f} MB → {depois / 1e6:.1f} MB)'
            + (f'; {falhas} falharam (ficam como estavam)' if falhas else '')))

    # ── vídeos ────────────────────────────────────────────────────
    def _videos(self, simular):
        agendados = 0
        for (modelo, campo) in video.PERFIS:
            Modelo = video._modelo(modelo)
            for obj in Modelo.objects.exclude(**{campo: ''}).exclude(**{f'{campo}__isnull': True}).iterator():
                nome = getattr(obj, campo).name
                if not video.e_video(nome):
                    continue
                if versoes_media.PRINCIPAL.match(nome) and getattr(obj, f'{campo}_estado') in ('pronto', 'pendente'):
                    continue                                    # já tem as versões (ou já está na fila)
                if not simular:
                    video.reprocessar(obj, campo)
                agendados += 1
        verbo = 'por converter' if simular else 'postos na fila do worker'
        self.stdout.write(self.style.SUCCESS(f'Vídeos {verbo}: {agendados}'))
