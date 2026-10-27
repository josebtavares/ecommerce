"""manage.py reconverter_fotos --mapa mapa.json [--confirmar]

Volta a converter fotos já convertidas a partir do ORIGINAL guardado na cópia de segurança das fotos
(utils/backup_media.py: media/publico/<nome> ou media-apagados/<dia>/publico/<nome>), com as definições
atuais de utils/versoes_media.py. Serve para quando se muda a qualidade da conversão.

O mapa diz de que original veio cada foto atual (tirado de um backup da base de antes da conversão):
  [{"atual": "produtos/2026/10/<hex>.webp", "original": "produtos/2026/10/foto.jpg", "modelo": "produto", "campo": "ficheiro"}, …]

A foto nova é gravada por cima do MESMO nome (e a miniatura __600 também): a base de dados não muda.
Sem --confirmar só mostra o que faria. Fotos cujo original já não está na cópia ficam como estão.
"""
import json

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from app.utils import backup_media, backups, limpeza, versoes_media


class Command(BaseCommand):
    help = 'Reconverte fotos a partir dos originais da cópia de segurança (mesmo nome, BD intacta).'

    def add_arguments(self, parser):
        parser.add_argument('--mapa', required=True, help='JSON com [{atual, original, modelo, campo}]')
        parser.add_argument('--confirmar', action='store_true')

    def handle(self, *args, **o):
        with open(o['mapa'], encoding='utf-8') as f:
            mapa = json.load(f)
        copia = backups.armazenamento()
        base = f'{backup_media.PASTA}/publico/'
        apagados = {}                      # nome original → chave em media-apagados/<dia>/publico/
        for chave in sorted(copia.listar(backup_media.PASTA_APAGADOS + '/')):
            partes = chave.split('/', 3)
            if len(partes) == 4 and partes[2] == 'publico':
                apagados[partes[3]] = chave     # o dia mais recente fica por último
        em_uso = {}
        for Modelo, campo in limpeza.campos_ficheiro():
            em_uso[(Modelo._meta.model_name, campo)] = Modelo

        feitas = sem_original = mudaram = falhas = antes = depois = 0
        for item in mapa:
            atual, original = item['atual'], item['original']
            Modelo = em_uso.get((item['modelo'], item['campo']))
            if (Modelo is None or not versoes_media.PRINCIPAL.match(atual)
                    or not Modelo.objects.filter(**{item['campo']: atual}).exists()):
                mudaram += 1                # a loja trocou a foto entretanto: não se mexe
                continue
            chave = base + original if copia.existe(base + original) else apagados.get(original)
            if not chave:
                sem_original += 1
                self.stdout.write(f'  sem original: {atual} ← {original}')
                continue
            if not o['confirmar']:
                feitas += 1
                continue
            try:
                fobj, _ = copia.abrir(chave)
                try:
                    dados = fobj.read()
                finally:
                    fobj.close()
                from io import BytesIO
                foto, mini = versoes_media.converter_imagem(
                    BytesIO(dados), versoes_media.lado_de(item['modelo'], item['campo']))
                self._por_cima(atual, foto)
                self._por_cima(versoes_media.variante(atual, '__600'), mini)
                feitas += 1
                antes += len(dados)
                depois += len(foto)
            except Exception as e:
                falhas += 1
                self.stderr.write(f'  {atual}: {e}')

        verbo = 'reconvertidas' if o['confirmar'] else 'por reconverter (simulação — usa --confirmar)'
        self.stdout.write(self.style.SUCCESS(
            f'Fotos {verbo}: {feitas}' + (f' ({antes / 1e6:.1f} MB originais → {depois / 1e6:.1f} MB)' if antes else '')
            + f'; sem original na cópia: {sem_original}; trocadas entretanto: {mudaram}'
            + (f'; falharam: {falhas}' if falhas else '')))

    @staticmethod
    def _por_cima(nome, dados):
        # o storage da produção não substitui (AWS_S3_FILE_OVERWRITE=False): apaga e grava no mesmo nome
        default_storage.delete(nome)
        gravado = default_storage.save(nome, ContentFile(dados))
        if gravado != nome:
            default_storage.delete(gravado)
            raise CommandError(f'o storage gravou {gravado} em vez de {nome}')
