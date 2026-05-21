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
from decimal import Decimal
import uuid


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


class ContaMesa(models.Model):
    """
    Conta/pedido de uma mesa.
    Agrupa todos os items consumidos numa sessão.
    """
    pos = models.ForeignKey(
        ConfiguracaoPOS,
        on_delete=models.CASCADE,
        related_name='contas',
        verbose_name='POS'
    )

    mesa = models.ForeignKey(
        Mesa,
        on_delete=models.CASCADE,
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
        return f"Conta #{self.id} - {self.mesa.numero} - {self.total}€"

    def calcular_totais(self):
        self.subtotal = sum(
            item.preco_total for item in self.items.all()
        ) or Decimal('0.00')

        if self.taxa_servico_percentagem > 0:
            self.taxa_servico_valor = (self.subtotal * self.taxa_servico_percentagem) / 100
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
        return f"{self.quantidade}x {self.nome} - {self.preco_total}€"

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
        return f"Pessoa {self.pessoa_numero} - {self.valor}€ ({status})"

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
        on_delete=models.CASCADE,
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
    Relação entre utilizadores e POS (equipa).
    Define papéis e permissões granulares.
    
    Um POS pode ter múltiplos utilizadores (equipa).
    Um utilizador pode ter acesso a múltiplos POS.
    """
    
    PAPEL_CHOICES = [
        ('dono', 'Dono/Gerente'),
        ('gerente', 'Gerente'),
        ('empregado', 'Empregado'),
        ('cozinha', 'Cozinha'),
        ('caixa', 'Operador de Caixa'),
    ]
    
    pos = models.ForeignKey(
        ConfiguracaoPOS,
        on_delete=models.CASCADE,
        related_name='equipa',
        verbose_name='POS'
    )
    
    utilizador = models.ForeignKey(
        'app.Utilizador',
        on_delete=models.CASCADE,
        related_name='pos_acessos',
        verbose_name='Utilizador'
    )
    
    papel = models.CharField(
        max_length=20,
        choices=PAPEL_CHOICES,
        default='empregado',
        verbose_name='Papel'
    )
    
    # ========================================================================
    # PERMISSÕES GRANULARES
    # ========================================================================
    
    # Operações básicas de mesas
    pode_abrir_mesas = models.BooleanField(
        default=True,
        verbose_name='Pode abrir mesas',
        help_text='Permite abrir mesas e criar contas'
    )
    
    pode_fechar_contas = models.BooleanField(
        default=False,
        verbose_name='Pode fechar contas',
        help_text='Permite finalizar pagamento de contas'
    )
    
    pode_cancelar_items = models.BooleanField(
        default=False,
        verbose_name='Pode cancelar items',
        help_text='Permite remover items de contas abertas'
    )
    
    pode_dar_descontos = models.BooleanField(
        default=False,
        verbose_name='Pode dar descontos',
        help_text='Permite aplicar descontos nas contas'
    )
    
    # Gestão de produtos e mesas
    pode_gerir_produtos = models.BooleanField(
        default=False,
        verbose_name='Pode gerir produtos',
        help_text='Permite criar/editar/apagar produtos'
    )
    
    pode_gerir_mesas = models.BooleanField(
        default=False,
        verbose_name='Pode gerir mesas',
        help_text='Permite criar/editar/apagar mesas'
    )
    
    pode_gerir_utilizadores = models.BooleanField(
        default=False,
        verbose_name='Pode gerir utilizadores',
        help_text='Permite adicionar/remover membros da equipa'
    )
    
    # Relatórios e caixa
    pode_ver_relatorios = models.BooleanField(
        default=False,
        verbose_name='Pode ver relatórios',
        help_text='Permite acesso ao histórico e estatísticas'
    )
    
    pode_abrir_fechar_turno = models.BooleanField(
        default=False,
        verbose_name='Pode abrir/fechar turno',
        help_text='Permite gerir turnos e caixa'
    )
    
    # Cozinha específico
    pode_ver_pedidos = models.BooleanField(
        default=True,
        verbose_name='Pode ver pedidos',
        help_text='Permite visualizar pedidos (todos têm por padrão)'
    )
    
    pode_atualizar_status_items = models.BooleanField(
        default=False,
        verbose_name='Pode atualizar status de items',
        help_text='Permite mudar status: pendente → preparando → pronto'
    )
    
    # Meta
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Membros inativos não têm acesso ao POS'
    )
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        unique_together = ['pos', 'utilizador']
        verbose_name = 'Utilizador do POS'
        verbose_name_plural = 'Utilizadores do POS'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['pos', 'ativo']),
            models.Index(fields=['utilizador', 'ativo']),
        ]
    
    def __str__(self):
        return f"{self.utilizador.nome} - {self.pos.nome} ({self.get_papel_display()})"
    
    def save(self, *args, **kwargs):
        """Define permissões padrão baseadas no papel ao criar"""
        if not self.pk:  # Novo objeto
            self._set_permissoes_padrao()
        super().save(*args, **kwargs)
    
    def _set_permissoes_padrao(self):
        """
        Define permissões padrão para cada papel.
        Chamado automaticamente ao criar novo UtilizadorPOS.
        """
        permissoes = {
            'dono': {
                # Dono tem TODAS as permissões
                'pode_abrir_mesas': True,
                'pode_fechar_contas': True,
                'pode_cancelar_items': True,
                'pode_dar_descontos': True,
                'pode_gerir_produtos': True,
                'pode_gerir_mesas': True,
                'pode_gerir_utilizadores': True,
                'pode_ver_relatorios': True,
                'pode_abrir_fechar_turno': True,
                'pode_ver_pedidos': True,
                'pode_atualizar_status_items': True,
            },
            'gerente': {
                # Gerente tem quase todas (exceto gerir utilizadores)
                'pode_abrir_mesas': True,
                'pode_fechar_contas': True,
                'pode_cancelar_items': True,
                'pode_dar_descontos': True,
                'pode_gerir_produtos': True,
                'pode_gerir_mesas': True,
                'pode_gerir_utilizadores': False,  # ← Não pode gerir equipa
                'pode_ver_relatorios': True,
                'pode_abrir_fechar_turno': True,
                'pode_ver_pedidos': True,
                'pode_atualizar_status_items': True,
            },
            'empregado': {
                # Empregado opera mesas apenas
                'pode_abrir_mesas': True,
                'pode_fechar_contas': False,
                'pode_cancelar_items': False,
                'pode_dar_descontos': False,
                'pode_gerir_produtos': False,
                'pode_gerir_mesas': False,
                'pode_gerir_utilizadores': False,
                'pode_ver_relatorios': False,
                'pode_abrir_fechar_turno': False,
                'pode_ver_pedidos': True,
                'pode_atualizar_status_items': False,
            },
            'cozinha': {
                # Cozinha vê e atualiza pedidos apenas
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
                'pode_atualizar_status_items': True,  # ← Pode atualizar status
            },
            'caixa': {
                # Caixa fecha contas e gere turno
                'pode_abrir_mesas': False,
                'pode_fechar_contas': True,
                'pode_cancelar_items': False,
                'pode_dar_descontos': False,
                'pode_gerir_produtos': False,
                'pode_gerir_mesas': False,
                'pode_gerir_utilizadores': False,
                'pode_ver_relatorios': True,
                'pode_abrir_fechar_turno': True,
                'pode_ver_pedidos': True,
                'pode_atualizar_status_items': False,
            },
        }
        
        papel_permissoes = permissoes.get(self.papel, permissoes['empregado'])
        
        for campo, valor in papel_permissoes.items():
            setattr(self, campo, valor)