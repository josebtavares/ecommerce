from django.db import models, transaction
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
            'gerir_conteudo',
            'ver_pos',
            'gerir_pos',
            'atender_suporte',   # chat: caixa "Suporte Bendi" (superchat)
            'moderar_chat',      # chat: denúncias e bloqueios
        ],
        'moderador': [
            'ver_stats',
            'gerir_lojas',
            'gerir_produtos',
            'moderar_chat',
        ],
        'suporte': [
            'ver_stats',
            'gerir_utilizadores',
            'gerir_lojas',
            'gerir_encomendas',
            'gerir_conteudo',
            'ver_pos',
            'gerir_pos',
            'atender_suporte',
        ],
        'contabilista': [
            'ver_stats',
            'gerir_pagamentos',
            'gerir_encomendas',
            'ver_pos',
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
    # vídeo otimizado em segundo plano (app/utils/video.py)
    ficheiro_poster = models.ImageField(upload_to='posters/%Y/%m/', blank=True, null=True)
    ficheiro_estado = models.CharField(max_length=12, blank=True, default='')
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
    banner = models.FileField(
        upload_to='lojas/banners/%Y/%m/',
        null=True, blank=True,
        validators=[FileExtensionValidator(
            ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm', 'mov']
        )]
    )
    # vídeo otimizado em segundo plano (app/utils/video.py)
    banner_poster   = models.ImageField(upload_to='posters/%Y/%m/', blank=True, null=True)
    banner_estado   = models.CharField(max_length=12, blank=True, default='')
    layout_produtos = models.CharField(max_length=10, default='grid',
                                       choices=[('grid', 'Grelha'), ('list', 'Lista')])

    # Estado da loja — fonte de verdade. `ativa` é derivado (= estado 'ativa') e mantido
    # em sincronia em save(): todos os filtros existentes (ativa=True) continuam válidos.
    #   pendente  → criada, à espera de aprovação da plataforma
    #   ativa     → visível no site, recebe encomendas
    #   fechada   → fechada pelo dono (pode reabrir); encomendas em curso continuam
    #   suspensa  → suspensa pela plataforma (só o admin reactiva)
    ESTADOS = [
        ('pendente', 'Pendente de aprovação'),
        ('ativa',    'Ativa'),
        ('fechada',  'Fechada pelo dono'),
        ('suspensa', 'Suspensa pela plataforma'),
    ]
    estado          = models.CharField(max_length=10, choices=ESTADOS, default='pendente', db_index=True)
    estado_motivo   = models.CharField(max_length=300, blank=True, default='')
    estado_alterado_em = models.DateTimeField(null=True, blank=True)
    ativa           = models.BooleanField(default=False)
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
    
    pos_ativo = models.BooleanField(
        default=False,
        verbose_name='POS Ativo'
    )
    
    efatura_ativo = models.BooleanField(default=False)
    efatura_nif = models.CharField(max_length=20, blank=True)
    efatura_api_key = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # `ativa` acompanha sempre o estado
        self.ativa = self.estado == 'ativa'
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'estado' in update_fields and 'ativa' not in update_fields:
            kwargs['update_fields'] = [*update_fields, 'ativa']
        super().save(*args, **kwargs)

    def mudar_estado(self, novo, motivo=''):
        """
        Muda o estado (valida-o) e grava. Se a loja deixa de estar activa, cancela as
        encomendas ainda por pagar (já não podem ser pagas). Devolve quantas cancelou.

        A linha da loja fica bloqueada até ao fim da transacção — encomenda_criar bloqueia-a
        também, por isso nenhuma encomenda nova escapa entre a mudança e o cancelamento.
        """
        from .utils.encomendas import cancelar_pendentes_da_loja

        if novo not in dict(self.ESTADOS):
            raise ValueError(f'Estado inválido: {novo}')
        with transaction.atomic():
            Loja.objects.select_for_update().filter(pk=self.pk).first()
            self.estado             = novo
            self.estado_motivo      = motivo or ''
            self.estado_alterado_em = now()
            self.save(update_fields=['estado', 'estado_motivo', 'estado_alterado_em', 'ativa'])
            return cancelar_pendentes_da_loja(self) if novo != 'ativa' else 0


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
    # chat: staff/contabilista só atendem a caixa da loja se o dono ativar (dono e gestor sempre)
    pode_chat   = models.BooleanField(default=False)

    class Meta:
        unique_together = ('loja', 'utilizador')

    def __str__(self):
        return f'{self.utilizador} — {self.role} @ {self.loja}'

    def pode(self, permissao: str) -> bool:
        """Verifica se este membro tem uma permissão específica."""
        if not self.ativo:
            return False
        return permissao in self.PERMISSOES.get(self.role, [])

    @property
    def atende_chat(self) -> bool:
        """Pode ler e responder na caixa de mensagens da loja (app.chat)."""
        return self.ativo and (self.role in ('dono', 'gestor') or self.pode_chat)

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
    # tipo próprio de um POS (para os produtos próprios do POS). loja=None e pos=None → global.
    pos              = models.ForeignKey(
                         'pos.ConfiguracaoPOS',
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
        if self.pos_id:
            return f'{self.nome} [POS {self.pos_id}]'
        return f'{self.nome} [global]'

    @property
    def is_global(self):
        return self.loja_id is None and self.pos_id is None

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
                        ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'mov', 'mkv','avif','webp']
                    )],
                    blank=True, null=True
                  )
    # vídeo otimizado em segundo plano (app/utils/video.py)
    ficheiro_poster = models.ImageField(upload_to='posters/%Y/%m/', blank=True, null=True)
    ficheiro_estado = models.CharField(max_length=12, blank=True, default='')
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
    
    disponivel_pos = models.BooleanField(
        default=True,
        verbose_name='Disponível no POS'
    )

    # True quando o dono configurou stock por variação (grelha de VarianteProduto).
    # Enquanto False, o produto usa o stock total do Inventario (comportamento antigo).
    stock_por_variante = models.BooleanField(default=False)

    # Conjunto (menu, pack, cabaz): feito de outros produtos da loja (ComponenteConjunto).
    # Não tem stock próprio — vender um conjunto desconta o stock de cada componente.
    e_conjunto = models.BooleanField(default=False)

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


