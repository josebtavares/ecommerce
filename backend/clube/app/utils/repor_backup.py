"""
Repor a base de dados a partir de um backup — usado por manage.py repor_backup (e por scripts/repor_backup.py).

Só aceita backups do armazenamento de backups (R2 privado; na dev BACKUP_DIR), com o nome que a plataforma
lhes dá e com assinatura válida (utils/backups.assinatura_valida). Nunca um ficheiro qualquer.

Passos de executar():
  1. descarrega o backup e confere a assinatura;
  2. ensaia-o numa base temporária e compara as contagens com a base atual (o que se perde);
  3. pede a confirmação escrita;
  4. guarda o estado atual (bd/antes-de-repor/…, assinado) — é por aí que se volta atrás;
  5. põe a plataforma em manutenção (o site responde 503, o worker pára);
  6. corta as ligações, apaga o esquema public e repõe o backup;
  7. confere as contagens com as do ensaio e corre as migrações;
  8. acerta a lista de backups com os ficheiros que existem (a base reposta não conhece os mais recentes);
  9. tira a manutenção, limpa a cache e avisa os super-admins por email.
Se o passo 6 ou 7 falhar, repõe sozinho o estado guardado no passo 4.
"""
import logging
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.core.management import call_command
from django.db import connection
from django.utils import timezone

from ..models import BackupBD
from . import backups

log = logging.getLogger(__name__)

PADRAO = re.compile(r'^bd/(?:\d{4}/\d{2}|antes-de-repor)/bende-(\d{8})-(\d{6})-(automatico|manual|antes-de-repor)\.dump$')
MANUTENCAO = 'plataforma:manutencao'
FRASE = {'dev': 'REPOR', 'prod': 'REPOR PRODUÇÃO'}
RESUMO = [('auth_user', 'Utilizadores'), ('app_loja', 'Lojas'), ('app_produto', 'Produtos'),
          ('app_encomenda', 'Encomendas'), ('app_pagamento', 'Pagamentos'), ('app_reembolso', 'Reembolsos'),
          ('pos_contamesa', 'Contas do POS'), ('servicos_marcacao', 'Marcações')]


class Recusado(Exception):
    """O backup não pode ser reposto (não existe, não está assinado, não se lê…). Nada foi alterado."""


# ── manutenção (lida pelo middleware do site e pelo worker) ─────────

def em_manutencao():
    try:
        return bool(cache.get(MANUTENCAO))
    except Exception:           # sem Redis o site continua a funcionar
        return False


def _manutencao(ligar, motivo=''):
    if ligar:
        cache.set(MANUTENCAO, {'motivo': motivo, 'desde': timezone.now().isoformat()}, 2 * 3600)
    else:
        cache.delete(MANUTENCAO)


# ── backups disponíveis ─────────────────────────────────────────────

