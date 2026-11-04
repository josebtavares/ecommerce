"""
python manage.py verificar_migracoes [--desde app:0091]

Antes de um deploy: as migrações por aplicar nesta base de dados são seguras para o código que ainda está no ar?
No deploy a migração corre primeiro e o código novo só entra minutos depois (o Railway ainda está a construir). Nesse
intervalo o código ANTIGO trabalha com a base de dados NOVA. Uma migração é segura se o código antigo continua a
funcionar com ela — por exemplo, se só acrescenta tabelas, colunas que aceitam vazio ou colunas com valor por omissão
na própria base de dados (db_default).

PERIGO (sai com código 1) — o código antigo falha durante a janela:
  - coluna nova obrigatória sem db_default (o código antigo não a preenche → erro ao criar registos). Nota: `default=`
    não chega — o Django só o usa ao preencher as linhas existentes e depois tira-o da base de dados;
  - coluna que passa a obrigatória (null → não null) ou a única;
  - apagar ou mudar o nome de colunas/tabelas (o código antigo ainda as lê).
AVISO — ver à mão: RunPython/RunSQL (dados, bloqueios em tabelas grandes) e operações que o comando não conhece.

Como resolver um PERIGO: db_default=…, ou dividir em dois deploys (1.º acrescenta a coluna com null=True e o código
passa a preenchê-la; 2.º torna-a obrigatória / apaga a antiga).

--desde app:NNNN analisa como se só estivesse aplicado até essa migração dessa app (para ensaiar com o histórico).
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django.db.migrations import operations as ops
from django.db.migrations.executor import MigrationExecutor

PERIGOSAS = {
    ops.RemoveField: 'apaga a coluna {campo} — o código antigo ainda a lê',
    ops.RenameField: 'muda o nome da coluna {campo} — o código antigo usa o nome antigo',
    ops.DeleteModel: 'apaga a tabela {modelo} — o código antigo ainda a usa',
    ops.RenameModel: 'muda o nome da tabela {modelo} — o código antigo usa o nome antigo',
    ops.AlterModelTable: 'muda o nome da tabela {modelo} — o código antigo usa o nome antigo',
}
SEGURAS = (ops.CreateModel, ops.AddIndex, ops.RemoveIndex, ops.RenameIndex, ops.AddConstraint, ops.RemoveConstraint,
           ops.AlterModelOptions, ops.AlterModelManagers, ops.AlterIndexTogether, ops.AlterOrderWithRespectTo)


def _obrigatorio(campo):
    """O código antigo, que não conhece este campo, consegue criar registos? (False = sim)"""
    from django.db.models.fields import NOT_PROVIDED
    if campo.many_to_many or campo.null or getattr(campo, 'db_default', NOT_PROVIDED) is not NOT_PROVIDED:
        return False
    return True


def analisar(migracao, estado, criados):
    """Devolve [(nivel, texto)] para uma migração e avança `estado` (ProjectState) por ela."""
    app = migracao.app_label
    saida = []
    for op in migracao.operations:
        modelo = getattr(op, 'model_name', None) or getattr(op, 'name', '') or getattr(op, 'old_name', '')
        chave = (app, str(modelo).lower())
        campo = f'{modelo}.{getattr(op, "name", "") or getattr(op, "old_name", "")}'
        if isinstance(op, ops.CreateModel):
            criados.add((app, op.name_lower))
        elif chave in criados:
            pass   # tabela criada neste mesmo deploy: o código antigo não a usa
        elif isinstance(op, ops.AddField):
            if _obrigatorio(op.field):
                saida.append(('PERIGO', f'coluna nova obrigatória {campo} sem db_default — o código antigo não a '
                                        'preenche e falha ao criar registos (usa db_default= ou null=True)'))
        elif isinstance(op, ops.AlterField):
            antes = estado.models.get(chave)
            velho = antes.fields.get(op.name) if antes else None
            if velho is not None:
                if velho.null and _obrigatorio(op.field):
                    saida.append(('PERIGO', f'{campo} passa a obrigatório — o código antigo pode gravá-lo vazio'))
                if not (velho.unique or velho.primary_key) and op.field.unique:
                    saida.append(('PERIGO', f'{campo} passa a único — o código antigo não garante valores diferentes'))
        elif type(op) in PERIGOSAS:
            saida.append(('PERIGO', PERIGOSAS[type(op)].format(campo=campo, modelo=modelo)))
        elif isinstance(op, (ops.RunPython, ops.RunSQL)):
            saida.append(('AVISO', f'{type(op).__name__} — ver se é rápido e se não depende do código novo'))
        elif isinstance(op, ops.AlterUniqueTogether) or isinstance(op, SEGURAS):
            if isinstance(op, ops.AlterUniqueTogether) and op.unique_together:
                saida.append(('AVISO', f'unique_together em {modelo} — o código antigo não o garante'))
        else:
            saida.append(('AVISO', f'{type(op).__name__} — operação não conhecida pelo verificador, ver à mão'))
        op.state_forwards(app, estado)
    return saida


class Command(BaseCommand):
    help = 'As migrações por aplicar são seguras para o código que ainda está no ar? (ver o docstring)'

    def add_arguments(self, parser):
        parser.add_argument('--desde', help='app:NNNN — como se só estivesse aplicado até aí (ensaio)')
        parser.add_argument('--database', default=DEFAULT_DB_ALIAS)

    def handle(self, *args, **o):
        executor = MigrationExecutor(connections[o['database']])
        loader = executor.loader
        folhas = loader.graph.leaf_nodes()
        if o['desde']:
            app, _, nome = o['desde'].partition(':')
            try:
                alvo = loader.get_migration_by_prefix(app, nome)
            except Exception as e:
                raise CommandError(f'--desde: {e}')
            feito = set(loader.graph.forwards_plan((app, alvo.name)))
            # as outras apps: o que já está aplicado nesta base de dados
            feito |= {n for n in loader.applied_migrations if n[0] != app}
            plano = [loader.graph.nodes[n] for f in folhas for n in loader.graph.forwards_plan(f) if n not in feito]
            plano = list(dict.fromkeys(plano))
            estado = loader.graph.make_state(nodes=list(feito), at_end=True, real_apps=loader.unmigrated_apps)
        else:
            plano = [m for m, para_tras in executor.migration_plan(folhas) if not para_tras]
            estado = executor._create_project_state(with_applied_migrations=True)
        if not plano:
            self.stdout.write('Nada por aplicar.')
            return
        perigos = 0
        criados = set()
        for m in plano:
            achados = analisar(m, estado, criados)
            marca = 'PERIGO' if any(n == 'PERIGO' for n, _ in achados) else ('aviso' if achados else 'ok')
            self.stdout.write(f'  [{marca}] {m.app_label}.{m.name}')
            for nivel, texto in achados:
                self.stdout.write(f'      {nivel}: {texto}')
                perigos += nivel == 'PERIGO'
        if perigos:
            self.stdout.write(self.style.ERROR(
                f'\n{perigos} perigo(s): o código antigo vai falhar entre a migração e o fim do deploy. Usa db_default '
                'ou divide em dois deploys (ver python manage.py help verificar_migracoes).'))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(f'\n{len(plano)} migração(ões) seguras para o código no ar.'))
