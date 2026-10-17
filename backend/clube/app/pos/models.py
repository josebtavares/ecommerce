"""
Modelos do Sistema POS (Point of Sale)
Suporta modo standalone, integrado e híbrido.
- standalone: usa apenas ProdutoPOS
- integrado: usa apenas produtos da loja Bendi
- hibrido: usa ProdutoPOS + produtos da loja Bendi
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
import uuid
from django.contrib.auth.hashers import make_password, check_password

class ConfiguracaoPOS(models.Model):
    """
    Configuração central de cada instância POS.
    Cada POS pode estar vinculado a uma loja ou funcionar de forma independente.
    """

    codigo_pos = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Código POS',
        help_text='Código único gerado automaticamente (ex: POS-A1B2C3D4)'
    )

    nome = models.CharField(
        max_length=100,
        verbose_name='Nome do POS',
        help_text='Ex: "POS Principal", "POS Esplanada", "Caixa 1"'
    )

    dono = models.ForeignKey(
        'app.Utilizador',
        on_delete=models.CASCADE,
        related_name='pos_geridos',
        verbose_name='Dono do POS'
    )

    loja_vinculada = models.ForeignKey(
        'app.Loja',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_vinculados',
        verbose_name='Loja vinculada',
        help_text='Se preenchido, POS pode usar catálogo e stock da loja'
    )

    MODO_CHOICES = [
        ('standalone', 'Standalone - Apenas produtos próprios do POS'),
        ('integrado', 'Integrado - Apenas catálogo da loja Bendi'),
        ('hibrido', 'Híbrido - Produtos próprios + catálogo da loja Bendi'),
    ]

    modo = models.CharField(
        max_length=20,
        choices=MODO_CHOICES,
        default='standalone',
        verbose_name='Modo de operação'
    )

    taxa_servico_ativa = models.BooleanField(
        default=True,
        verbose_name='Taxa de serviço ativa',
        help_text='Se ativo, aplica taxa de serviço nas contas'
    )

    taxa_servico_percentagem = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        verbose_name='Taxa de serviço (%)',
        help_text='Percentagem aplicada sobre o subtotal (ex: 10 = 10%)'
    )

    efatura_ativo = models.BooleanField(
        default=False,
        verbose_name='eFatura ativo',
        help_text='Se ativo, emite faturas via eFatura CV'
    )

    efatura_nif = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='NIF',
        help_text='NIF registado no eFatura Cabo Verde'
    )

    efatura_api_key = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='API Key eFatura',
        help_text='Chave de API do eFatura CV'
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name='POS ativo',
        help_text='POS inativos não aparecem na lista'
    )

    # Suspensão pela plataforma (admin Bendi) — distinto de `ativo`, que é do dono.
    # Um POS suspenso não opera (vendas, mesas, produtos, login de membros).
    suspenso = models.BooleanField(default=False)
    suspenso_motivo = models.CharField(max_length=300, blank=True, default='')
    suspenso_em = models.DateTimeField(null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Configuração POS'
        verbose_name_plural = 'Configurações POS'
        ordering = ['-criado_em']

    def __str__(self):
        if self.loja_vinculada:
            return f"{self.nome} ({self.get_modo_display()} - Loja: {self.loja_vinculada.nome})"
        return f"{self.nome} ({self.get_modo_display()})"

    def save(self, *args, **kwargs):
        if not self.codigo_pos:
            self.codigo_pos = f"POS-{uuid.uuid4().hex[:8].upper()}"

        if self.modo == 'integrado' and not self.loja_vinculada:
            self.modo = 'standalone'

        super().save(*args, **kwargs)

    def conectar_loja(self, loja, modo='integrado'):
        """
        Conecta o POS a uma loja.
        modo pode ser:
        - integrado: usa apenas produtos da loja
        - hibrido: usa produtos próprios + produtos da loja
        """
        if modo not in ['integrado', 'hibrido']:
            modo = 'integrado'

        self.loja_vinculada = loja
        self.modo = modo
        self.save(update_fields=['loja_vinculada', 'modo', 'atualizado_em'])

    def desconectar_loja(self):
        """
        Desconecta da loja e volta ao modo standalone.
        ProdutosPOS continuam intactos.
        """
        self.loja_vinculada = None
        self.modo = 'standalone'
        self.save(update_fields=['loja_vinculada', 'modo', 'atualizado_em'])


class Mesa(models.Model):
    """
    Mesa física do restaurante/café.
    Pertence a um POS.
    """
    pos = models.ForeignKey(
        ConfiguracaoPOS,
        on_delete=models.CASCADE,
        related_name='mesas',
        verbose_name='POS'
    )

    numero = models.CharField(
        max_length=10,
        verbose_name='Número/Nome',
        help_text='Ex: "Mesa 1", "Balcão", "Esplanada 5"'
    )

    capacidade = models.IntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name='Capacidade'
    )

    STATUS_CHOICES = [
        ('livre', 'Livre'),
        ('ocupada', 'Ocupada'),
        ('reservada', 'Reservada'),
        ('limpeza', 'Em limpeza'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='livre',
        verbose_name='Status atual'
    )

    atendente_atual = models.ForeignKey(
        'app.Utilizador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mesas_atendendo',
        verbose_name='Atendente atual'
    )

    aberta_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Aberta em'
    )

    ativa = models.BooleanField(
        default=True,
        verbose_name='Mesa ativa'
    )

    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'
        unique_together = ['pos', 'numero']
        ordering = ['numero']

    def __str__(self):
        return f"{self.pos.nome} - {self.numero} ({self.get_status_display()})"

    def abrir(self, atendente):
        self.status = 'ocupada'
        self.atendente_atual = atendente
        self.aberta_em = timezone.now()
        self.save(update_fields=['status', 'atendente_atual', 'aberta_em'])

    def fechar(self):
        self.status = 'livre'
        self.atendente_atual = None
        self.aberta_em = None
        self.save(update_fields=['status', 'atendente_atual', 'aberta_em'])

    def marcar_limpeza(self):
        self.status = 'limpeza'
        self.save(update_fields=['status'])


class ProdutoPOS(models.Model):
    """
    Produto próprio do POS.
    Usado em modo standalone e híbrido.
    Não depende de Loja.
    """
    pos = models.ForeignKey(
        ConfiguracaoPOS,
        on_delete=models.CASCADE,
        related_name='produtos_pos',
        verbose_name='POS'
    )

    nome = models.CharField(max_length=200, verbose_name='Nome')
    descricao = models.TextField(blank=True, default='', verbose_name='Descrição')
    categoria = models.CharField(max_length=100, blank=True, default='Sem categoria')
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Preço'
    )

    imagem = models.ImageField(
        upload_to='pos/produtos/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Imagem'
    )

    controlar_stock = models.BooleanField(default=False, verbose_name='Controlar stock')
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    # Tipo e atributos (globais ou tipos próprios do POS) — mesmo formato da loja
    tipo = models.ForeignKey(
        'app.TipoProduto', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='produtos_pos',
    )
    atributos = models.JSONField(default=dict, blank=True)
    # True → stock gerido por VarianteProdutoPOS; `stock` passa a ser a soma das variantes
    stock_por_variante = models.BooleanField(default=False)
    # Conjunto/menu feito de produtos do POS e/ou da loja Bendi ligada (ComponenteConjuntoPOS);
    # sem stock próprio — vender desconta o stock de cada componente
    e_conjunto = models.BooleanField(default=False)

    ativo = models.BooleanField(default=True)
    disponivel_pos = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produto POS'
        verbose_name_plural = 'Produtos POS'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['pos', 'ativo']),
            models.Index(fields=['pos', 'categoria']),
        ]

    def __str__(self):
        return f"{self.nome} - {self.pos.nome}"

    @property
    def disponivel(self):
        if not self.ativo or not self.disponivel_pos:
            return False

        if self.controlar_stock:
            return self.stock > 0

        return True


class VarianteProdutoPOS(models.Model):
    """
    Combinação de opções de um produto próprio do POS, com stock próprio.
    Espelha app.VarianteProduto (mesma lógica em app/utils/variantes.py).
    """
    produto    = models.ForeignKey(ProdutoPOS, on_delete=models.CASCADE, related_name='variantes')
    combinacao = models.JSONField(default=dict)
    chave      = models.CharField(max_length=500)
    quantidade = models.PositiveIntegerField(default=0)
    preco      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                     validators=[MinValueValidator(Decimal('0.00'))])
    sku        = models.CharField(max_length=100, blank=True, default='')
    ativo      = models.BooleanField(default=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('produto', 'chave')]
        ordering = ['chave']

    @property
    def preco_efetivo(self):
        return self.preco if self.preco is not None else self.produto.preco

    def descricao(self):
        return ' · '.join(str(v) for v in self.combinacao.values())

    def __str__(self):
        return f'{self.produto.nome} [{self.descricao()}] — {self.quantidade} un.'


class ComponenteConjuntoPOS(models.Model):
    """
    Um produto dentro de um conjunto do POS. Pode ser um produto do próprio POS (produto_pos)
    ou, num POS híbrido, um produto da loja Bendi ligada (produto) — exactamente um dos dois.
    Se a loja for suspensa/desligada, o conjunto fica indisponível até o dono substituir o
    componente (ver pos/views_conjuntos.py — "substituir").
    """
    conjunto     = models.ForeignKey(ProdutoPOS, on_delete=models.CASCADE, related_name='componentes')
    produto      = models.ForeignKey('app.Produto', on_delete=models.RESTRICT, null=True, blank=True,
                                     related_name='em_conjuntos_pos')
    produto_pos  = models.ForeignKey(ProdutoPOS, on_delete=models.RESTRICT, null=True, blank=True,
                                     related_name='em_conjuntos')
    variante     = models.ForeignKey('app.VarianteProduto', on_delete=models.RESTRICT, null=True, blank=True,
                                     related_name='em_conjuntos_pos')
    variante_pos = models.ForeignKey(VarianteProdutoPOS, on_delete=models.RESTRICT, null=True, blank=True,
                                     related_name='em_conjuntos')
    quantidade   = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    variante_livre = models.BooleanField(default=False)   # o cliente escolhe a variação
    ordem        = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'produto num menu do POS'
        ordering = ['ordem', 'id']
        constraints = [
            models.CheckConstraint(
                check=(models.Q(produto__isnull=False, produto_pos__isnull=True) |
                       models.Q(produto__isnull=True, produto_pos__isnull=False)),
                name='componente_pos_uma_origem'),
            models.CheckConstraint(check=~models.Q(conjunto=models.F('produto_pos')),
                                   name='conjunto_pos_nao_se_contem'),
        ]

    @property
    def origem(self):
        return 'pos' if self.produto_pos_id else 'loja'

    def __str__(self):
        alvo = self.produto_pos or self.produto
        return f'{self.quantidade}× {alvo} em {self.conjunto.nome}'


class GrupoEscolhaPOS(models.Model):
    """Escolha dentro de um menu do POS (ex.: "Bebida — escolhe 1"). Ver app.GrupoEscolha."""
    conjunto = models.ForeignKey(ProdutoPOS, on_delete=models.CASCADE, related_name='grupos')
    nome     = models.CharField(max_length=60)
    minimo   = models.PositiveSmallIntegerField(default=1)
    maximo   = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    ordem    = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'escolha num menu do POS'
        ordering = ['ordem', 'id']
        constraints = [
            models.CheckConstraint(check=models.Q(minimo__lte=models.F('maximo')), name='grupo_pos_minimo_ate_maximo'),
        ]


class OpcaoEscolhaPOS(models.Model):
    """Opção de uma escolha do POS: produto do POS ou (POS híbrido) da loja Bendi — exactamente um."""
    grupo        = models.ForeignKey(GrupoEscolhaPOS, on_delete=models.CASCADE, related_name='opcoes')
    produto      = models.ForeignKey('app.Produto', on_delete=models.RESTRICT, null=True, blank=True,
                                     related_name='em_opcoes_pos')
    produto_pos  = models.ForeignKey(ProdutoPOS, on_delete=models.RESTRICT, null=True, blank=True,
                                     related_name='em_opcoes')
    variante     = models.ForeignKey('app.VarianteProduto', on_delete=models.RESTRICT, null=True, blank=True,
                                     related_name='em_opcoes_pos')
    variante_pos = models.ForeignKey(VarianteProdutoPOS, on_delete=models.RESTRICT, null=True, blank=True,
                                     related_name='em_opcoes')
    quantidade   = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    variante_livre = models.BooleanField(default=False)   # o cliente escolhe a variação
    preco_extra  = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                       validators=[MinValueValidator(Decimal('0.00'))])
    ordem        = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'opção num menu do POS'
        ordering = ['ordem', 'id']
        constraints = [
            models.CheckConstraint(
                check=(models.Q(produto__isnull=False, produto_pos__isnull=True) |
                       models.Q(produto__isnull=True, produto_pos__isnull=False)),
                name='opcao_pos_uma_origem'),
        ]

    @property
    def origem(self):
        return 'pos' if self.produto_pos_id else 'loja'


class ContaMesa(models.Model):
    """
    Conta/pedido de uma mesa.
    Agrupa todos os items consumidos numa sessão.
    """
    pos = models.ForeignKey(
        ConfiguracaoPOS,
        on_delete=models.PROTECT,      # vendas do POS são registos financeiros
        related_name='contas',
        verbose_name='POS'
    )

    mesa = models.ForeignKey(
        Mesa,
        on_delete=models.PROTECT,      # apagar uma mesa nunca apaga as contas dela
        related_name='contas',
        verbose_name='Mesa'
    )

    atendente = models.ForeignKey(
        'app.Utilizador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_atendidas',
        verbose_name='Atendente'
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    taxa_servico_percentagem = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    taxa_servico_valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    gorjeta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    desconto_valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('fechada', 'Fechada/Paga'),
        ('cancelada', 'Cancelada'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberta')

    METODO_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('cartao', 'Cartão de Crédito/Débito'),
        ('mbway', 'MBWay'),
        ('transferencia', 'Transferência Bancária'),
        ('dividida', 'Conta Dividida'),
    ]

    metodo_pagamento = models.CharField(
        max_length=20,
        choices=METODO_PAGAMENTO_CHOICES,
        null=True,
        blank=True
    )

    dividida_em = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )

    nif_cliente = models.CharField(max_length=20, blank=True)
    efatura_processada = models.BooleanField(default=False)
    efatura_codigo = models.CharField(max_length=100, blank=True)
    efatura_url = models.URLField(blank=True)

    observacoes = models.TextField(blank=True)

    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    fechada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Conta de Mesa'
        verbose_name_plural = 'Contas de Mesa'
        ordering = ['-criada_em']
        indexes = [
            models.Index(fields=['pos', 'status']),
            models.Index(fields=['mesa', '-criada_em']),
        ]

    def __str__(self):
        return f"Conta #{self.id} - {self.mesa.numero} - {self.total} CVE"

    def calcular_totais(self):
        # itens cancelados não são cobrados
        self.subtotal = sum(
            item.preco_total for item in self.items.exclude(status='cancelado')
        ) or Decimal('0.00')

        if self.taxa_servico_percentagem > 0:
            # ao centavo (ex.: 12,5% de 1.653$00 = 206$63), como fica gravado — o total bate com a soma
            self.taxa_servico_valor = ((self.subtotal * self.taxa_servico_percentagem) / 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            self.taxa_servico_valor = Decimal('0.00')

        self.total = (
            self.subtotal +
            self.taxa_servico_valor +
            self.gorjeta -
            self.desconto_valor
        )

        if self.total < 0:
            self.total = Decimal('0.00')

        self.save(update_fields=['subtotal', 'taxa_servico_valor', 'total', 'atualizada_em'])

    def fechar(self, metodo_pagamento):
        self.status = 'fechada'
        self.metodo_pagamento = metodo_pagamento
        self.fechada_em = timezone.now()
        self.save(update_fields=['status', 'metodo_pagamento', 'fechada_em'])

        self.mesa.fechar()

    def cancelar(self, motivo=''):
        from .stock import repor_stock_item   # evita import circular
        for item in self.items.exclude(status='cancelado'):
            repor_stock_item(item)
        self.status = 'cancelada'
        if motivo:
            self.observacoes += f"\n[CANCELADA] {motivo} em {timezone.now()}"
        self.save(update_fields=['status', 'observacoes'])


class ItemContaMesa(models.Model):
    """
    Item individual de uma conta.
    Pode referenciar:
    - produto da loja Bendi: produto
    - produto próprio do POS: produto_pos
    """
    conta = models.ForeignKey(
        ContaMesa,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Conta'
    )

    # Produto do e-commerce Bendi.
    # Mantive o nome "produto" para reduzir problemas de migração com o teu campo antigo.
    produto = models.ForeignKey(
        'app.Produto',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='vendas_pos',
        verbose_name='Produto da loja Bendi'
    )

    produto_pos = models.ForeignKey(
        ProdutoPOS,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='vendas',
        verbose_name='Produto próprio do POS'
    )

    # Variação vendida (só uma das duas, conforme a origem do produto)
    variante = models.ForeignKey(
        'app.VarianteProduto', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vendas_pos',
    )
    variante_pos = models.ForeignKey(
        VarianteProdutoPOS, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vendas',
    )
    atributos = models.JSONField(default=dict, blank=True)   # opções escolhidas (snapshot)
    # conjunto: o que levava no momento da venda (cozinha, histórico e reposição do stock)
    # [{"origem": "loja"|"pos", "produto_id", "variante_id", "nome", "quantidade" (por unidade)}]
    componentes = models.JSONField(default=list, blank=True)
    nome = models.CharField(
        max_length=200,
        verbose_name='Nome do produto',
        help_text='Cache do nome no momento da venda'
    )

    quantidade = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    preco_total = models.DecimalField(max_digits=10, decimal_places=2)

    observacoes = models.TextField(blank=True)

    atribuido_pessoa = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )

    STATUS_ITEM_CHOICES = [
        ('pendente', 'Pendente'),
        ('preparando', 'Em preparação'),
        ('pronto', 'Pronto'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_ITEM_CHOICES,
        default='pendente'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item da Conta'
        verbose_name_plural = 'Items da Conta'
        ordering = ['criado_em']
        indexes = [
            models.Index(fields=['conta', 'status']),
        ]

    def __str__(self):
        return f"{self.quantidade}x {self.nome} - {self.preco_total} CVE"

    @property
    def origem(self):
        if self.produto_pos_id:
            return 'pos'
        return 'loja'

    @property
    def produto_ref_id(self):
        if self.produto_pos_id:
            return self.produto_pos_id
        return self.produto_id

    def clean(self):
        if not self.produto and not self.produto_pos:
            raise ValidationError('O item precisa de um produto da loja ou produto POS.')

        if self.produto and self.produto_pos:
            raise ValidationError('O item não pode ter produto da loja e produto POS ao mesmo tempo.')

    def save(self, *args, **kwargs):
        if self.quantidade is None:
            self.quantidade = 1

        if self.preco_unitario is None:
            self.preco_unitario = Decimal('0.00')

        self.preco_total = Decimal(str(self.quantidade)) * Decimal(str(self.preco_unitario))

        self.full_clean(exclude=None)

        super().save(*args, **kwargs)

        if self.conta_id:
            self.conta.calcular_totais()


class PagamentoDividido(models.Model):
    """
    Pagamento individual quando a conta é dividida.
    """
    conta = models.ForeignKey(
        ContaMesa,
        on_delete=models.CASCADE,
        related_name='pagamentos_divididos',
        verbose_name='Conta'
    )

    pessoa_numero = models.IntegerField(validators=[MinValueValidator(1)])
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    metodo = models.CharField(max_length=20, choices=ContaMesa.METODO_PAGAMENTO_CHOICES)
    pago = models.BooleanField(default=False)
    pago_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pagamento Dividido'
        verbose_name_plural = 'Pagamentos Divididos'
        unique_together = ['conta', 'pessoa_numero']
        ordering = ['pessoa_numero']

    def __str__(self):
        status = "✓ Pago" if self.pago else "Pendente"
        return f"Pessoa {self.pessoa_numero} - {self.valor} CVE ({status})"

    def marcar_como_pago(self):
        self.pago = True
        self.pago_em = timezone.now()
        self.save(update_fields=['pago', 'pago_em'])


class TurnoPOS(models.Model):
    """
    Turno de trabalho no POS.
    Controla abertura/fecho de caixa e vendas do período.
    """
    pos = models.ForeignKey(
        ConfiguracaoPOS,
        on_delete=models.PROTECT,      # turnos de caixa são registos financeiros
        related_name='turnos',
        verbose_name='POS'
    )

    operador = models.ForeignKey(
        'app.Utilizador',
        on_delete=models.PROTECT,
        related_name='turnos_operados',
        verbose_name='Operador'
    )

    valor_abertura = models.DecimalField(max_digits=10, decimal_places=2)
    valor_fecho = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    diferenca = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    aberto = models.BooleanField(default=True)
    aberto_em = models.DateTimeField(auto_now_add=True)
    fechado_em = models.DateTimeField(null=True, blank=True)

    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Turno POS'
        verbose_name_plural = 'Turnos POS'
        ordering = ['-aberto_em']
        indexes = [
            models.Index(fields=['pos', '-aberto_em']),
        ]

    def __str__(self):
        status = "Aberto" if self.aberto else "Fechado"
        return f"Turno #{self.id} - {self.operador.nome} ({status})"

    def fechar_turno(self, valor_contado):
        self.aberto = False
        self.fechado_em = timezone.now()
        self.valor_fecho = valor_contado

        vendas_dinheiro = ContaMesa.objects.filter(
            pos=self.pos,
            status='fechada',
            metodo_pagamento='dinheiro',
            fechada_em__gte=self.aberto_em,
            fechada_em__lte=self.fechado_em
        ).aggregate(
            total=models.Sum('total')
        )['total'] or Decimal('0.00')

        valor_esperado = self.valor_abertura + vendas_dinheiro
        self.diferenca = self.valor_fecho - valor_esperado

        self.save(update_fields=['aberto', 'fechado_em', 'valor_fecho', 'diferenca'])
        
        
class UtilizadorPOS(models.Model):
    """
    Membro da equipa de um POS.
    
    Sistema simples de subutilizadores:
    - Criado pelo dono do POS
    - Login com username_pos + password (sem email, sem conta Bendi)
    - Username único POR POS (pode existir "joana" em POS diferentes)
    - JWT próprio com claims pos_id e membro_id
    - Completamente separado de contas Bendi/Django
    """

    PAPEL_CHOICES = [
        ('gerente', 'Gerente'),
        ('empregado', 'Empregado'),
        ('cozinha', 'Cozinha'),
        ('caixa', 'Operador de Caixa'),
    ]

    pos = models.ForeignKey(
        'ConfiguracaoPOS',
        on_delete=models.CASCADE,
        related_name='staff',
        verbose_name='POS'
    )

    # Identidade do membro (sem email, sem User Django)
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome completo',
        help_text='Ex: João Silva'
    )

    username_pos = models.CharField(
        max_length=50,
        verbose_name='Username',
        help_text='Usado para login. Único por POS. Ex: joana, chef_mario'
    )

    password_pos = models.CharField(
        max_length=128,
        verbose_name='Password (hash)',
    )

    # Papel e permissões
    papel = models.CharField(
        max_length=20,
        choices=PAPEL_CHOICES,
        default='empregado',
        verbose_name='Papel'
    )

    pode_abrir_mesas = models.BooleanField(default=True)
    pode_fechar_contas = models.BooleanField(default=False)
    pode_cancelar_items = models.BooleanField(default=False)
    pode_dar_descontos = models.BooleanField(default=False)
    pode_gerir_produtos = models.BooleanField(default=False)
    pode_gerir_mesas = models.BooleanField(default=False)
    pode_gerir_utilizadores = models.BooleanField(default=False)
    pode_ver_relatorios = models.BooleanField(default=False)
    pode_abrir_fechar_turno = models.BooleanField(default=False)
    pode_ver_pedidos = models.BooleanField(default=True)
    pode_atualizar_status_items = models.BooleanField(default=False)

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Membro da Equipa POS'
        verbose_name_plural = 'Membros da Equipa POS'
        # Username único POR POS
        unique_together = [['pos', 'username_pos']]
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} (@{self.username_pos}) — {self.pos.nome} [{self.papel}]"

    # -------------------------------------------------------------------------
    # Password helpers
    # -------------------------------------------------------------------------

    def set_password(self, raw_password):
        """Hash e guarda a password. Retorna a password em texto para mostrar ao dono."""
        self.password_pos = make_password(raw_password)
        return raw_password

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_pos)

    # -------------------------------------------------------------------------
    # Permissões por papel (chamado ao criar)
    # -------------------------------------------------------------------------

    def aplicar_permissoes_padrao(self):
        matriz = {
            'gerente': {
                'pode_abrir_mesas': True,
                'pode_fechar_contas': True,
                'pode_cancelar_items': True,
                'pode_dar_descontos': True,
                'pode_gerir_produtos': True,
                'pode_gerir_mesas': True,
                'pode_gerir_utilizadores': False,
                'pode_ver_relatorios': True,
                'pode_abrir_fechar_turno': True,
                'pode_ver_pedidos': True,
                'pode_atualizar_status_items': True,
            },
            'empregado': {
                'pode_abrir_mesas': True,
                'pode_fechar_contas': True,
                'pode_cancelar_items': True,
                'pode_dar_descontos': False,
                'pode_gerir_produtos': False,
                'pode_gerir_mesas': True,
                'pode_gerir_utilizadores': False,
                'pode_ver_relatorios': False,
                'pode_abrir_fechar_turno': False,
                'pode_ver_pedidos': True,
                'pode_atualizar_status_items': True,
            },
            'cozinha': {
                'pode_abrir_mesas': False,
                'pode_fechar_contas': False,
                'pode_cancelar_items': False,
                'pode_dar_descontos': False,
                'pode_gerir_produtos': False,
                'pode_gerir_mesas': False,
                'pode_gerir_utilizadores': False,
                'pode_ver_relatorios': False,
                'pode_abrir_fechar_turno': False,
                'pode_ver_pedidos': True,
                'pode_atualizar_status_items': True,
            },
            'caixa': {
                'pode_abrir_mesas': True,
                'pode_fechar_contas': True,
                'pode_cancelar_items': True,
                'pode_dar_descontos': False,
                'pode_gerir_produtos': True,
                'pode_gerir_mesas': True,
                'pode_gerir_utilizadores': False,
                'pode_ver_relatorios': True,
                'pode_abrir_fechar_turno': True,
                'pode_ver_pedidos': True,
                'pode_atualizar_status_items': True,
            },
        }
        for campo, valor in matriz.get(self.papel, matriz['empregado']).items():
            setattr(self, campo, valor)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.aplicar_permissoes_padrao()
        super().save(*args, **kwargs)

    # -------------------------------------------------------------------------
    # Helper payload para respostas API
    # -------------------------------------------------------------------------

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'username_pos': self.username_pos,
            'papel': self.papel,
            'papel_display': self.get_papel_display(),
            'ativo': self.ativo,
            'permissoes': {
                'pode_abrir_mesas': self.pode_abrir_mesas,
                'pode_fechar_contas': self.pode_fechar_contas,
                'pode_cancelar_items': self.pode_cancelar_items,
                'pode_dar_descontos': self.pode_dar_descontos,
                'pode_gerir_produtos': self.pode_gerir_produtos,
                'pode_gerir_mesas': self.pode_gerir_mesas,
                'pode_gerir_utilizadores': self.pode_gerir_utilizadores,
                'pode_ver_relatorios': self.pode_ver_relatorios,
                'pode_abrir_fechar_turno': self.pode_abrir_fechar_turno,
                'pode_ver_pedidos': self.pode_ver_pedidos,
                'pode_atualizar_status_items': self.pode_atualizar_status_items,
            },
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
        }