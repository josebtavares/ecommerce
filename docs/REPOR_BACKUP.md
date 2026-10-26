# Repor um backup da base de dados

Procedimento para recuperar a plataforma Bende a partir de um backup. Lê tudo antes de começar.
Repor **substitui** os dados — o que entrou depois do backup perde-se (encomendas, registos, pagamentos).

> Ensaiado a 26/10/2026 com o backup automático `bende-20261026-142314-automatico.dump` (464 KB):
> descarregar do R2 11 s · repor num Postgres 18 novo 2,5 s · migrar para o código atual 11 s.
> Todas as tabelas de negócio bateram certo linha a linha; login e testes da aplicação passaram em cima da cópia.

---

## 0. Como repor (o caminho normal): o script

```bash
python scripts/repor_backup.py --prod --listar     # ver os backups que há
python scripts/repor_backup.py --prod              # escolher um e repor na PRODUÇÃO
python scripts/repor_backup.py --dev               # o mesmo na dev
```
Precisa só de: Docker a correr, Git, e a CLI do Railway com sessão iniciada (`railway login`) nesta pasta
(`railway link`). Não se escreve nenhuma password: o script lê-as do Railway e apaga-as no fim.

O que o script faz (backend/clube/app/utils/repor_backup.py):
1. **Só aceita backups do bucket de backups** com o nome que a plataforma lhes dá e **com assinatura válida**
   (sha256 + HMAC com a SECRET_KEY da plataforma). Um ficheiro posto lá por outra pessoa, alterado ou de outra
   plataforma é recusado. Não há maneira de lhe dar um ficheiro do computador.
2. Repõe-no primeiro numa base temporária e mostra, tabela a tabela, **o que se perde** (encomendas, pagamentos…).
3. Pede uma frase escrita: `REPOR PRODUÇÃO` (na dev `REPOR`).
4. Guarda o estado atual em `bd/antes-de-repor/` (também assinado) — é por aí que se volta atrás:
   `python scripts/repor_backup.py --prod --backup bende-…-antes-de-repor.dump`.
5. Põe o site em manutenção (a API responde 503; o worker pára), repõe, confere as contagens com as do ensaio
   e corre as migrações. **Se algo falhar a meio, volta sozinho ao estado anterior.**
6. Acerta a lista de backups, tira a manutenção, limpa a cache, avisa os super-admins por email e oferece-se para
   reiniciar os serviços `ecommerce` e `worker`.

Na produção o script constrói a imagem a partir da **branch `prod`** (o código que está no ar) e corre-a no teu
computador ligada à base da produção — funciona mesmo que os serviços do Railway estejam em baixo.
Se a base estiver tão estragada que nem se consegue guardar o estado atual, junta `--sem-copia-atual`.

Os backups feitos antes de 26/10/2026 (sem assinatura) ficam assinados no backup diário seguinte
(ou já: `manage.py backup_bd --assinar`).

As secções seguintes são o procedimento à mão — para perceber o que o script faz, ou se ele não puder correr.

## 1. Antes de repor: é mesmo preciso?

| Situação | O que fazer |
|---|---|
| A base desapareceu, está corrompida, ou a maior parte dos dados foi apagada | Repor tudo (secção 4) |
| Apagou-se **um** registo ou poucos (uma loja, uma encomenda) | **Não** repor tudo: repor numa base temporária e copiar só esses dados (secção 6) |
| Um deploy correu mal mas os dados estão bons | Não repor: voltar à versão anterior do código no Railway |

## 2. Onde estão os backups

- **Bucket privado do Cloudflare R2 `bende-backups`**, pasta `bd/AAAA/MM/`, ficheiros `bende-AAAAMMDD-HHMMSS-<automatico|manual>.dump`
  (formato `pg_dump -Fc`, um único ficheiro com a base inteira).
