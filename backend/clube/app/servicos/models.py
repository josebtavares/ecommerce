"""
Serviços e marcações (doc "Serviços e Marcações — Fase 1").

- Uma loja activa o módulo (ConfigServicos). Em subscrição já está incluído; em comissão paga a
  subscrição de Serviços (Subscricao.loja_servicos) — ver utils/servicos_cobranca.py.
- Profissional = quem presta o serviço; não é obrigatório ter conta (membro é opcional).
- Marcacao nunca se apaga (registo financeiro): cancela-se. Dois intervalos activos do mesmo
  profissional nunca se sobrepõem (restrição de exclusão no Postgres, migração 0001).
"""
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Func, Q

from ..models import Loja, UtilizadorLoja, Utilizador


class TsTzRange(Func):
    function = 'TSTZRANGE'
    output_field = DateTimeRangeField()


def servico_imagem_upload(instance, filename):
    return f'servicos/{instance.servico.loja_id}/{instance.servico_id}/{filename}'


def profissional_foto_upload(instance, filename):
    return f'servicos/{instance.loja_id}/profissionais/{filename}'


class ConfigServicos(models.Model):
    """O módulo Serviços de uma loja e as regras das marcações."""
    CONFIRMACAO = [('auto', 'Automática'), ('manual', 'A loja confirma')]
    REEMBOLSO = [('total', 'Reembolso total'), ('nenhum', 'Sem reembolso')]

    loja                  = models.OneToOneField(Loja, on_delete=models.CASCADE, related_name='config_servicos')
    ativo                 = models.BooleanField(default=False)
    ativado_em            = models.DateTimeField(null=True, blank=True)
    confirmacao           = models.CharField(max_length=6, choices=CONFIRMACAO, default='auto')
    antecedencia_min      = models.PositiveIntegerField(default=60, validators=[MaxValueValidator(60 * 24 * 30)])
    dias_max              = models.PositiveSmallIntegerField(default=60, validators=[MinValueValidator(1), MaxValueValidator(365)])
    cancelar_horas        = models.PositiveSmallIntegerField(default=24, validators=[MaxValueValidator(24 * 30)])
    # cancelamento fora de prazo / falta de uma marcação paga antecipadamente
    reembolso_fora_prazo  = models.CharField(max_length=6, choices=REEMBOLSO, default='nenhum')
    cliente_escolhe_profissional = models.BooleanField(default=True)
    profissional_altera_preco    = models.BooleanField(default=False)
    data_atualizacao      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Serviços de {self.loja} ({"activo" if self.ativo else "desligado"})'


class Profissional(models.Model):
    loja       = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='profissionais')
    nome       = models.CharField(max_length=100)
    foto       = models.ImageField(upload_to=profissional_foto_upload, null=True, blank=True)
    descricao  = models.CharField(max_length=300, blank=True, default='')
    # conta de staff ligada (vê a sua agenda no backoffice); SET_NULL: sair da equipa não apaga a ficha
    membro     = models.OneToOneField(UtilizadorLoja, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='profissional')
    ativo      = models.BooleanField(default=True)
    ordem      = models.PositiveSmallIntegerField(default=0)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'nome', 'id']

    def __str__(self):
        return f'{self.nome} @ {self.loja}'


class HorarioProfissional(models.Model):
    """Blocos semanais (0 = segunda). Sem blocos = segue o horário da loja."""
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='horarios')
    dia_semana   = models.PositiveSmallIntegerField(validators=[MaxValueValidator(6)])
    inicio       = models.TimeField()
    fim          = models.TimeField()

    class Meta:
        ordering = ['dia_semana', 'inicio']
        constraints = [models.CheckConstraint(check=models.Q(fim__gt=models.F('inicio')), name='horario_prof_fim_depois')]


class AusenciaProfissional(models.Model):
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='ausencias')
    inicio       = models.DateTimeField()
    fim          = models.DateTimeField()
    motivo       = models.CharField(max_length=200, blank=True, default='')
    criada_por   = models.CharField(max_length=100, blank=True, default='')
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['inicio']
        constraints = [models.CheckConstraint(check=models.Q(fim__gt=models.F('inicio')), name='ausencia_fim_depois')]


