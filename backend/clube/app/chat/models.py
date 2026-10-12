"""
Chat por caixas de mensagens.

Cada pessoa tem UMA conta; o que muda é "como quem fala":
  • Caixa pessoal   — o utilizador (cliente, ou membro de equipa a título pessoal)
  • Caixa da loja   — partilhada pela equipa que atende o chat da loja
  • Caixa de suporte — a "Suporte Bendi" (superchat da plataforma)

Quem pode falar com quem está em app/chat/regras.py (o servidor aplica sempre).
"""
from django.db import models
from django.db.models import Q

from app.models import Utilizador, Loja, Encomenda, Produto
from .imagens import armazenamento_privado


class Caixa(models.Model):
    PESSOAL = 'pessoal'
    LOJA    = 'loja'
    SUPORTE = 'suporte'
    TIPOS = [(PESSOAL, 'Pessoal'), (LOJA, 'Loja'), (SUPORTE, 'Suporte Bendi')]

    tipo       = models.CharField(max_length=10, choices=TIPOS)
    utilizador = models.OneToOneField(Utilizador, null=True, blank=True, on_delete=models.CASCADE,
                                      related_name='caixa_chat')
    loja       = models.OneToOneField(Loja, null=True, blank=True, on_delete=models.CASCADE,
                                      related_name='caixa_chat')
    criada_em  = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name='caixa_dono_coerente',
                check=(Q(tipo='pessoal', utilizador__isnull=False, loja__isnull=True)
                       | Q(tipo='loja', loja__isnull=False, utilizador__isnull=True)
                       | Q(tipo='suporte', utilizador__isnull=True, loja__isnull=True)),
            ),
            # só existe uma caixa "Suporte Bendi"
            models.UniqueConstraint(fields=['tipo'], condition=Q(tipo='suporte'), name='uma_caixa_suporte'),
        ]

    def __str__(self):
        if self.tipo == self.PESSOAL:
            return f'Pessoal · {self.utilizador}'
        if self.tipo == self.LOJA:
            return f'Loja · {self.loja}'
        return 'Suporte Bendi'

    # ── obter (cria na primeira vez) ─────────────────────────────
    @classmethod
    def de_utilizador(cls, utilizador):
        return cls.objects.get_or_create(tipo=cls.PESSOAL, utilizador=utilizador)[0]

    @classmethod
    def de_loja(cls, loja):
        return cls.objects.get_or_create(tipo=cls.LOJA, loja=loja)[0]

    @classmethod
    def suporte(cls):
        return cls.objects.get_or_create(tipo=cls.SUPORTE)[0]


class Conversa(models.Model):
    CLIENTE_LOJA  = 'cliente_loja'    # cliente ↔ loja (geral, ou de uma encomenda)
    SUPORTE       = 'suporte'         # utilizador ou loja ↔ Suporte Bendi
    EQUIPA_GRUPO  = 'equipa_grupo'    # grupo da equipa de uma loja
    EQUIPA_DIRETA = 'equipa_direta'   # dois membros da mesma loja
    TIPOS = [
        (CLIENTE_LOJA, 'Cliente ↔ Loja'),
        (SUPORTE, 'Suporte'),
        (EQUIPA_GRUPO, 'Equipa (grupo)'),
        (EQUIPA_DIRETA, 'Equipa (directa)'),
    ]

    ABERTA, FECHADA = 'aberta', 'fechada'
    ESTADOS = [(ABERTA, 'Aberta'), (FECHADA, 'Fechada')]

    tipo      = models.CharField(max_length=15, choices=TIPOS)
    # loja do contexto: a do cliente_loja, ou a da equipa
    loja      = models.ForeignKey(Loja, null=True, blank=True, on_delete=models.CASCADE, related_name='conversas_chat')
    # conversa própria de uma encomenda (o condutor da entrega só vê estas)
    encomenda = models.ForeignKey(Encomenda, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='conversas_chat')
    assunto   = models.CharField(max_length=120, blank=True, default='')
    estado    = models.CharField(max_length=8, choices=ESTADOS, default=ABERTA)
    # identidade única da conversa (evita duplicados com pedidos em simultâneo):
    #   cl:<caixa cliente>:<loja>  ·  enc:<encomenda>  ·  sup:<caixa>  ·  grp:<loja>  ·  dir:<loja>:<caixa>:<caixa>
    chave     = models.CharField(max_length=80, unique=True)

    criada_em          = models.DateTimeField(auto_now_add=True)
    ultima_mensagem_em = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-ultima_mensagem_em', '-id']
        constraints = [
            # um só grupo de equipa por loja
            models.UniqueConstraint(fields=['loja'], condition=Q(tipo='equipa_grupo'), name='um_grupo_por_loja'),
            # uma só conversa por encomenda
            models.UniqueConstraint(fields=['encomenda'], condition=Q(encomenda__isnull=False),
                                    name='uma_conversa_por_encomenda'),
        ]

    def __str__(self):
        return f'Conversa #{self.pk} ({self.get_tipo_display()})'