- Retenção: o último de cada um dos últimos 7 dias, 4 semanas e 12 meses; os manuais ficam 30 dias.
- Para descarregar: **Admin → Backups → Descarregar** (link de 5 minutos, fica registado), ou o painel do Cloudflare (R2 → `bende-backups`).
- O worker faz o backup todos os dias depois das 03:00 (hora de Cabo Verde) e de 30 em 30 dias repõe um numa base
  temporária para confirmar que serve (**Admin → Backups → Ensaio de reposição**; também `manage.py backup_bd --ensaiar`).
  Escolhe, de preferência, um backup marcado como **reposição testada**.

**Fotos e vídeos** (bucket das lojas e bucket privado do chat/reembolsos/comprovativos): o worker copia-os todos
os dias, de forma incremental, para o mesmo bucket `bende-backups`, pasta `media/publico/` e `media/privado/`.
O que as lojas apagam passa para `media-apagados/AAAAMMDD/` e fica lá 30 dias. Ver secção 7.

**O que NÃO está no backup**
- Variáveis de ambiente do Railway (chaves, passwords): guarda uma cópia num gestor de passwords.
- Redis: só cache e mensagens em tempo real — não precisa de backup.

## 3. Ferramentas

Postgres **18** (`pg_restore` e `psql` da mesma versão do servidor; a produção e a dev são 18.x). Num Windows:
`C:\Program Files\PostgreSQL\18\bin`. Ou um contentor: `docker run --rm -it -v "$PWD:/r" postgres:18 bash`.

O endereço da base vem do Railway: serviço **Postgres → Variables → `DATABASE_PUBLIC_URL`**
(`postgresql://postgres:<password>@<host>:<porta>/railway`). Nunca o coloques em chats nem em ficheiros do repositório.

## 4. Repor a plataforma inteira (à mão — o script da secção 0 faz isto tudo)

### 4.1 Parar as escritas
No Railway, pôr os serviços **`ecommerce`** e **`worker`** em pausa (Settings → *Remove/Stop* da instância, ou
réplicas a 0). Assim ninguém grava nada a meio da reposição. O frontend pode ficar ligado.

### 4.2 Guardar o estado atual (mesmo que esteja estragado)
```bash
pg_dump -Fc --no-owner --no-acl -d "$DATABASE_PUBLIC_URL" -f antes-de-repor-$(date +%Y%m%d-%H%M).dump
```
Se algo correr mal, há sempre maneira de voltar a este ponto.

### 4.3 Ensaiar primeiro numa base temporária
```bash
psql "$DATABASE_PUBLIC_URL" -c "CREATE DATABASE bende_ensaio_manual"
pg_restore --no-owner --no-acl --exit-on-error \
  -d "${DATABASE_PUBLIC_URL%/*}/bende_ensaio_manual" bende-AAAAMMDD-HHMMSS-automatico.dump
psql "${DATABASE_PUBLIC_URL%/*}/bende_ensaio_manual" -c "SELECT count(*) FROM auth_user" -c "SELECT count(*) FROM app_loja" -c "SELECT count(*) FROM app_encomenda"
```
Se os números fizerem sentido, segue. Se o `pg_restore` der erro, escolhe outro backup.

### 4.4 Repor
**Opção A — recomendada: um Postgres novo.** Deixa a base antiga intacta para analisar o que aconteceu.
1. Railway → *New* → *Database* → *PostgreSQL* (versão 18), na mesma região (EU West).
2. Repor nele:
   ```bash
   pg_restore --no-owner --no-acl --exit-on-error -d "$NOVO_DATABASE_PUBLIC_URL" bende-AAAAMMDD-HHMMSS-automatico.dump
   ```
3. Nos serviços `ecommerce` e `worker`, trocar a variável `DATABASE_URL` para a referência do novo serviço
   (`${{NovoPostgres.DATABASE_URL}}`).

**Opção B — na mesma base** (só se não for possível criar outra):
```bash
psql "$DATABASE_PUBLIC_URL" -c "DROP SCHEMA public CASCADE" -c "CREATE SCHEMA public"
pg_restore --no-owner --no-acl --exit-on-error -d "$DATABASE_PUBLIC_URL" bende-AAAAMMDD-HHMMSS-automatico.dump
```