class Servico(models.Model):
    TIPOS_PRECO = [('fixo', 'Preço fixo'), ('a_partir', 'A partir de')]
    PAGAMENTOS = [('ambos', 'Antecipado ou no local'), ('antecipado', 'Só antecipado'), ('local', 'Só no local')]

    loja           = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='servicos')
    nome           = models.CharField(max_length=120)
    descricao      = models.TextField(blank=True, default='')
    categoria      = models.CharField(max_length=80, blank=True, default='')
    duracao_min    = models.PositiveSmallIntegerField(validators=[MinValueValidator(5), MaxValueValidator(60 * 12)])
    # tempo livre depois (limpar, preparar) — ocupa a agenda mas não aparece ao cliente
    intervalo_min  = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(240)])
    tipo_preco     = models.CharField(max_length=8, choices=TIPOS_PRECO, default='fixo')
    preco          = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    pagamento      = models.CharField(max_length=10, choices=PAGAMENTOS, default='ambos')
    profissionais  = models.ManyToManyField(Profissional, related_name='servicos', blank=True)
    ativo          = models.BooleanField(default=True)
    ordem          = models.PositiveSmallIntegerField(default=0)
    data_criacao   = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordem', 'nome', 'id']

    def __str__(self):
        return f'{self.nome} ({self.duracao_min} min) @ {self.loja}'


class ServicoImagem(models.Model):
    servico  = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='imagens')
    ficheiro = models.ImageField(upload_to=servico_imagem_upload)
    ordem    = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'id']


class Marcacao(models.Model):
    ESTADOS = [
        ('pendente',   'Pendente'),
        ('confirmada', 'Confirmada'),
        ('concluida',  'Concluída'),
        ('cancelada',  'Cancelada'),
        ('falta',      'Falta'),
        ('expirada',   'Expirada'),
    ]
    # estes seguram o horário (entram na restrição de exclusão)
    ATIVOS = ('pendente', 'confirmada')
    PAGAMENTOS = [('antecipado', 'Antecipado'), ('local', 'No local')]

    loja          = models.ForeignKey(Loja, on_delete=models.PROTECT, related_name='marcacoes')
    servico       = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name='marcacoes')
    profissional  = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name='marcacoes')
    cliente       = models.ForeignKey(Utilizador, on_delete=models.PROTECT, related_name='marcacoes', null=True, blank=True)
    # marcação manual (cliente ao telefone / balcão) sem conta
    cliente_nome  = models.CharField(max_length=120, blank=True, default='')
    cliente_telefone = models.CharField(max_length=30, blank=True, default='')
    # snapshot do serviço quando foi marcado
    servico_nome  = models.CharField(max_length=120)
    duracao_min   = models.PositiveSmallIntegerField()
    tipo_preco    = models.CharField(max_length=8, default='fixo')
    inicio        = models.DateTimeField(db_index=True)
    fim           = models.DateTimeField()                 # fim do serviço
    ocupado_ate   = models.DateTimeField()                 # fim + intervalo (o que a agenda bloqueia)
    estado        = models.CharField(max_length=10, choices=ESTADOS, default='pendente', db_index=True)
    preco_indicado = models.DecimalField(max_digits=10, decimal_places=2)
    preco_final   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_final_por    = models.CharField(max_length=100, blank=True, default='')
    preco_final_motivo = models.CharField(max_length=200, blank=True, default='')
    pagamento     = models.CharField(max_length=10, choices=PAGAMENTOS, default='local')
    pago          = models.BooleanField(default=False)
    pago_em       = models.DateTimeField(null=True, blank=True)
    # a marcação por pagar segura o horário até aqui; depois expira
    expira_em     = models.DateTimeField(null=True, blank=True)
    notas_cliente = models.CharField(max_length=500, blank=True, default='')
    notas_internas = models.CharField(max_length=500, blank=True, default='')
    criada_por    = models.CharField(max_length=100, blank=True, default='')
    cancelada_em  = models.DateTimeField(null=True, blank=True)
    cancelada_por = models.CharField(max_length=100, blank=True, default='')
    cancelada_motivo = models.CharField(max_length=200, blank=True, default='')
    concluida_em  = models.DateTimeField(null=True, blank=True)
    # pagamento antecipado (simulado): quanto entrou e quanto a loja tem de devolver (cancelamento, falta,
    # preço novo/final mais baixo); a devolução é feita logo (marcacoes.reembolsar)
    valor_pago    = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_default=0)
    reembolso_devido = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_default=0)
    # o que já foi devolvido (simulado, para o meio de pagamento) e quando
    valor_reembolsado = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_default=0)
    reembolsado_em = models.DateTimeField(null=True, blank=True)
    # conversa: até quando cada lado leu (mensagens por ler)
    lida_cliente_em = models.DateTimeField(null=True, blank=True)
    lida_loja_em  = models.DateTimeField(null=True, blank=True)
    # lembretes já enviados ('vespera'…) — o worker não os repete
    avisos        = models.JSONField(default=list, blank=True)
    data_criacao  = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['inicio', 'id']
        indexes = [models.Index(fields=['loja', 'inicio']), models.Index(fields=['profissional', 'inicio'])]
        constraints = [
            models.CheckConstraint(check=models.Q(fim__gt=models.F('inicio')), name='marcacao_fim_depois'),
            models.CheckConstraint(check=models.Q(ocupado_ate__gte=models.F('fim')), name='marcacao_ocupado_depois'),
            # o mesmo profissional nunca tem duas marcações activas a sobrepor-se ([inicio, ocupado_ate))
            ExclusionConstraint(
                name='marcacao_sem_sobreposicao',
                expressions=[(TsTzRange('inicio', 'ocupado_ate', RangeBoundary()), RangeOperators.OVERLAPS),
                             ('profissional', RangeOperators.EQUAL)],
                condition=Q(estado__in=('pendente', 'confirmada')),
            ),
        ]

    @property
    def preco(self):
        """O que o cliente paga: o final, se a loja o registou, senão o indicado."""
        return self.preco_final if self.preco_final is not None else self.preco_indicado

    def __str__(self):
        return f'Marcação #{self.pk} {self.servico_nome} {self.inicio:%d/%m %H:%M} ({self.estado})'