class VarianteProduto(models.Model):
    """
    Uma combinação concreta das opções-variante de um produto, com stock próprio.
      combinacao: {"cor": "preto", "tamanho": "M"}  (só atributos com "variante": true no tipo)
      chave:      "cor=preto|tamanho=M"              (ordenada, única por produto)
    Combinações que deixam de existir são desactivadas (nunca apagadas) para manter
    o histórico das encomendas. Com produto.stock_por_variante, o Inventario do
    produto guarda a soma das variantes activas.
    """
    produto    = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='variantes')
    combinacao = models.JSONField(default=dict)
    chave      = models.CharField(max_length=500)
    quantidade = models.PositiveIntegerField(default=0)
    preco      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                     validators=[MinValueValidator(0)],
                                     help_text='Vazio → usa o preço do produto')
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


class ComponenteConjunto(models.Model):
    """
    Um produto dentro de um conjunto (ex.: "1× Batata média" no "Menu Hambúrguer").
    O componente é um produto normal da mesma loja, que continua à venda sozinho; vender o
    conjunto desconta o stock dele (na variação escolhida, se o produto usa stock por variação).
    RESTRICT: um produto/variação dentro de um conjunto não pode ser apagado da BD — excepto
    quando o próprio conjunto é apagado na mesma operação (ex.: eliminar a loja inteira).
    """
    conjunto   = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='componentes')
    produto    = models.ForeignKey(Produto, on_delete=models.RESTRICT, related_name='em_conjuntos')
    variante   = models.ForeignKey(VarianteProduto, on_delete=models.RESTRICT, null=True, blank=True,
                                   related_name='em_conjuntos')
    quantidade = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    # produto com variações: o cliente escolhe a variação (ex.: o tamanho da peça) em vez de ser fixa
    variante_livre = models.BooleanField(default=False)
    ordem      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'id']
        constraints = [
            models.CheckConstraint(check=~models.Q(conjunto=models.F('produto')),
                                   name='conjunto_nao_se_contem'),
            models.UniqueConstraint(fields=['conjunto', 'produto', 'variante'],
                                    name='componente_unico_por_variante'),
            models.UniqueConstraint(fields=['conjunto', 'produto'], condition=models.Q(variante__isnull=True),
                                    name='componente_unico_sem_variante'),
        ]

    def __str__(self):
        return f'{self.quantidade}× {self.produto.nome} em {self.conjunto.nome}'


class GrupoEscolha(models.Model):
    """
    Escolha do cliente dentro de um conjunto (ex.: "Bebida — escolhe 1", "Extras — até 3").
    O cliente escolhe entre `minimo` e `maximo` opções diferentes; cada opção é um produto
    da loja (na variação definida) e pode ter um custo extra.
    """
    conjunto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='grupos')
    nome     = models.CharField(max_length=60)
    minimo   = models.PositiveSmallIntegerField(default=1)
    maximo   = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    ordem    = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'id']
        constraints = [
            models.CheckConstraint(check=models.Q(minimo__lte=models.F('maximo')), name='grupo_minimo_ate_maximo'),
        ]

    def __str__(self):
        return f'{self.nome} ({self.minimo}–{self.maximo}) em {self.conjunto.nome}'