### 4.5 Pôr ao nível do código atual
Se o backup for de antes do último deploy com migrações, a base fica atrás do código. Com o código da branch `prod`:
```bash
# DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME tirados do DATABASE_PUBLIC_URL (ficheiro temporário, apagar no fim)
docker exec --env-file pgdj.env ecommerce-backend-1 python manage.py migrate
docker exec --env-file pgdj.env ecommerce-backend-1 python manage.py migrate --check
```

### 4.6 Voltar a ligar e verificar
1. Ligar `ecommerce` e `worker` no Railway; esperar pelo health check.
2. Verificar: entrar com o super-admin; abrir uma loja; ver as encomendas no admin; fazer login com uma conta demo.
3. **Admin → Backups → Fazer backup agora** — o primeiro backup da base reposta.
4. Avisar as lojas, se houve dados perdidos (o que entrou entre o backup e a falha).
5. Apagar os ficheiros `.dump` e `pgdj.env` do computador onde se trabalhou.

## 5. Tempos de referência
Com a base de 26/10/2026 (~0,5 MB comprimida, ~4 000 linhas): descarregar 11 s, repor 2,5 s, migrar 11 s.
Contar com 15–30 minutos no total por causa dos passos manuais. O ensaio automático mostra o tempo de cada
ensaio no Admin → Backups — se a base crescer, é aí que se vê.

## 6. Recuperar só alguns dados
1. Repor o backup numa base temporária (4.3).
2. Encontrar os registos e exportá-los:
   ```bash
   psql "${DATABASE_PUBLIC_URL%/*}/bende_ensaio_manual" -c "\copy (SELECT * FROM app_produto WHERE loja_id = 123) TO 'produtos.csv' CSV HEADER"
   ```
3. Inseri-los na base da plataforma com cuidado (chaves estrangeiras, ids que entretanto possam ter sido reutilizados) — de
   preferência com um script revisto e testado primeiro numa cópia.
4. Apagar a base temporária: `psql "$DATABASE_PUBLIC_URL" -c "DROP DATABASE bende_ensaio_manual WITH (FORCE)"`.

## 7. Repor fotos e vídeos
Os ficheiros não fazem parte do dump da base: a base guarda só o caminho (`produtos/abc.webp`) e o ficheiro vive
no bucket das lojas. Para os devolver usa-se o comando, que **só repõe ficheiros que faltam — nunca substitui
nenhum que exista**. Sem `--confirmar` apenas simula e diz quantos faltam.

```bash
# no serviço worker do Railway (railway ssh --service worker) ou com as variáveis da prod num contentor
python manage.py backup_media --repor publico                       # simula: quantos faltam
python manage.py backup_media --repor publico --confirmar           # repõe tudo o que falta
python manage.py backup_media --repor publico --prefixo lojas/7/ --confirmar   # só uma loja/pasta
python manage.py backup_media --repor publico --dia 20261026 --confirmar       # ficheiros que a loja apagou nesse dia
python manage.py backup_media --repor privado --confirmar           # chat, reembolsos, comprovativos
```
Depois de repor a base de um backup antigo (secção 4), corre `--repor publico` e `--repor privado`: os ficheiros
apagados entretanto voltam, desde que tenham sido apagados há menos de 30 dias (usa `--dia`).

Proteção: se o bucket das lojas aparecer vazio, ou se uma passagem fosse tirar da cópia mais de metade dos ficheiros,
a cópia pára com erro e os super-admins recebem email — a cópia de segurança não é esvaziada por uma credencial ou
bucket errado. Quando o armazenamento de backups passa dos 8 GB (`BACKUP_LIMITE_GB`) chega um email (no máximo 1 por semana).

## 8. Ensaio automático (o que o worker faz)
`app/utils/backups.py → ensaiar_reposicao()`: descarrega o backup, cria a base temporária `bende_ensaio_reposicao`
no mesmo servidor (ou em `BACKUP_ENSAIO_URL`), corre `pg_restore --exit-on-error`, confere que todas as tabelas do
backup foram repostas e que utilizadores, lojas e migrações não estão vazios, e apaga a base. Nunca toca na base da
plataforma (recusa se os nomes coincidirem). Se falhar, os super-admins recebem um email.