class ReatribuicaoMarcacao(models.Model):
    """Histórico: a loja passou a marcação de um profissional para outro."""
    marcacao     = models.ForeignKey(Marcacao, on_delete=models.CASCADE, related_name='reatribuicoes')
    de           = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name='+')
    para         = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name='+')
    por          = models.CharField(max_length=100, blank=True, default='')
    motivo       = models.CharField(max_length=200, blank=True, default='')
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_criacao', 'id']


# ══════════════════════════════════════════════════════════════
# CONVERSA DA MARCAÇÃO (cliente ↔ loja/profissional) E PROPOSTAS DE PREÇO
# ══════════════════════════════════════════════════════════════

def _armazenamento_privado():
    # as fotos da conversa são privadas, como as do chat e dos reembolsos
    from ..chat.imagens import armazenamento_privado
    return armazenamento_privado()


def foto_marcacao_upload(instance, filename):
    from django.utils.timezone import now
    return f'marcacoes_privado/{now():%Y/%m}/{filename}'


class PropostaPreco(models.Model):
    """A loja propõe um preço novo; o cliente aceita ou recusa. Uma pendente de cada vez."""
    ESTADOS = [('pendente', 'À espera do cliente'), ('aceite', 'Aceite'), ('recusada', 'Recusada'), ('anulada', 'Substituída')]

    marcacao     = models.ForeignKey(Marcacao, on_delete=models.CASCADE, related_name='propostas')
    valor        = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    valor_antes  = models.DecimalField(max_digits=10, decimal_places=2)
    motivo       = models.CharField(max_length=300, blank=True, default='')
    estado       = models.CharField(max_length=10, choices=ESTADOS, default='pendente')
    criada_por   = models.CharField(max_length=100, blank=True, default='')
    respondida_em = models.DateTimeField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']


class MensagemMarcacao(models.Model):
    PAPEIS = [('cliente', 'Cliente'), ('loja', 'Loja'), ('sistema', 'Sistema')]

    marcacao  = models.ForeignKey(Marcacao, on_delete=models.CASCADE, related_name='mensagens')
    autor     = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    autor_nome = models.CharField(max_length=100, blank=True, default='')
    papel     = models.CharField(max_length=10, choices=PAPEIS)
    texto     = models.TextField(blank=True, default='')
    proposta  = models.ForeignKey(PropostaPreco, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']


class FotoMarcacao(models.Model):
    marcacao  = models.ForeignKey(Marcacao, on_delete=models.CASCADE, related_name='fotos')
    mensagem  = models.ForeignKey(MensagemMarcacao, on_delete=models.SET_NULL, null=True, blank=True, related_name='fotos')
    autor     = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    ficheiro  = models.FileField(upload_to=foto_marcacao_upload, storage=_armazenamento_privado)
    criada_em = models.DateTimeField(auto_now_add=True)