class OpcaoEscolha(models.Model):
    """Uma opção de um grupo (ex.: "Fanta 33cl", +0,50 €). Desconta o stock do produto se escolhida."""
    grupo       = models.ForeignKey(GrupoEscolha, on_delete=models.CASCADE, related_name='opcoes')
    produto     = models.ForeignKey(Produto, on_delete=models.RESTRICT, related_name='em_opcoes')
    variante    = models.ForeignKey(VarianteProduto, on_delete=models.RESTRICT, null=True, blank=True,
                                    related_name='em_opcoes')
    quantidade  = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    variante_livre = models.BooleanField(default=False)   # o cliente escolhe a variação
    preco_extra = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                      validators=[MinValueValidator(0)])
    ordem       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'id']

    def __str__(self):
        return f'{self.produto.nome} em {self.grupo}'


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
    variante    = models.ForeignKey('VarianteProduto', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='+')
    # conjunto: opções escolhidas pelo cliente {"<grupo_id>": [<opcao_id>, ...]}
    escolhas    = models.JSONField(default=dict, blank=True)

    @property
    def preco_unitario(self):
        if self.variante_id and self.variante.preco is not None:
            return self.variante.preco
        if self.escolhas and self.produto.e_conjunto:
            from .utils.conjuntos import preco_com_escolhas
            return preco_com_escolhas(self.produto, self.escolhas)
        return self.produto.preco

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

    # PROTECT: encomendas são registos financeiros — apagar o comprador ou a loja nunca as apaga
    comprador       = models.ForeignKey(Utilizador, on_delete=models.PROTECT, related_name='encomendas')
    loja            = models.ForeignKey(Loja, on_delete=models.PROTECT, related_name='encomendas')
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
    variante    = models.ForeignKey('VarianteProduto', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='itens_encomenda')
    # conjunto: o que levava no momento da compra (para o histórico e para repor o stock)
    # [{"origem": "loja", "produto_id", "variante_id", "nome", "quantidade" (por unidade)}]
    componentes = models.JSONField(default=list, blank=True)


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

    encomenda           = models.OneToOneField(Encomenda, on_delete=models.PROTECT, related_name='pagamento')   # registo financeiro
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
# CHAT antigo — substituído pela app app.chat (caixas de mensagens).
# Só fica esta função: a migração 0001 importa-a (upload_to=app.models.chat_upload).
# ══════════════════════════════════════════════════════════════

def chat_upload(instance, filename):
    return f'chat/{now():%Y/%m}/{filename}'


