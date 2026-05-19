"""
Modelos do Sistema POS (Point of Sale)
Suporta modo integrado (vinculado a loja) e standalone (independente)
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class ConfiguracaoPOS(models.Model):
    """
    Configuração central de cada instância POS
    Cada POS pode estar vinculado a uma loja ou ser independente
    """
    
    # Identificação única
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
    
    # Dono do POS (obrigatório)
    dono = models.ForeignKey(
        'Utilizador',
        on_delete=models.CASCADE,
        related_name='pos_geridos',
        verbose_name='Dono do POS'
    )
    
    # Conexão com loja (OPCIONAL - null = standalone)
    loja_vinculada = models.ForeignKey(
        'Loja',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_vinculados',
        verbose_name='Loja vinculada',
        help_text='Se preenchido, POS usa catálogo e stock da loja'
    )
    
    # Modo de operação
    MODO_CHOICES = [
        ('standalone', 'Standalone - Produtos próprios'),
        ('integrado', 'Integrado - Usa catálogo da loja'),
    ]
    
    modo = models.CharField(
        max_length=20,
        choices=MODO_CHOICES,
        default='standalone',
        verbose_name='Modo de operação'
    )
    
    # Configurações de taxa de serviço
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
    
    # Configurações eFatura Cabo Verde (independente da loja)
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
        help_text='Chave de API do eFatura CV (será encriptada)'
    )
    
    # Status
    ativo = models.BooleanField(
        default=True,
        verbose_name='POS ativo',
        help_text='POS inativos não aparecem na lista'
    )
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Configuração POS'
        verbose_name_plural = 'Configurações POS'
        ordering = ['-criado_em']
    
    def __str__(self):
        if self.loja_vinculada:
            return f"{self.nome} (Loja: {self.loja_vinculada.nome})"
        return f"{self.nome} (Standalone)"
    
    def save(self, *args, **kwargs):
        # Gerar código único na primeira vez
        if not self.codigo_pos:
            self.codigo_pos = f"POS-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def conectar_loja(self, loja):
        """Conecta o POS a uma loja existente"""
        self.loja_vinculada = loja
        self.modo = 'integrado'
        self.save(update_fields=['loja_vinculada', 'modo', 'atualizado_em'])
    
    def desconectar_loja(self):
        """Desconecta da loja e volta ao modo standalone"""
        self.loja_vinculada = None
        self.modo = 'standalone'
        self.save(update_fields=['loja_vinculada', 'modo', 'atualizado_em'])


class Mesa(models.Model):
    """
    Mesa física do restaurante/café
    Pertence a um POS (não diretamente a uma loja)
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
        verbose_name='Capacidade',
        help_text='Número de pessoas'
    )
    
    # Status da mesa
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
        'Utilizador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mesas_atendendo',
        verbose_name='Atendente atual'
    )
    
    aberta_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Aberta em',
        help_text='Timestamp de quando a mesa foi ocupada'
    )
    
    ativa = models.BooleanField(
        default=True,
        verbose_name='Mesa ativa',
        help_text='Mesas inativas não aparecem no POS'
    )
    
    # Metadados
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
        """Marca a mesa como ocupada"""
        self.status = 'ocupada'
        self.atendente_atual = atendente
        self.aberta_em = timezone.now()
        self.save(update_fields=['status', 'atendente_atual', 'aberta_em'])
    
    def fechar(self):
        """Libera a mesa após pagamento"""
        self.status = 'livre'
        self.atendente_atual = None
        self.aberta_em = None
        self.save(update_fields=['status', 'atendente_atual', 'aberta_em'])
    
    def marcar_limpeza(self):
        """Marca mesa para limpeza"""
        self.status = 'limpeza'
        self.save(update_fields=['status'])