def disponiveis():
    """Backups no armazenamento com nome válido, do mais recente para o mais antigo."""
    res = []
    for chave, (tamanho, _) in backups.armazenamento().listar('bd/').items():
        m = PADRAO.match(chave)
        if not m:
            continue
        quando = timezone.make_aware(datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S'))
        res.append({'chave': chave, 'nome': chave.rsplit('/', 1)[-1], 'tamanho': tamanho,
                    'quando': quando, 'tipo': m.group(3)})
    return sorted(res, key=lambda x: x['quando'], reverse=True)


def escolher(nome=None):
    lista = disponiveis()
    if not lista:
        raise Recusado('Não há nenhum backup no armazenamento de backups.')
    if not nome:
        return lista[0]
    for b in lista:
        if nome in (b['nome'], b['chave']):
            return b
    raise Recusado(f'O backup «{nome}» não existe no armazenamento de backups (usa --listar para ver os que há).')


def preparar(b, pasta):
    """Descarrega e confere assinatura e leitura. Devolve (caminho, nº de tabelas com dados)."""
    arm = backups.armazenamento()
    ficheiro = Path(pasta) / b['nome']
    arm.descarregar(b['chave'], ficheiro)
    ok, motivo = backups.assinatura_valida(ficheiro, arm.assinatura(b['chave']))
    if not ok:
        raise Recusado(f'Backup recusado: {motivo}.')
    r = subprocess.run(['pg_restore', '-l', str(ficheiro)], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise Recusado(f'O ficheiro não se lê: {r.stderr.strip()[-400:]}')
    return ficheiro, sum(1 for linha in r.stdout.splitlines() if ' TABLE DATA ' in linha)


# ── contagens ──────────────────────────────────────────────────────

def _contar(args, env, bd):
    res = {}
    for linha in backups._psql(args, env, backups.SQL_CONTAR, bd).splitlines():
        if '|' in linha:
            nome, n = linha.split('|', 1)
            res[nome] = int(n or 0)
    return res


def contar_atual():
    args, env = backups._ambiente_pg()
    return _contar(args[:-2], env, args[-1])


def ensaiar(ficheiro):
    """Repõe numa base temporária, conta e apaga-a. Devolve as contagens por tabela."""
    args, env, manutencao = backups._servidor_ensaio()
    if backups.BD_ENSAIO == connection.settings_dict.get('NAME'):
        raise Recusado('a base de ensaio não pode ser a da plataforma')
    if cache.get(backups.TRANCA_ENSAIO):
        raise Recusado('O worker está a fazer um ensaio de reposição; tenta daqui a uns minutos.')
    backups._psql(args, env, f'DROP DATABASE IF EXISTS {backups.BD_ENSAIO} WITH (FORCE)', manutencao)
    backups._psql(args, env, f'CREATE DATABASE {backups.BD_ENSAIO}', manutencao)
    try:
        r = subprocess.run(['pg_restore', '--no-owner', '--no-acl', '--exit-on-error', *args, '-d', backups.BD_ENSAIO,
                            str(ficheiro)], env=env, capture_output=True, text=True, timeout=backups.LIMITE_S)
        if r.returncode != 0:
            raise Recusado(f'O backup não se repõe numa base vazia: {r.stderr.strip()[-600:]}')
        return _contar(args, env, backups.BD_ENSAIO)
    finally:
        backups._psql(args, env, f'DROP DATABASE IF EXISTS {backups.BD_ENSAIO} WITH (FORCE)', manutencao)


def diferencas(atual, backup):
    """[(rótulo, agora, no backup)] para as tabelas do RESUMO que existem, mais o total de linhas."""
    linhas = [(rotulo, atual.get(t, 0), backup.get(t, 0)) for t, rotulo in RESUMO if t in atual or t in backup]
    linhas.append(('Total de linhas (todas as tabelas)', sum(atual.values()), sum(backup.values())))
    return linhas


# ── repor ──────────────────────────────────────────────────────────

def guardar_estado_atual(pasta):
    agora = timezone.localtime()
    nome = f'bende-{agora:%Y%m%d-%H%M%S}-antes-de-repor.dump'
    ficheiro = Path(pasta) / nome
    backups._dump(ficheiro)
    chave = f'bd/antes-de-repor/{nome}'
    backups.armazenamento().guardar(ficheiro, chave, backups.assinatura_de(ficheiro))
    return chave, ficheiro


def repor_na_base(ficheiro):
    args, env = backups._ambiente_pg()
    ligacao, bd = args[:-2], args[-1]
    connection.close()
    backups._psql(ligacao, env, 'SELECT pg_terminate_backend(pid) FROM pg_stat_activity '
                                'WHERE datname = current_database() AND pid <> pg_backend_pid()', bd)
    backups._psql(ligacao, env, 'DROP SCHEMA public CASCADE', bd)
    backups._psql(ligacao, env, 'CREATE SCHEMA public', bd)
    r = subprocess.run(['pg_restore', '--no-owner', '--no-acl', '--exit-on-error', *ligacao, '-d', bd, str(ficheiro)],
                       env=env, capture_output=True, text=True, timeout=backups.LIMITE_S)
    if r.returncode != 0:
        raise RuntimeError(f'pg_restore falhou: {r.stderr.strip()[-800:]}')


def reconciliar():
    """A base reposta só conhece os backups que existiam quando foi feita: junta os ficheiros que existem e
    marca como apagados os que já não existem. Sem isto a retenção nunca apagaria os mais recentes."""
    existentes = {b['chave']: b for b in disponiveis()}
    conhecidos = set(BackupBD.objects.exclude(chave='').values_list('chave', flat=True))
    novos = 0
    for chave, b in existentes.items():
        if chave in conhecidos:
            continue
        r = BackupBD.objects.create(tipo='automatico' if b['tipo'] == 'automatico' else 'manual',
                                    estado='ok', chave=chave, tamanho=b['tamanho'])
        BackupBD.objects.filter(pk=r.pk).update(criado_em=b['quando'])
        novos += 1
    sumidos = BackupBD.objects.filter(estado='ok', apagado_em__isnull=True).exclude(chave='') \
        .exclude(chave__in=list(existentes)).update(apagado_em=timezone.now())
    return novos, sumidos


def _avisar(b, alvo, copia, quem):
    para = backups.destinatarios_alertas()
    if not para:
        return
    try:
        EmailMessage(
            subject='Bende: a base de dados foi reposta a partir de um backup',
            body=(f'A base de dados ({alvo}) foi reposta a partir do backup {b["nome"]} '
                  f'({timezone.localtime(b["quando"]):%d/%m/%Y %H:%M}).\n\nFeito por: {quem}\n'
                  f'Estado anterior guardado em: {copia or "(não foi guardado)"}\n\n'
                  'Tudo o que entrou depois da hora do backup deixou de existir na plataforma. '
                  'Se não foste tu, muda já as passwords e as chaves do Railway e do Cloudflare.\n\nBende'),
            from_email=settings.DEFAULT_FROM_EMAIL, to=para,
        ).send()
    except Exception:
        log.exception('repor: não consegui enviar o aviso')


def executar(alvo, nome=None, confirmacao=None, sem_copia_atual=False, quem='', escrever=print, perguntar=input):
    """Faz a reposição completa. Devolve um dict com o resultado; levanta Recusado se nada foi alterado."""
    if alvo not in FRASE:
        raise Recusado('alvo desconhecido')
    if cache.get(backups.TRANCA):
        raise Recusado('Está a ser feito um backup neste momento; tenta daqui a uns minutos.')
    b = escolher(nome)
    escrever(f'\nBackup: {b["nome"]} ({timezone.localtime(b["quando"]):%d/%m/%Y %H:%M}, {b["tamanho"] / 1e6:.1f} MB)')
    pasta = tempfile.mkdtemp(prefix='repor-')
    try:
        escrever('1/8 A descarregar e a conferir a assinatura…')
        ficheiro, tabelas = preparar(b, pasta)
        escrever(f'    assinatura válida; {tabelas} tabelas com dados.')

        escrever('2/8 A ensaiar numa base temporária…')
        no_backup = ensaiar(ficheiro)
        if len(no_backup) != tabelas:
            raise Recusado(f'o ensaio repôs {len(no_backup)} tabelas e o backup tem {tabelas}')
        atual = contar_atual()
        escrever('    o ensaio correu bem. Diferenças para a base atual:\n')
        escrever(f'    {"":38}{"agora":>10}{"no backup":>12}{"perde-se":>10}')
        for rotulo, agora, antes in diferencas(atual, no_backup):
            escrever(f'    {rotulo:38}{agora:>10}{antes:>12}{max(0, agora - antes):>10}')
        escrever('\n    Tudo o que entrou depois da hora do backup deixa de existir (encomendas, pagamentos, faturas…).')

        frase = FRASE[alvo]
        resposta = confirmacao if confirmacao is not None else perguntar(f'\n3/8 Para continuar escreve «{frase}»: ')
        if (resposta or '').strip() != frase:
            raise Recusado('Cancelado: a confirmação não bate certo. Nada foi alterado.')

        escrever('4/8 A guardar o estado atual…')
        copia = copia_local = None
        try:
            copia, copia_local = guardar_estado_atual(pasta)
            escrever(f'    guardado em {copia}')
        except Exception as e:
            if not sem_copia_atual:
                raise Recusado(f'Não consegui guardar o estado atual ({str(e)[:300]}). Nada foi alterado. '
                               'Se a base atual estiver mesmo estragada, corre outra vez com --sem-copia-atual.')
            escrever(f'    AVISO: não guardado ({str(e)[:200]}) — continua por causa de --sem-copia-atual')

        escrever('5/8 Plataforma em manutenção.')
        _manutencao(True, f'reposição de {b["nome"]}')
        inicio = time.monotonic()
        try:
            escrever('6/8 A repor…')
            repor_na_base(ficheiro)
            depois = contar_atual()
            if depois != no_backup:
                raise RuntimeError('as contagens depois de repor não batem com as do ensaio')
            escrever(f'    reposto e conferido ({sum(depois.values())} linhas em {len(depois)} tabelas).')
            escrever('7/8 A pôr a base ao nível do código (migrações)…')
            call_command('migrate', interactive=False, verbosity=0)
        except Exception as e:
            log.exception('repor: falhou a meio')
            if not copia_local:
                _manutencao(False)
                raise RuntimeError(f'A reposição falhou a meio e não havia cópia do estado anterior: {e}')
            escrever(f'    FALHOU ({str(e)[:300]}). A voltar ao estado anterior…')
            try:
                repor_na_base(copia_local)
            except Exception as e2:
                log.exception('repor: falhou também a volta ao estado anterior')
                raise RuntimeError(f'CRÍTICO: a reposição falhou ({e}) e a volta ao estado anterior também ({e2}). '
                                   f'A plataforma ficou em manutenção. Repõe à mão o ficheiro {copia} '
                                   '(docs/REPOR_BACKUP.md, secção 4).')
            _manutencao(False)
            raise RuntimeError(f'A reposição falhou e a base voltou ao estado anterior ({copia}). Erro: {e}')

        escrever('8/8 A acertar a lista de backups e a avisar…')
        novos, sumidos = reconciliar()
        _manutencao(False)
        try:
            cache.clear()
        except Exception:
            log.exception('repor: não consegui limpar a cache')
        _avisar(b, alvo, copia, quem)
        res = {'backup': b['nome'], 'copia_anterior': copia, 'segundos': round(time.monotonic() - inicio, 1),
               'backups_juntados': novos, 'backups_sumidos': sumidos}
        escrever(f'\nFeito em {res["segundos"]} s. Estado anterior: {copia or "não guardado"}.')
        return res
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