class Comissao(models.Model):
    STATUS = [
        ('pendente',   'Pendente'),    # registada, aguarda liquidacao
        ('liquidada',  'Liquidada'),   # paga ao administrador
    ]
 
    # PROTECT: comissões são registos financeiros
    encomenda        = models.OneToOneField(
                           Encomenda, on_delete=models.PROTECT,
                           related_name='comissao'
                       )
    loja             = models.ForeignKey(
                           Loja, on_delete=models.PROTECT,
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
        ('loja_suspensa',            'Loja suspensa'),
        ('loja_reativada',           'Loja reactivada'),
        ('loja_fechada',             'Loja fechada pelo dono'),
        ('nova_encomenda',           'Nova encomenda'),
        ('pagamento_aprovado',       'Pagamento aprovado'),
        ('pagamento_reembolsar',     'Pagamento a reembolsar'),
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

# ══════════════════════════════════════════════════════════════
# PÁGINAS INSTITUCIONAIS DA PLATAFORMA (rodapé da home)
# ══════════════════════════════════════════════════════════════

class PaginaInstitucional(models.Model):
    """
    Conteúdo editável no painel de admin e mostrado num popup na home.
      conteudo → texto livre (parágrafos, "## Título", "- item")
      dados    → campos estruturados conforme o tipo de página:
                   faq:      {"perguntas": [{"pergunta": "...", "resposta": "..."}]}
                   contacto: {"email", "telefone", "whatsapp", "morada", "horario"}
    """
    SLUGS = [
        ('ajuda',       'Ajuda'),
        ('contacto',    'Contacto'),
        ('faq',         'FAQ'),
        ('termos',      'Termos de Serviço'),
        ('privacidade', 'Privacidade'),
    ]
    SECCOES = [
        ('suporte', 'Suporte'),
        ('legal',   'Legal'),
    ]

    slug             = models.SlugField(max_length=30, unique=True, choices=SLUGS)
    seccao           = models.CharField(max_length=10, choices=SECCOES, default='suporte')
    titulo           = models.CharField(max_length=120)
    conteudo         = models.TextField(blank=True, default='')
    dados            = models.JSONField(default=dict, blank=True)
    ativo            = models.BooleanField(default=True)
    ordem            = models.PositiveSmallIntegerField(default=0)
    data_atualizacao = models.DateTimeField(auto_now=True)
    atualizado_por   = models.ForeignKey(
        Utilizador, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )

    class Meta:
        ordering = ['seccao', 'ordem']

    def __str__(self):
        return self.titulo


# ══════════════════════════════════════════════════════════════
# CONVERSÃO DE VÍDEO (fila em segundo plano — app/utils/video.py)
# ══════════════════════════════════════════════════════════════

class ConversaoVideo(models.Model):
    """
    Uma tarefa de otimização de vídeo. A tabela é a própria fila: o worker
    (manage.py processar_videos) apanha as pendentes com select_for_update(skip_locked),
    por isso sobrevive a reinícios e funciona igual em dev e prod.
    """
    ESTADOS = [
        ('pendente',    'Pendente'),
        ('a_processar', 'A processar'),
        ('pronto',      'Pronto'),
        ('erro',        'Erro'),
        ('substituido', 'Substituído'),   # o ficheiro mudou antes de acabar
    ]

    modelo        = models.CharField(max_length=20)          # 'loja' | 'produto' | 'galeria'
    objeto_id     = models.PositiveBigIntegerField()
    campo         = models.CharField(max_length=30)          # 'banner' | 'ficheiro'
    ficheiro      = models.CharField(max_length=255)         # nome no storage quando foi agendado
    estado        = models.CharField(max_length=12, choices=ESTADOS, default='pendente', db_index=True)
    tentativas    = models.PositiveSmallIntegerField(default=0)
    erro          = models.TextField(blank=True, default='')
    bytes_origem  = models.PositiveBigIntegerField(null=True, blank=True)
    bytes_final   = models.PositiveBigIntegerField(null=True, blank=True)
    duracao_s     = models.FloatField(null=True, blank=True)  # tempo que a conversão demorou
    criado_em     = models.DateTimeField(auto_now_add=True)
    iniciado_em   = models.DateTimeField(null=True, blank=True)
    terminado_em  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['criado_em']
        indexes  = [models.Index(fields=['modelo', 'objeto_id', 'campo'])]

    def __str__(self):
        return f'{self.modelo}#{self.objeto_id}.{self.campo} ({self.estado})'


class FicheiroParaApagar(models.Model):
    """
    Fila de limpeza do storage (app/utils/limpeza.py). Quando um ficheiro é substituído ou o
    registo dono é apagado, o nome entra aqui e o worker (processar_videos) apaga-o em segundo
    plano — o pedido do utilizador responde logo, mesmo que sejam centenas de ficheiros no R2.
    Antes de apagar, o worker confirma que nenhum registo voltou a usar o ficheiro.
    """
    nome          = models.CharField(max_length=500, db_index=True)   # nome no storage por defeito
    origem        = models.CharField(max_length=60, blank=True, default='')  # ex.: 'substituido:loja.banner'
    tentativas    = models.PositiveSmallIntegerField(default=0)
    erro          = models.TextField(blank=True, default='')
    criado_em     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']

    def __str__(self):
        return self.nome


# ══════════════════════════════════════════════════════════════
# FAVORITOS — produtos e lojas guardados pelo utilizador (coração nos cards)
# ══════════════════════════════════════════════════════════════

class Favorito(models.Model):
    utilizador = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='favoritos')
    # um dos dois (a base de dados garante)
    produto    = models.ForeignKey(Produto, null=True, blank=True, on_delete=models.CASCADE, related_name='favoritado_por')
    loja       = models.ForeignKey(Loja, null=True, blank=True, on_delete=models.CASCADE, related_name='favoritada_por')
    criado_em  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em', '-id']
        constraints = [
            models.CheckConstraint(
                name='favorito_produto_ou_loja',
                check=(models.Q(produto__isnull=False, loja__isnull=True)
                       | models.Q(produto__isnull=True, loja__isnull=False)),
            ),
            models.UniqueConstraint(fields=['utilizador', 'produto'], condition=models.Q(produto__isnull=False),
                                    name='favorito_produto_unico'),
            models.UniqueConstraint(fields=['utilizador', 'loja'], condition=models.Q(loja__isnull=False),
                                    name='favorito_loja_unico'),
        ]

    def __str__(self):
        return f'{self.utilizador} ♥ {self.produto or self.loja}'
