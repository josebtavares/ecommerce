from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils.timezone import now


# ══════════════════════════════════════════════════════════════
# UTILIZADOR
# ══════════════════════════════════════════════════════════════

class Utilizador(models.Model):
    """
    Extensão do User do Django.
    Um utilizador pode comprar, abrir loja, ser staff ou condutor.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='utilizador')
 
    telefone        = models.CharField(max_length=30, blank=True, default='')
    morada          = models.CharField(max_length=300, blank=True, default='')
    foto            = models.ImageField(
                        upload_to='utilizadores/%Y/%m/',
                        null=True, blank=True,
                        default='utilizadores/default.png'
                      )
    verificado      = models.BooleanField(default=False)
    rating          = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    data_criacao    = models.DateTimeField(auto_now_add=True)
    data_atualizacao= models.DateTimeField(auto_now=True)
    status          = models.CharField(max_length=20, default='ativo')
    google_id       = models.CharField(max_length=100, blank=True, null=True, unique=True)
 
    # ── Role no painel de administração ──────────────────────
    # Só activo se user.is_staff=True
    ROLES_ADMIN = [
        ('superadmin',   'Super Admin'),
        ('moderador',    'Moderador'),
        ('suporte',      'Suporte'),
        ('contabilista', 'Contabilista'),
    ]
 
    PERMISSOES_ADMIN = {
        'superadmin': [
            'ver_stats',
            'gerir_lojas',
            'gerir_utilizadores',
            'gerir_produtos',
            'gerir_encomendas',
            'gerir_pagamentos',
            'gerir_tipos_globais',
        ],
        'moderador': [
            'ver_stats',
            'gerir_lojas',
            'gerir_produtos',
        ],
        'suporte': [
            'ver_stats',
            'gerir_utilizadores',
            'gerir_lojas',
            'gerir_encomendas',
        ],
        'contabilista': [
            'ver_stats',
            'gerir_pagamentos',
            'gerir_encomendas',
        ],
    }
 
    role_admin = models.CharField(
        max_length=20,
        choices=ROLES_ADMIN,
        null=True, blank=True,
        default=None,
    )
 
    # ── propriedades de conveniência ──────────────────────────
    @property
    def nome(self):
        return self.user.get_full_name() or self.user.username
 
    @property
    def email(self):
        return self.user.email
 
    @property
    def username(self):
        return self.user.username
 
    @property
    def is_active(self):
        return self.status == 'ativo'
 
    def pode_admin(self, permissao: str) -> bool:
        """Verifica se este utilizador tem permissão no painel de admin."""
        if not self.user.is_staff:
            return False
        if not self.role_admin:
            return False
        return permissao in self.PERMISSOES_ADMIN.get(self.role_admin, [])
 
    def __str__(self):
        return self.user.username


# ══════════════════════════════════════════════════════════════
# GALERIA  (mantida — útil para lojas e produtos)
# ══════════════════════════════════════════════════════════════

def galeria_upload(instance, filename):
    return f'galeria/{now():%Y/%m}/{filename}'

def produto_upload(instance, filename):
    return f'produtos/{now():%Y/%m}/{filename}'

def produto_imagem_upload(instance, filename):
    return f'produtos/{instance.produto.loja_id}/{instance.produto_id}/{filename}'


class Galeria(models.Model):
    titulo      = models.CharField(max_length=200, blank=True, null=True)
    descricao   = models.TextField(blank=True, null=True)
    ficheiro    = models.FileField(
                    upload_to=galeria_upload,
                    validators=[FileExtensionValidator(
                        ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'mov', 'mkv']
                    )],
                    blank=True, null=True
                  )
    utilizador  = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='galeria')
    data        = models.DateTimeField(default=now)
    status      = models.CharField(max_length=20, default='ativo')
    likes       = models.PositiveIntegerField(default=0)
    comentarios = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.titulo or f'Galeria #{self.pk}'


# ══════════════════════════════════════════════════════════════
# TEMPLATES DE LOJA
# ══════════════════════════════════════════════════════════════

class LojaTemplate(models.Model):
    nome                    = models.CharField(max_length=100)
    tipo_layout             = models.CharField(max_length=50)   # ex: 'grid', 'list', 'magazine'
    imagem_preview          = models.ImageField(upload_to='templates/', null=True, blank=True)
    suporta_banner          = models.BooleanField(default=True)
    suporta_produtos_destaque = models.BooleanField(default=True)
    suporta_sidebar         = models.BooleanField(default=False)
    ativo                   = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


# ══════════════════════════════════════════════════════════════
# LOJA
# ══════════════════════════════════════════════════════════════

class Loja(models.Model):
    dono            = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='lojas')
    

    nome            = models.CharField(max_length=200)
    descricao       = models.TextField(blank=True, default='')
    categoria       = models.CharField(max_length=100)          # ex: 'comida', 'roupa', 'eletronicos'
    localizacao     = models.CharField(max_length=300, blank=True, default='')
    percentagem_iva = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    percentagem_comissao = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, validators=[MinValueValidator(0), MaxValueValidator(100)],help_text='Percentagem de comissao cobrada pela plataforma')

    # Opções de entrega/levantamento
    entrega_ativa   = models.BooleanField(default=False)
    levantamento_ativo = models.BooleanField(default=False)

    # Branding
    logo            = models.ImageField(upload_to='lojas/logos/%Y/%m/', null=True, blank=True)
    banner          = models.ImageField(upload_to='lojas/banners/%Y/%m/', null=True, blank=True)
   
    layout_produtos = models.CharField(max_length=10, default='grid',
                                       choices=[('grid', 'Grelha'), ('list', 'Lista')])

    ativa           = models.BooleanField(default=True)
    data_criacao    = models.DateTimeField(auto_now_add=True)
    data_atualizacao= models.DateTimeField(auto_now=True)
    
    politica_devolucao   = models.TextField(blank=True, default='')
    termos_servico       = models.TextField(blank=True, default='')
    politica_privacidade = models.TextField(blank=True, default='')
    
    template_id    = models.CharField(max_length=50, default='classico', blank=True)
    cor_primaria   = models.CharField(max_length=7,  default='#dc2626',  blank=True)
    cor_secundaria = models.CharField(max_length=7,  default='#1c1c1e',  blank=True)
    dark_mode      = models.BooleanField(default=True)
 
    flutterwave_subaccount_id = models.CharField(
            max_length=200, blank=True, default='',
            help_text='Subaccount ID do Flutterwave desta loja (ex: RS_XXXX)'
        )
    aceita_flutterwave = models.BooleanField(
        default=False,
        help_text='A loja tem Flutterwave configurado e activo'
    )

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return self.nome


# ══════════════════════════════════════════════════════════════
# STAFF DA LOJA
# ══════════════════════════════════════════════════════════════

class UtilizadorLoja(models.Model):
    ROLES = [
        ('dono',        'Dono'),
        ('gestor',      'Gestor'),
        ('staff',       'Staff'),
        ('contabilista','Contabilista'),
        ('condutor',    'Condutor'),
    ]

    # ── Mapa de permissões por role ───────────────────────────
    # Cada permissão é uma string. Basta verificar:
    #   membro.pode('editar_loja')
    PERMISSOES = {
        'dono': [
            'ver_loja',
            'editar_loja',
            'apagar_loja',
            'gerir_staff',
            'gerir_produtos',
            'gerir_inventario',
            'gerir_encomendas',
            'atribuir_condutor',
            'gerir_pagamentos',
            'gerir_entregas',
            'ver_relatorios',
            'gerir_metodos_pagamento',
            'gerir_opcoes_entrega',
            'gerir_template',
        ],
        'gestor': [
            'ver_loja',
            'editar_loja',
            'gerir_staff',
            'gerir_produtos',
            'gerir_inventario',
            'gerir_encomendas',
            'atribuir_condutor',
            'gerir_pagamentos',
            'gerir_entregas',
            'ver_relatorios',
            'gerir_metodos_pagamento',
            'gerir_opcoes_entrega',
            'gerir_template',
        ],
        'staff': [
            'ver_loja',
            'gerir_produtos',
            'gerir_inventario',
            'gerir_encomendas',
        ],
        'contabilista': [
            'ver_loja',
            'gerir_pagamentos',
            'ver_relatorios',
        ],
        'condutor': [
            'ver_loja',
            'gerir_entregas',
        ],
    }

    loja        = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='staff')
    utilizador  = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='lojas_staff')
    role        = models.CharField(max_length=20, choices=ROLES, default='staff')
    ativo       = models.BooleanField(default=True)
    data_entrada= models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('loja', 'utilizador')

    def __str__(self):
        return f'{self.utilizador} — {self.role} @ {self.loja}'

    def pode(self, permissao: str) -> bool:
        """Verifica se este membro tem uma permissão específica."""
        if not self.ativo:
            return False
        return permissao in self.PERMISSOES.get(self.role, [])

    @classmethod
    def obter_membro(cls, loja, utilizador):
        """
        Devolve o UtilizadorLoja activo ou None.
        Uso: membro = UtilizadorLoja.obter_membro(loja, request.user.utilizador)
        """
        return cls.objects.filter(loja=loja, utilizador=utilizador, ativo=True).first()

    @classmethod
    def verificar_permissao(cls, loja, utilizador, permissao: str) -> bool:
        """
        Atalho directo para views.
        Uso: UtilizadorLoja.verificar_permissao(loja, request.user.utilizador, 'editar_loja')
        """
        membro = cls.obter_membro(loja, utilizador)
        if not membro:
            return False
        return membro.pode(permissao)


# ══════════════════════════════════════════════════════════════
# TIPO DE PRODUTO
# ══════════════════════════════════════════════════════════════

class TipoProduto(models.Model):
    """
    Define um tipo de produto e os atributos esperados para esse tipo.
    loja=None → tipo global da plataforma (visível a todas as lojas)
    loja=X    → tipo privado da loja X
 
    Formato do atributos_schema (novo):
    [
        {"nome": "tamanho", "tipo": "choices", "opcoes": ["XS","S","M","L","XL"], "obrigatorio": true},
        {"nome": "cor",     "tipo": "choices", "opcoes": ["preto","branco"],       "obrigatorio": false},
        {"nome": "material","tipo": "texto",   "opcoes": [],                       "obrigatorio": false},
    ]
    """
    loja             = models.ForeignKey(
                         'Loja',
                         on_delete=models.CASCADE,
                         related_name='tipos_produto',
                         null=True, blank=True,
                       )
    nome             = models.CharField(max_length=100)   # removido unique=True
    descricao        = models.CharField(max_length=255, blank=True, default='')
    atributos_schema = models.JSONField(default=list)
    ativo            = models.BooleanField(default=True)
 
    class Meta:
        # nome único por loja (null loja = global)
        unique_together = [('loja', 'nome')]
 
    def __str__(self):
        if self.loja:
            return f'{self.nome} ({self.loja.nome})'
        return f'{self.nome} [global]'
 
    def validar_atributos(self, atributos: dict) -> list:
        """
        Verifica atributos obrigatórios em falta.
        Compatível com schema antigo (lista de strings) e novo (lista de dicts).
        """
        em_falta = []
        for campo in self.atributos_schema:
            if isinstance(campo, str):
                # formato antigo
                if campo not in atributos:
                    em_falta.append(campo)
            elif isinstance(campo, dict) and campo.get('obrigatorio'):
                if campo.get('nome') not in atributos:
                    em_falta.append(campo['nome'])
        return em_falta

# ══════════════════════════════════════════════════════════════
# PRODUTO
# ══════════════════════════════════════════════════════════════

class Produto(models.Model):
    loja        = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='produtos')
    tipo        = models.ForeignKey(TipoProduto, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='produtos')
    nome        = models.CharField(max_length=200)
    descricao   = models.TextField(blank=True, default='')
    categorias = models.ManyToManyField(
       'CategoriaLoja',
       blank=True,
       related_name='produtos',
         help_text='Categorias associadas a este produto (ex: "calçado", "roupa", "comida").'
       
    )
    preco       = models.DecimalField(max_digits=10, decimal_places=2,
                                      validators=[MinValueValidator(0)])
    sku         = models.CharField(max_length=100, blank=True, default='')
    ficheiro    = models.FileField(
                    upload_to=produto_upload,
                    validators=[FileExtensionValidator(
                        ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'mov', 'mkv']
                    )],
                    blank=True, null=True
                  )
    # Atributos dinâmicos de acordo com o TipoProduto
    # Exemplos:
    #   calcado:  {"tamanho": "42", "cor": "preto", "material": "couro"}
    #   roupa:    {"tamanho": "L", "cor": "azul", "genero": "masculino"}
    #   comida:   {"ingredientes": "carne, alface", "calorias": "550", "alergenos": "glúten"}
    #   bebida:   {"volume": "500ml", "alcool": "0%", "temperatura": "fria"}
    atributos   = models.JSONField(default=dict, blank=True)

    destaque    = models.BooleanField(default=False)
    ativo       = models.BooleanField(default=True)
    data_criacao= models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return f'{self.nome} ({self.loja.nome})'

    def atributos_em_falta(self) -> list:
        """
        Atalho para verificar se o produto tem todos os atributos
        esperados para o seu tipo.
        """
        if not self.tipo:
            return []
        return self.tipo.validar_atributos(self.atributos)
    

class ProdutoImagem(models.Model):
    """
    Imagens adicionais de um produto.
    A imagem principal continua em Produto.ficheiro (retrocompatibilidade).
    """
    produto  = models.ForeignKey(
        'Produto', on_delete=models.CASCADE, related_name='imagens'
    )
    ficheiro = models.ImageField(upload_to=produto_imagem_upload)
    ordem    = models.PositiveSmallIntegerField(default=0)  # para ordenar no slider
    legenda  = models.CharField(max_length=120, blank=True)
 
    class Meta:
        ordering = ['ordem', 'id']
 
    def __str__(self):
        return f'Imagem {self.id} do produto {self.produto_id}'
 
    @property
    def ficheiro_url(self):
        if self.ficheiro:
            return self.ficheiro.url
        return None


# ══════════════════════════════════════════════════════════════
# INVENTÁRIO
# ══════════════════════════════════════════════════════════════

class Inventario(models.Model):
    loja            = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='inventario')
    produto         = models.OneToOneField(Produto, on_delete=models.CASCADE, related_name='inventario')
    quantidade      = models.PositiveIntegerField(default=0)
    preco_custo     = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                          validators=[MinValueValidator(0)])
    preco_venda     = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                          validators=[MinValueValidator(0)])
    data_atualizacao= models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Inventário: {self.produto.nome} — {self.quantidade} un.'


# ══════════════════════════════════════════════════════════════
# CARRINHO
# ══════════════════════════════════════════════════════════════

class Carrinho(models.Model):
    utilizador  = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='carrinhos')
    loja        = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='carrinhos')
    data_criacao= models.DateTimeField(auto_now_add=True)

    class Meta:
        # Um utilizador só tem um carrinho activo por loja
        unique_together = ('utilizador', 'loja')

    def __str__(self):
        return f'Carrinho de {self.utilizador} @ {self.loja}'


class ItemCarrinho(models.Model):
    carrinho    = models.ForeignKey(Carrinho, on_delete=models.CASCADE, related_name='itens')
    produto     = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade  = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    atributos   = models.JSONField(default=dict, blank=True)

    

    def __str__(self):
        return f'{self.quantidade}x {self.produto.nome}'


# ══════════════════════════════════════════════════════════════
# ENCOMENDA
# ══════════════════════════════════════════════════════════════

class Encomenda(models.Model):
    TIPO_ENTREGA = [
        ('entrega',      'Entrega ao domicílio'),
        ('levantamento', 'Levantamento em loja'),
    ]
    STATUS = [
        ('pendente',    'Pendente'),
        ('pago',        'Pago'),
        ('preparando',  'Em preparação'),
        ('enviado',     'Enviado'),
        ('concluido',   'Concluído'),
        ('cancelado',   'Cancelado'),
    ]

    comprador       = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='encomendas')
    loja            = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='encomendas')
    valor_total     = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tipo_entrega    = models.CharField(max_length=15, choices=TIPO_ENTREGA, default='levantamento')
    status          = models.CharField(max_length=15, choices=STATUS, default='pendente')
    morada_entrega  = models.CharField(max_length=300, blank=True, default='')
    notas           = models.TextField(blank=True, default='')
    data_criacao    = models.DateTimeField(auto_now_add=True)
    data_atualizacao= models.DateTimeField(auto_now=True)
    opcao_entrega   = models.ForeignKey(
        'OpcaoEntrega',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='encomendas',
    )

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return f'Encomenda #{self.pk} — {self.comprador} @ {self.loja}'


class ItemEncomenda(models.Model):
    encomenda   = models.ForeignKey(Encomenda, on_delete=models.CASCADE, related_name='itens')
    produto     = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True)
    quantidade  = models.PositiveIntegerField(default=1)
    preco       = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot do preço
    atributos   = models.JSONField(default=dict, blank=True)  # ← novo


    def __str__(self):
        return f'{self.quantidade}x {self.produto} (enc. #{self.encomenda_id})'


# ══════════════════════════════════════════════════════════════
# ENTREGA & CONDUTOR  (opcionais por loja)
# ══════════════════════════════════════════════════════════════

class OpcaoEntrega(models.Model):
    loja            = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='opcoes_entrega')
    nome            = models.CharField(max_length=100)          # ex: 'Standard', 'Expresso'
    preco           = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    tempo_estimado  = models.CharField(max_length=100, blank=True, default='')  # ex: '30–45 min'
    area_cobertura  = models.CharField(max_length=300, blank=True, default='')
    ativa           = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.nome} ({self.loja.nome})'


class Condutor(models.Model):
    loja            = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='condutores')
    utilizador      = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='condutor_em')
    tipo_veiculo    = models.CharField(max_length=100, blank=True, default='')
    ativo           = models.BooleanField(default=True)

    class Meta:
        unique_together = ('loja', 'utilizador')

    def __str__(self):
        return f'Condutor {self.utilizador} @ {self.loja}'


class Entrega(models.Model):
    STATUS = [
        ('atribuido',   'Atribuído'),
        ('a_caminho',   'A caminho'),
        ('entregue',    'Entregue'),
        ('falhou',      'Falhou'),
    ]

    encomenda       = models.OneToOneField(Encomenda, on_delete=models.CASCADE, related_name='entrega')
    condutor        = models.ForeignKey(Condutor, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='entregas')
    opcao_entrega   = models.ForeignKey(OpcaoEntrega, on_delete=models.SET_NULL,
                                         null=True, blank=True)
    status          = models.CharField(max_length=15, choices=STATUS, default='atribuido')
    data_criacao    = models.DateTimeField(auto_now_add=True)
    data_entrega    = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Entrega da encomenda #{self.encomenda_id}'


# ══════════════════════════════════════════════════════════════
# PAGAMENTO
# ══════════════════════════════════════════════════════════════

class MetodoPagamento(models.Model):
    TIPOS = [
        ('cartao',  'Cartão'),
        ('dinheiro','Dinheiro'),
        ('mbway',   'MBWay'),
        ('paypal',  'PayPal'),
        ('stripe',  'Stripe'),
        ('flutterwave',   'Flutterwave'),
        ('transferencia', 'Transferência Bancária'),
    ]

    loja    = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='metodos_pagamento')
    tipo    = models.CharField(max_length=20, choices=TIPOS)
    ativo   = models.BooleanField(default=True)

    class Meta:
        unique_together = ('loja', 'tipo')

    def __str__(self):
        return f'{self.tipo} ({self.loja.nome})'


class Pagamento(models.Model):
    STATUS = [
        ('pendente',  'Pendente'),
        ('aprovado',  'Aprovado'),
        ('falhado',   'Falhado'),
        ('reembolsado','Reembolsado'),
    ]

    encomenda           = models.OneToOneField(Encomenda, on_delete=models.CASCADE, related_name='pagamento')
    metodo              = models.ForeignKey(MetodoPagamento, on_delete=models.SET_NULL,
                                            null=True, blank=True)
    valor               = models.DecimalField(max_digits=10, decimal_places=2)
    status              = models.CharField(max_length=15, choices=STATUS, default='pendente')
    referencia_transacao= models.CharField(max_length=255, blank=True, default='')
    data_criacao        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pagamento #{self.pk} — {self.status}'


# ══════════════════════════════════════════════════════════════
# AVALIAÇÕES
# ══════════════════════════════════════════════════════════════

class AvaliacaoLoja(models.Model):
    utilizador  = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='avaliacoes')
    loja        = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='avaliacoes')
    encomenda   = models.ForeignKey(Encomenda, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='avaliacao')
    pontuacao   = models.PositiveSmallIntegerField(
                    validators=[MinValueValidator(1), MaxValueValidator(5)]
                  )
    comentario  = models.TextField(blank=True, default='')
    data_criacao= models.DateTimeField(auto_now_add=True)
    oculta = models.BooleanField(default=False)

    class Meta:
        unique_together = ('utilizador', 'loja', 'encomenda')

    def __str__(self):
        return f'{self.pontuacao}★ — {self.utilizador} → {self.loja}'


# ══════════════════════════════════════════════════════════════
# CARTÃO GUARDADO  (token Stripe — nunca dados reais)
# ══════════════════════════════════════════════════════════════

class CartaoGuardado(models.Model):
    """
    Guarda apenas tokens do Stripe — nunca números de cartão reais.
    O utilizador vê "Visa **** 4242" mas os dados ficam nos servidores Stripe.
    """
    MARCAS = [
        ('visa',       'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex',       'American Express'),
        ('other',      'Outro'),
    ]

    utilizador         = models.ForeignKey(
                           Utilizador, on_delete=models.CASCADE,
                           related_name='cartoes'
                         )
    # tokens Stripe — não são dados sensíveis
    stripe_customer_id = models.CharField(max_length=255)  # cus_xxx
    stripe_payment_id  = models.CharField(max_length=255)  # pm_xxx

    # dados de display (vêm do Stripe, não são sensíveis)
    marca              = models.CharField(max_length=20, choices=MARCAS, default='other')
    ultimos_4          = models.CharField(max_length=4)
    mes_expiracao      = models.PositiveSmallIntegerField()
    ano_expiracao      = models.PositiveSmallIntegerField()

    predefinido        = models.BooleanField(default=False)
    data_criacao       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-predefinido', '-data_criacao']

    def __str__(self):
        return f'{self.marca.upper()} **** {self.ultimos_4} ({self.utilizador})'

    def save(self, *args, **kwargs):
        # garante que só existe um cartão predefinido por utilizador
        if self.predefinido:
            CartaoGuardado.objects.filter(
                utilizador=self.utilizador, predefinido=True
            ).exclude(pk=self.pk).update(predefinido=False)
        super().save(*args, **kwargs)


# ══════════════════════════════════════════════════════════════
# CHAT  (mantido, será activado numa fase posterior)
# ══════════════════════════════════════════════════════════════

class ChatThread(models.Model):
    PRIVATE = 'private'
    GROUP   = 'group'
    TYPES   = [(PRIVATE, 'Private'), (GROUP, 'Group')]

    thread_type = models.CharField(max_length=7, choices=TYPES, default=PRIVATE)
    title       = models.CharField(max_length=120, blank=True)
    created_at  = models.DateTimeField(default=now)
    last_msg_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ['-last_msg_at']

    def __str__(self):
        return f'Chat #{self.pk}' if self.thread_type == self.PRIVATE else (self.title or f'Grupo #{self.pk}')


class ChatParticipant(models.Model):
    thread      = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='participants')
    user        = models.ForeignKey(Utilizador, on_delete=models.CASCADE)
    joined_at   = models.DateTimeField(default=now)
    last_read   = models.DateTimeField(default=now)

    class Meta:
        unique_together = ('thread', 'user')

    def __str__(self):
        return f'{self.user} em {self.thread}'


def chat_upload(instance, filename):
    return f'chat/{now():%Y/%m}/{filename}'


class ChatMessage(models.Model):
    thread      = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    sender      = models.ForeignKey(Utilizador, on_delete=models.CASCADE)
    text        = models.TextField(blank=True)
    attachment  = models.FileField(upload_to=chat_upload, blank=True, null=True)
    created_at  = models.DateTimeField(default=now)
    edited_at   = models.DateTimeField(blank=True, null=True)
    deleted     = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        
class Comissao(models.Model):
    STATUS = [
        ('pendente',   'Pendente'),    # registada, aguarda liquidacao
        ('liquidada',  'Liquidada'),   # paga ao administrador
    ]
 
    encomenda        = models.OneToOneField(
                           Encomenda, on_delete=models.CASCADE,
                           related_name='comissao'
                       )
    loja             = models.ForeignKey(
                           Loja, on_delete=models.CASCADE,
                           related_name='comissoes'
                       )
    valor_encomenda  = models.DecimalField(max_digits=10, decimal_places=2)
    percentagem      = models.DecimalField(max_digits=5, decimal_places=2)
    valor_comissao   = models.DecimalField(max_digits=10, decimal_places=2)
    status           = models.CharField(max_length=15, choices=STATUS, default='pendente')
    data_criacao     = models.DateTimeField(auto_now_add=True)
    data_liquidacao  = models.DateTimeField(null=True, blank=True)
    notas            = models.TextField(blank=True, default='')
 
    class Meta:
        ordering = ['-data_criacao']
 
    def __str__(self):
        return f'Comissao #{self.pk} — {self.loja.nome} — {self.valor_comissao}€ ({self.status})'
 
    @classmethod
    def registar(cls, encomenda):
        """
        Cria o registo de comissao para uma encomenda.
        Chama isto apos pagamento confirmado (cartao/mbway)
        ou quando encomenda.status = concluido (dinheiro).
        Evita duplicados com get_or_create.
        """
        loja = encomenda.loja
        percentagem   = loja.percentagem_comissao
        valor_comissao = (encomenda.valor_total * percentagem / 100).quantize(
            __import__('decimal').Decimal('0.01')
        )
        comissao, criada = cls.objects.get_or_create(
            encomenda=encomenda,
            defaults={
                'loja':           loja,
                'valor_encomenda': encomenda.valor_total,
                'percentagem':    percentagem,
                'valor_comissao': valor_comissao,
                'status':         'pendente',
            }
        )
        return comissao, criada
    
    
class Categoria(models.Model):
    """
    Categorias de loja geridas pelo admin.
    A Loja guarda só o nome (CharField) — sem FK.
    """
    nome  = models.CharField(max_length=100, unique=True)
    icon  = models.CharField(max_length=10, default='🏪')
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)
 
    class Meta:
        ordering = ['ordem', 'nome']
 
    def __str__(self):
        return f'{self.icon} {self.nome}'


# ══════════════════════════════════════════════════════════════
# PERMISSION CLASSES (DRF) — reutilizáveis nas views
# ══════════════════════════════════════════════════════════════

from rest_framework.permissions import BasePermission


def _get_loja(view, obj=None):
    """Helper: tenta obter a Loja do objecto ou dos kwargs da view."""
    if obj and isinstance(obj, Loja):
        return obj
    if obj and hasattr(obj, 'loja'):
        return obj.loja
    loja_id = view.kwargs.get('loja_pk') or view.kwargs.get('loja_id')
    if loja_id:
        return Loja.objects.filter(pk=loja_id).first()
    return None


class PermissaoLoja(BasePermission):
    """
    Permission class base para o backoffice da loja.
    Subclasses definem `permissao_necessaria`.

    Uso numa view:
        class EditarLojaView(UpdateAPIView):
            permission_classes = [IsAuthenticated, PodeEditarLoja]
    """
    permissao_necessaria = ''

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True   # detalhe verifica o objecto

    def has_object_permission(self, request, view, obj):
        try:
            utilizador = request.user.utilizador
        except Exception:
            return False
        loja = _get_loja(view, obj)
        if not loja:
            return False
        return UtilizadorLoja.verificar_permissao(loja, utilizador, self.permissao_necessaria)
    
    
# ══════════════════════════════════════════════════════════════
# NOTIFICAÇÕES
# ══════════════════════════════════════════════════════════════
 
class Notificacao(models.Model):
    TIPOS = [
        # Admin do site
        ('loja_pendente',            'Loja pendente de aprovação'),
        ('comissao_recebida',        'Comissão recebida'),
        # Dono/gestor da loja
        ('loja_aprovada',            'Loja aprovada'),
        ('loja_rejeitada',           'Loja rejeitada'),
        ('nova_encomenda',           'Nova encomenda'),
        ('pagamento_aprovado',       'Pagamento aprovado'),
        ('encomenda_concluida_loja', 'Encomenda concluída na loja'),
        ('encomenda_cancelada_loja', 'Encomenda cancelada na loja'),
        ('stock_baixo',              'Stock baixo'),
        ('novo_staff',               'Novo membro de staff'),
        ('avaliacao_recebida',       'Nova avaliação recebida'),
        # Condutor
        ('entrega_atribuida',        'Entrega atribuída'),
        ('entrega_cancelada',        'Entrega cancelada'),
        # Comprador
        ('encomenda_paga',           'Encomenda paga'),
        ('encomenda_enviada',        'Encomenda enviada'),
        ('encomenda_concluida',      'Encomenda concluída'),
        ('encomenda_cancelada',      'Encomenda cancelada'),
        # Staff
        ('encomenda_atualizada',     'Encomenda actualizada'),
    ]
 
    utilizador   = models.ForeignKey(
                       Utilizador, on_delete=models.CASCADE,
                       related_name='notificacoes'
                   )
    tipo         = models.CharField(max_length=30, choices=TIPOS)
    titulo       = models.CharField(max_length=200)
    mensagem     = models.TextField(blank=True, default='')
    loja         = models.ForeignKey(
                       'Loja', on_delete=models.CASCADE,
                       null=True, blank=True,
                       related_name='notificacoes'
                   )
    link         = models.CharField(max_length=300, blank=True, default='')
    lida         = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-data_criacao']
 
    def __str__(self):
        return f'{self.tipo} → {self.utilizador} ({self.lida})'
 
    @classmethod
    def criar(cls, utilizador, tipo, titulo, mensagem='', loja=None, link=''):
        return cls.objects.create(
            utilizador=utilizador,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            loja=loja,
            link=link,
        )
 
    @classmethod
    def criar_para_staff(cls, loja, roles, tipo, titulo, mensagem='', link='', excluir=None):
        """
        Cria notificação para todos os membros activos da loja com os roles indicados.
        roles: lista de strings, ex: ['dono', 'gestor', 'staff']
        excluir: Utilizador a excluir (ex: o próprio que fez a acção)
        """
        from .models import UtilizadorLoja
        membros = UtilizadorLoja.objects.filter(
            loja=loja, role__in=roles, ativo=True
        ).select_related('utilizador')
 
        notificacoes = []
        for membro in membros:
            if excluir and membro.utilizador == excluir:
                continue
            notificacoes.append(cls(
                utilizador=membro.utilizador,
                tipo=tipo,
                titulo=titulo,
                mensagem=mensagem,
                loja=loja,
                link=link,
            ))
        if notificacoes:
            cls.objects.bulk_create(notificacoes)

class CategoriaLoja(models.Model):
    """
    Categoria de produtos criada pelo dono da loja.
    Um produto pode pertencer a várias categorias (M2M).
    """
    loja   = models.ForeignKey('Loja', on_delete=models.CASCADE, related_name='categorias')
    nome   = models.CharField(max_length=100)
    icone  = models.CharField(max_length=10, default='📂', blank=True)
    ativo  = models.BooleanField(default=True)   # aparece na página da loja
    ordem  = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['ordem', 'nome']
        unique_together = [('loja', 'nome')]      # nome único por loja
    
    def __str__(self):
        return f'{self.loja.nome} / {self.nome}'
    
    def save(self, *args, **kwargs):
        self.nome = self.nome.lower().strip()
        super().save(*args, **kwargs)
        
class CategoriaDestaque(models.Model):
    """
    Categorias de lojas promovidas pelo admin para aparecer no home.
    Referencia directamente uma CategoriaLoja.
    """
    categoria = models.ForeignKey(
    'CategoriaLoja',
    on_delete=models.CASCADE,
    related_name='destaques',
    null=True,      # ← temporário para a migração passar
    blank=True,
)
    icone  = models.CharField(max_length=10, default='', blank=True)
    ordem  = models.IntegerField(default=0)
    ativo  = models.BooleanField(default=True)
 
    class Meta:
        ordering = ['ordem']
 
    def __str__(self):
        return f'Destaque: {self.categoria.nome} ({self.categoria.loja.nome})'
 
    @property
    def nome(self):
        return self.categoria.nome
 
    @property  
    def icone_display(self):
        return self.icone or self.categoria.icone or '📂'



# ── Permissões concretas ──────────────────────────────────────

class PodeVerLoja(PermissaoLoja):
    permissao_necessaria = 'ver_loja'

class PodeEditarLoja(PermissaoLoja):
    permissao_necessaria = 'editar_loja'

class PodeApagarLoja(PermissaoLoja):
    permissao_necessaria = 'apagar_loja'

class PodeGerirStaff(PermissaoLoja):
    permissao_necessaria = 'gerir_staff'

class PodeGerirProdutos(PermissaoLoja):
    permissao_necessaria = 'gerir_produtos'

class PodeGerirInventario(PermissaoLoja):
    permissao_necessaria = 'gerir_inventario'

class PodeGerirEncomendas(PermissaoLoja):
    permissao_necessaria = 'gerir_encomendas'

class PodeAtribuirCondutor(PermissaoLoja):
    permissao_necessaria = 'atribuir_condutor'

class PodeGerirPagamentos(PermissaoLoja):
    permissao_necessaria = 'gerir_pagamentos'

class PodeGerirEntregas(PermissaoLoja):
    permissao_necessaria = 'gerir_entregas'

class PodeVerRelatorios(PermissaoLoja):
    permissao_necessaria = 'ver_relatorios'

class PodeGerirTemplate(PermissaoLoja):
    permissao_necessaria = 'gerir_template'