class ContaMesa(models.Model):
    """
    Conta/pedido de uma mesa
    Agrupa todos os items consumidos numa sessão
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
        'Utilizador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_atendidas',
        verbose_name='Atendente'
    )
    
    # Valores financeiros (calculados automaticamente)
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Subtotal',
        help_text='Soma dos items'
    )
    
    taxa_servico_percentagem = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Taxa de serviço (%)'
    )
    
    taxa_servico_valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Taxa de serviço (€)'
    )
    
    gorjeta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Gorjeta'
    )
    
    desconto_valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Desconto aplicado'
    )
    
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total final'
    )
    
    # Status da conta
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('fechada', 'Fechada/Paga'),
        ('cancelada', 'Cancelada'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='aberta',
        verbose_name='Status'
    )
    
    # Método de pagamento
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
        blank=True,
        verbose_name='Método de pagamento'
    )
    
    # Divisão de conta
    dividida_em = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name='Dividida em',
        help_text='Número de pessoas para dividir a conta'
    )
    
    # eFatura Cabo Verde
    nif_cliente = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='NIF do cliente',
        help_text='Para emissão de fatura'
    )
    
    efatura_processada = models.BooleanField(
        default=False,
        verbose_name='Fatura emitida'
    )
    
    efatura_codigo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Código da fatura',
        help_text='Código retornado pelo eFatura CV'
    )
    
    efatura_url = models.URLField(
        blank=True,
        verbose_name='URL da fatura',
        help_text='Link para download do PDF'
    )
    
    # Observações gerais
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )
    
    # Metadados
    criada_em = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    atualizada_em = models.DateTimeField(auto_now=True, verbose_name='Atualizada em')
    fechada_em = models.DateTimeField(null=True, blank=True, verbose_name='Fechada em')
    
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
        """
        Recalcula todos os valores da conta
        Chamado automaticamente quando items são adicionados/removidos
        """
        # Subtotal = soma dos items
        self.subtotal = sum(
            item.preco_total for item in self.items.all()
        ) or Decimal('0.00')
        
        # Taxa de serviço
        if self.taxa_servico_percentagem > 0:
            self.taxa_servico_valor = (self.subtotal * self.taxa_servico_percentagem) / 100
        else:
            self.taxa_servico_valor = Decimal('0.00')
        
        # Total = subtotal + taxa + gorjeta - desconto
        self.total = (
            self.subtotal +
            self.taxa_servico_valor +
            self.gorjeta -
            self.desconto_valor
        )
        
        # Garante que total nunca é negativo
        if self.total < 0:
            self.total = Decimal('0.00')
        
        self.save(update_fields=['subtotal', 'taxa_servico_valor', 'total', 'atualizado_em'])
    
    def fechar(self, metodo_pagamento):
        """Fecha a conta após pagamento confirmado"""
        self.status = 'fechada'
        self.metodo_pagamento = metodo_pagamento
        self.fechada_em = timezone.now()
        self.save(update_fields=['status', 'metodo_pagamento', 'fechada_em'])
        
        # Libera a mesa
        self.mesa.fechar()
    
    def cancelar(self, motivo=''):
        """Cancela a conta (ex: cliente saiu sem pagar)"""
        self.status = 'cancelada'
        if motivo:
            self.observacoes += f"\n[CANCELADA] {motivo} em {timezone.now()}"
        self.save(update_fields=['status', 'observacoes'])


class ItemContaMesa(models.Model):
    """
    Item individual de uma conta
    Referencia sempre o modelo Produto (tabela unificada)
    """
    conta = models.ForeignKey(
        ContaMesa,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Conta'
    )
    
    # Referência ao produto (usa o modelo Produto do e-commerce)
    produto = models.ForeignKey(
        'Produto',
        on_delete=models.PROTECT,
        related_name='vendas_pos',
        verbose_name='Produto'
    )
    
    # Cache do nome/preço (caso produto seja editado/removido depois)
    nome = models.CharField(
        max_length=200,
        verbose_name='Nome do produto',
        help_text='Cache do nome no momento da venda'
    )
    
    quantidade = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Quantidade'
    )
    
    preco_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço unitário',
        help_text='Preço no momento da venda'
    )
    
    preco_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço total',
        help_text='Quantidade × Preço unitário'
    )
    
    # Observações do cliente (ex: "sem cebola", "bem passado")
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações do pedido'
    )
    
    # Para divisão de conta (atribuir items a pessoas)
    atribuido_pessoa = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='Atribuído à pessoa nº',
        help_text='Usado na divisão de conta (1, 2, 3...)'
    )
    
    # Status do item (para cozinha/bar)
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
        default='pendente',
        verbose_name='Status'
    )
    
    # Metadados
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
    
    def save(self, *args, **kwargs):
        # Calcular preço total automaticamente
        self.preco_total = self.quantidade * self.preco_unitario
        
        super().save(*args, **kwargs)
        
        # Recalcular totais da conta
        self.conta.calcular_totais()


class PagamentoDividido(models.Model):
    """
    Pagamento individual quando a conta é dividida
    Permite que cada pessoa pague sua parte separadamente
    """
    conta = models.ForeignKey(
        ContaMesa,
        on_delete=models.CASCADE,
        related_name='pagamentos_divididos',
        verbose_name='Conta'
    )
    
    pessoa_numero = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Pessoa nº',
        help_text='Número identificador da pessoa (1, 2, 3...)'
    )
    
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor a pagar'
    )
    
    metodo = models.CharField(
        max_length=20,
        choices=ContaMesa.METODO_PAGAMENTO_CHOICES,
        verbose_name='Método de pagamento'
    )
    
    pago = models.BooleanField(
        default=False,
        verbose_name='Pago'
    )
    
    pago_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Pago em'
    )
    
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
        """Confirma o pagamento desta parte"""
        self.pago = True
        self.pago_em = timezone.now()
        self.save(update_fields=['pago', 'pago_em'])


class TurnoPOS(models.Model):
    """
    Turno de trabalho no POS
    Controla abertura/fecho de caixa e vendas do período
    """
    pos = models.ForeignKey(
        ConfiguracaoPOS,
        on_delete=models.CASCADE,
        related_name='turnos',
        verbose_name='POS'
    )
    
    operador = models.ForeignKey(
        'Utilizador',
        on_delete=models.PROTECT,
        related_name='turnos_operados',
        verbose_name='Operador',
        help_text='Pessoa responsável pelo turno'
    )
    
    # Controlo de caixa
    valor_abertura = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor de abertura (€)',
        help_text='Dinheiro em caixa no início do turno'
    )
    
    valor_fecho = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor de fecho (€)',
        help_text='Dinheiro contado no fim do turno'
    )
    
    diferenca = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Diferença (€)',
        help_text='Diferença entre esperado e contado (+ sobra, - falta)'
    )
    
    # Status
    aberto = models.BooleanField(
        default=True,
        verbose_name='Turno aberto'
    )
    
    # Metadados
    aberto_em = models.DateTimeField(auto_now_add=True, verbose_name='Aberto em')
    fechado_em = models.DateTimeField(null=True, blank=True, verbose_name='Fechado em')
    
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações',
        help_text='Notas sobre o turno, incidentes, etc.'
    )
    
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
        """
        Fecha o turno e calcula diferença de caixa
        """
        self.aberto = False
        self.fechado_em = timezone.now()
        self.valor_fecho = valor_contado
        
        # Calcular vendas em dinheiro do turno
        vendas_dinheiro = ContaMesa.objects.filter(
            pos=self.pos,
            status='fechada',
            metodo_pagamento='dinheiro',
            fechada_em__gte=self.aberto_em,
            fechada_em__lte=self.fechado_em
        ).aggregate(
            total=models.Sum('total')
        )['total'] or Decimal('0.00')
        
        # Valor esperado = abertura + vendas
        valor_esperado = self.valor_abertura + vendas_dinheiro
        
        # Diferença = contado - esperado
        self.diferenca = self.valor_fecho - valor_esperado
        
        self.save(update_fields=['aberto', 'fechado_em', 'valor_fecho', 'diferenca'])