class Participante(models.Model):
    """Uma caixa numa conversa + estado de leitura dessa caixa."""
    conversa   = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name='participantes')
    caixa      = models.ForeignKey(Caixa, on_delete=models.CASCADE, related_name='participacoes')
    # id da última mensagem lida (o ✓✓ de quem envia)
    ultima_lida = models.BigIntegerField(default=0)
    silenciada = models.BooleanField(default=False)
    arquivada  = models.BooleanField(default=False)
    entrou_em  = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['conversa', 'caixa'], name='participante_unico')]
        indexes = [models.Index(fields=['caixa', 'conversa'])]

    def __str__(self):
        return f'{self.caixa} em {self.conversa}'


def anexo_chat_upload(instance, filename):
    # pasta dentro do armazenamento privado (o nome do ficheiro já vem aleatório)
    from django.utils.timezone import now
    return f'chat_privado/{now():%Y/%m}/{filename}'


class Mensagem(models.Model):
    TEXTO, IMAGEM, SISTEMA = 'texto', 'imagem', 'sistema'
    TIPOS = [(TEXTO, 'Texto'), (IMAGEM, 'Imagem'), (SISTEMA, 'Sistema')]

    conversa  = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name='mensagens')
    # "como quem" foi enviada (ex.: a caixa da loja) …
    remetente = models.ForeignKey(Caixa, null=True, on_delete=models.SET_NULL, related_name='mensagens_enviadas')
    # … e quem a escreveu de facto (a equipa vê "respondido por João")
    autor     = models.ForeignKey(Utilizador, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='mensagens_chat')
    tipo      = models.CharField(max_length=8, choices=TIPOS, default=TEXTO)
    texto     = models.TextField(blank=True, default='')
    # privado: bucket/pasta própria, servido só por link assinado (ver imagens.py)
    anexo     = models.FileField(upload_to=anexo_chat_upload, storage=armazenamento_privado, null=True, blank=True)
    anexo_largura = models.PositiveIntegerField(null=True, blank=True)
    anexo_altura  = models.PositiveIntegerField(null=True, blank=True)
    # "cartão" de contexto dentro da conversa geral (ex.: dúvida sobre um produto)
    produto   = models.ForeignKey(Produto, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    apagada   = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['id']
        indexes = [models.Index(fields=['conversa', 'id'])]

    def __str__(self):
        return f'Mensagem #{self.pk} em {self.conversa_id}'


class Bloqueio(models.Model):
    """`caixa` deixa de receber mensagens de `bloqueada` (e não pode iniciar conversa com ela)."""
    caixa     = models.ForeignKey(Caixa, on_delete=models.CASCADE, related_name='bloqueios')
    bloqueada = models.ForeignKey(Caixa, on_delete=models.CASCADE, related_name='bloqueado_por')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['caixa', 'bloqueada'], name='bloqueio_unico')]


class Denuncia(models.Model):
    PENDENTE, RESOLVIDA = 'pendente', 'resolvida'
    ESTADOS = [(PENDENTE, 'Pendente'), (RESOLVIDA, 'Resolvida')]

    conversa   = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name='denuncias')
    mensagem   = models.ForeignKey(Mensagem, null=True, blank=True, on_delete=models.SET_NULL, related_name='denuncias')
    denunciante = models.ForeignKey(Utilizador, null=True, on_delete=models.SET_NULL, related_name='denuncias_chat')
    motivo     = models.CharField(max_length=500)
    estado     = models.CharField(max_length=10, choices=ESTADOS, default=PENDENTE)
    resolvida_por = models.ForeignKey(Utilizador, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    nota       = models.CharField(max_length=500, blank=True, default='')
    criada_em  = models.DateTimeField(auto_now_add=True)
    resolvida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criada_em']
