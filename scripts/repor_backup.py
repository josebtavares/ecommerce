#!/usr/bin/env python3
"""
Repor a base de dados da Bende a partir de um backup — corre no teu computador.

  python scripts/repor_backup.py --dev --listar        backups da dev
  python scripts/repor_backup.py --dev                 escolhe e repõe na dev (Docker)
  python scripts/repor_backup.py --prod --listar       backups da produção (bucket R2 privado)
  python scripts/repor_backup.py --prod                escolhe e repõe na PRODUÇÃO

Precisa de: Docker a correr; para --prod, a CLI do Railway com sessão iniciada (railway login) e esta pasta
ligada ao projeto (railway link). Não precisa de passwords: lê-as do Railway e apaga-as no fim.

Só aceita backups do armazenamento de backups com assinatura válida — nunca um ficheiro qualquer.
O trabalho é feito por manage.py repor_backup (backend/clube/app/utils/repor_backup.py): descarrega, confere a
assinatura, ensaia numa base temporária, mostra o que se perde, pede confirmação escrita, guarda o estado atual,
repõe, confere, migra e, se algo falhar a meio, volta sozinho ao estado anterior.

--prod: constrói a imagem a partir da branch `prod` (o código que está no ar, não o desta pasta) e corre-a aqui
com as variáveis da produção. Funciona mesmo que os serviços do Railway estejam em baixo — só precisa da base.

--ensaio-prod: igual ao --prod, mas a base é a cópia de ensaio local (contentor ensaio-pg, base prodcopy) e o
Redis é o da dev. Serve para ensaiar o procedimento sem tocar na produção.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
IMAGEM = 'bende-repor:prod'
CONTENTOR_DEV = 'ecommerce-backend-1'
REDE_DEV = 'ecommerce_default'
ENSAIO_BD = 'postgres://postgres:ensaio@ensaio-pg:5432/prodcopy'
ENSAIO_REDIS = 'redis://redis:6379/5'


def sair(msg):
    print(f'\nERRO: {msg}', file=sys.stderr)
    sys.exit(1)


def correr(cmd, **kw):
    return subprocess.run(cmd, **kw)


def tty():
    return ['-it'] if sys.stdin.isatty() and sys.stdout.isatty() else ['-i']


def variaveis(servico):
    r = correr(['railway', 'variables', '--service', servico, '--json'], capture_output=True, text=True,
               cwd=RAIZ, encoding='utf-8')
    if r.returncode != 0:
        sair(f'não consegui ler as variáveis do serviço {servico} no Railway (railway login / railway link?)\n'
             f'{r.stderr.strip()[-300:]}')
    return json.loads(r.stdout)


def construir_imagem(pasta, ref):
    print(f'A preparar o código da branch {ref}…')
    r = correr(['git', 'archive', '--format=tar', ref, 'backend/clube'], capture_output=True, cwd=RAIZ)
    if r.returncode != 0:
        sair(f'git archive {ref} falhou: {r.stderr.decode(errors="replace")[-300:]}')
    arquivo = pasta / 'codigo.tar'
    arquivo.write_bytes(r.stdout)
    with tarfile.open(arquivo) as t:
        t.extractall(pasta / 'codigo')
    print('A construir a imagem (a primeira vez demora alguns minutos)…')
    r = correr(['docker', 'build', '-q', '-t', IMAGEM, str(pasta / 'codigo' / 'backend' / 'clube')])
    if r.returncode != 0:
        sair('docker build falhou')


def ambiente_prod(ensaio):
    app = variaveis('ecommerce')
    env = {k: v for k, v in app.items() if not k.startswith('RAILWAY_') and '\n' not in str(v)}
    if ensaio:
        env['DATABASE_URL'] = ENSAIO_BD
        env['REDIS_URL'] = ENSAIO_REDIS
        env['EMAIL_BACKEND'] = 'django.core.mail.backends.console.EmailBackend'
    else:
        env['DATABASE_URL'] = variaveis('Postgres')['DATABASE_PUBLIC_URL']
        env['REDIS_URL'] = variaveis('Redis')['REDIS_PUBLIC_URL']
    env['DJANGO_SETTINGS_MODULE'] = 'clube.settings_prod'
    env['SENTRY_DSN'] = ''
    return env


def repor_prod(extra, ensaio, ref='prod'):
    for prog in ('docker', 'railway', 'git'):
        if not shutil.which(prog):
            sair(f'falta o programa «{prog}»')
    pasta = Path(tempfile.mkdtemp(prefix='bende-repor-'))
    try:
        construir_imagem(pasta, ref)
        env = ambiente_prod(ensaio)
        ficheiro_env = pasta / 'prod.env'
        ficheiro_env.write_text(''.join(f'{k}={v}\n' for k, v in env.items()), encoding='utf-8')
        os.chmod(ficheiro_env, 0o600)
        # --entrypoint: o entrypoint.sh da imagem corre o migrate e arranca o servidor — aqui não pode
        cmd = ['docker', 'run', '--rm', *tty(), '--env-file', str(ficheiro_env), '--entrypoint', 'python']
        if ensaio:
            cmd += ['--network', REDE_DEV]
        cmd += [IMAGEM, 'manage.py', 'repor_backup', '--alvo', 'prod', *extra]
        r = correr(cmd)
    finally:
        shutil.rmtree(pasta, ignore_errors=True)    # leva o ficheiro com as variáveis
    return r.returncode


def reiniciar_servicos():
    if not sys.stdin.isatty():
        print('Reinicia os serviços ecommerce e worker no Railway para limparem o que tinham em memória.')
        return
    if input('\nReiniciar agora os serviços ecommerce e worker no Railway? [s/N] ').strip().lower() != 's':
        print('Não reiniciados. Fá-lo no painel do Railway quando puderes.')
        return
    for s in ('ecommerce', 'worker'):
        r = correr(['railway', 'redeploy', '--service', s, '-y'], cwd=RAIZ)
        print(f'  {s}: {"pedido" if r.returncode == 0 else "FALHOU — reinicia no painel"}')


def main():
    p = argparse.ArgumentParser(description='Repor a base de dados da Bende a partir de um backup assinado.')
    alvo = p.add_mutually_exclusive_group(required=True)
    alvo.add_argument('--dev', action='store_true', help='base da dev (Docker)')
    alvo.add_argument('--prod', action='store_true', help='base da PRODUÇÃO')
    alvo.add_argument('--ensaio-prod', action='store_true', help='como --prod mas na cópia de ensaio local')
    p.add_argument('--listar', action='store_true', help='só lista os backups')
    p.add_argument('--backup', metavar='NOME', help='nome do backup (sem isto escolhes numa lista)')
    p.add_argument('--confirmar', metavar='FRASE', help=argparse.SUPPRESS)
    p.add_argument('--codigo', default='prod', help=argparse.SUPPRESS)   # só para ensaiar uma branch antes do deploy
    p.add_argument('--sem-copia-atual', action='store_true',
                   help='continua mesmo sem conseguir guardar o estado atual (só se a base estiver estragada)')
    a = p.parse_args()

    extra = []
    if a.listar:
        extra.append('--listar')
    if a.backup:
        extra += ['--backup', a.backup]
    if a.confirmar:
        extra += ['--confirmar', a.confirmar]
    if a.sem_copia_atual:
        extra.append('--sem-copia-atual')

    if a.dev:
        r = correr(['docker', 'exec', *tty(), CONTENTOR_DEV, 'python', 'manage.py', 'repor_backup', '--alvo', 'dev', *extra])
        if r.returncode == 0 and not a.listar:
            correr(['docker', 'restart', 'ecommerce-worker-1'], capture_output=True)
            print('Worker da dev reiniciado.')
        sys.exit(r.returncode)

    if a.prod and not a.listar:
        print('\n*** ATENÇÃO: vais repor a base de dados da PRODUÇÃO. ***')
    if a.prod and a.codigo != 'prod':
        sair('na produção usa-se sempre o código da branch prod')
    codigo = repor_prod(extra, ensaio=a.ensaio_prod, ref=a.codigo)
    if codigo == 0 and a.prod and not a.listar:
        reiniciar_servicos()
    sys.exit(codigo)


if __name__ == '__main__':
    main()
