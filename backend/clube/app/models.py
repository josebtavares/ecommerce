import uuid
from decimal import Decimal

from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils.timezone import now
from .utils.fiscal import REGIMES


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
    # moderação (utils/moderacao.py): 'suspenso' pode ter fim; o motivo é o do estado actual
    suspenso_ate    = models.DateTimeField(null=True, blank=True)
    motivo_estado   = models.CharField(max_length=500, blank=True, default='')
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
            'gerir_plataforma',  # definições do site (fuso horário)
            'gerir_subscricoes', # planos, subscrições e faturas das lojas
            'gerir_faturacao',   # dados fiscais, faturas registadas, faturas do Bende (utils/fiscal.py)
            'gerir_home',        # secções da página inicial
            'gerir_devolucoes',  # reembolsos: disputas e decisões finais
            'ver_relatorios',    # relatórios financeiros e exportações (Excel, PDF, CSV)
            'gerir_backups',     # backups da base de dados: ver, fazer e descarregar (utils/backups.py)
            'exportar_lojas',    # exportar os dados de uma loja (ZIP com clientes, vendas...) — utils/exportacao_loja.py
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
            'gerir_devolucoes',
        ],
        'contabilista': [
            'ver_stats',
            'gerir_pagamentos',
            'gerir_encomendas',
            'ver_pos',
            'gerir_subscricoes',
            'gerir_faturacao',
            'ver_relatorios',
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
        # uma suspensão com data de fim já passada conta como activa (levanta-se em moderacao.levantar_expiradas)
        if self.status == 'suspenso' and self.suspenso_ate:
            from django.utils import timezone
            return self.suspenso_ate <= timezone.now()
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
    # como a plataforma ganha com a loja: % por venda (comissão) ou mensalidade (subscrição — ver Subscricao)
    MODELOS_COBRANCA = [('comissao', 'Comissão por venda'), ('subscricao', 'Subscrição')]
    modelo_cobranca = models.CharField(max_length=10, choices=MODELOS_COBRANCA, default='comissao', db_default='comissao')
    # última troca de modelo (o dono só pode trocar uma vez a cada 3 meses)
    modelo_alterado_em = models.DateTimeField(null=True, blank=True)

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

    # ── Dados fiscais de quem vende (ver utils/fiscal.py) — só o dono vê/altera, nunca públicos ──
    nif = models.CharField(max_length=9, blank=True, default='', db_default='')
    regime_fiscal = models.CharField(max_length=10, blank=True, default='', db_default='',
                                     choices=REGIMES)
    # quando o dono aceitou a declaração de responsabilidade fiscal (vazio = lojas antigas, por preencher)
    dados_fiscais_aceites_em = models.DateTimeField(null=True, blank=True)

    # ── Horário (ver utils/horarios.py) ──
    # desligado = aberta 24h (como antes). db_default: o código antigo continua a gravar lojas
    # entre a migração e o deploy.
    FORA_HORARIO = [
        ('agendar',  'Aceitar encomendas para a abertura'),
        ('bloquear', 'Não aceitar encomendas'),
    ]
    horario_ativo = models.BooleanField(default=False, db_default=False)
    fora_horario  = models.CharField(max_length=10, choices=FORA_HORARIO,
                                     default='agendar', db_default='agendar')
    # o cliente escolhe dia e hora para receber/levantar (só dentro do horário)
    agendamento_ativo        = models.BooleanField(default=False, db_default=False)
    agendamento_intervalo    = models.PositiveSmallIntegerField(default=30, db_default=30)   # minutos entre horas
    agendamento_dias         = models.PositiveSmallIntegerField(default=7, db_default=7)     # dias que se podem escolher (hoje incluído)
    agendamento_antecedencia = models.PositiveSmallIntegerField(default=30, db_default=30)   # minutos mínimos a partir de agora
    # aceitar encomendas só até X minutos antes de fechar (0 = até fechar)
    ultima_encomenda_min = models.PositiveSmallIntegerField(default=0, db_default=0)
    # "Fechar agora": fechada para encomendas até esta hora (vazio/passado = sem pausa)
    pausa_ate            = models.DateTimeField(null=True, blank=True)
    # último dia em que se avisou a equipa das encomendas agendadas (worker)
    aviso_agendadas_data = models.DateField(null=True, blank=True)

    # Devoluções por "mudei de ideias": dias depois de receber (0 = a loja não aceita).
    # Os problemas reais (defeito, errado, em falta, não chegou) têm sempre 48h — ver utils/devolucoes.py
    prazo_devolucao_dias = models.PositiveSmallIntegerField(default=14, db_default=14,
                                                            validators=[MaxValueValidator(365)])

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
            # serviços: os clientes com marcações futuras sabem que a loja fechou (ou voltou)
            from .servicos.ciclo import sincronizar_depois
            sincronizar_depois(self)
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
            'ver_subscricao',
            'pagar_subscricao',
            'editar_loja',
            'apagar_loja',
            'gerir_dados_fiscais',     # NIF e regime (utils/fiscal.py) — só o dono
            'gerir_staff',
            'gerir_produtos',
            'gerir_inventario',
            'gerir_encomendas',
            'gerir_devolucoes',
            'atribuir_condutor',
            'gerir_pagamentos',
            'gerir_entregas',
            'ver_relatorios',
            'gerir_metodos_pagamento',
            'gerir_opcoes_entrega',
            'gerir_template',
            'gerir_servicos',
            'gerir_marcacoes',
            'gerir_faturacao',         # aba Faturação: comprovativos e faturas de todas as vendas
        ],
        'gestor': [
            'ver_loja',
            'ver_subscricao',
            'editar_loja',
            'gerir_staff',
            'gerir_produtos',
            'gerir_inventario',
            'gerir_encomendas',
            'gerir_devolucoes',
            'atribuir_condutor',
            'gerir_pagamentos',
            'gerir_entregas',
            'ver_relatorios',
            'gerir_metodos_pagamento',
            'gerir_opcoes_entrega',
            'gerir_template',
            'gerir_servicos',
            'gerir_marcacoes',
            'gerir_faturacao',         # aba Faturação: comprovativos e faturas de todas as vendas
        ],
        'staff': [
            'ver_loja',
            'gerir_produtos',
            'gerir_inventario',
            'gerir_encomendas',
            'gerir_marcacoes',
        ],
        'contabilista': [
            'ver_loja',
            'ver_subscricao',
            'gerir_pagamentos',
            'ver_relatorios',
            'gerir_faturacao',
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
    """Uma opção de um grupo (ex.: "Fanta 33cl", +50$00). Desconta o stock do produto se escolhida."""
    grupo       = models.ForeignKey(GrupoEscolha, on_delete=models.CASCADE, related_name='opcoes')
    produto     = models.ForeignKey(Produto, on_delete=models.RESTRICT, related_name='em_opcoes')
    variante    = models.ForeignKey(VarianteProduto, on_delete=models.RESTRICT, null=True, blank=True,
                                    related_name='em_opcoes')
    quantidade  = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    variante_livre = models.BooleanField(default=False)   # o cliente escolhe a variação
    preco_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0,
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

def caminho_fatura_encomenda(instance, filename):
    # nome aleatório: a fatura tem dados do cliente e o armazenamento (R2) serve os ficheiros por URL
    return f'faturas/{instance.loja_id}/{uuid.uuid4().hex}.pdf'


def caminho_fatura_bende(instance, filename):
    # faturas que o Bende emite às lojas/POS (subscrições e comissões)
    return f'faturas/bende/{uuid.uuid4().hex}.pdf'


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
    # vazio = o mais cedo possível. agendamento_origem diz porquê:
    #   'abertura' → feita com a loja fechada, preparar a partir da abertura
    #   'cliente'  → o cliente escolheu dia e hora para receber/levantar
    AGENDAMENTO_ORIGEM = [('abertura', 'Loja fechada — para a abertura'), ('cliente', 'Escolhida pelo cliente')]
    agendada_para   = models.DateTimeField(null=True, blank=True, db_index=True)
    agendamento_origem = models.CharField(max_length=10, choices=AGENDAMENTO_ORIGEM, blank=True,
                                          default='', db_default='')
    # modelo de cobrança da loja quando a encomenda foi feita ('' = antiga → comissão)
    modelo_cobranca = models.CharField(max_length=10, blank=True, default='', db_default='')
    # quando passou a "concluido" (entregue/levantada) — conta o prazo para pedir devolução
    data_conclusao  = models.DateTimeField(null=True, blank=True)
    # fatura emitida pela loja no e-Fatura (ela emite fora do Bende e regista aqui — utils/fiscal.py)
    fatura_numero   = models.CharField(max_length=60, blank=True, default='', db_default='')
    fatura_pdf      = models.FileField(upload_to=caminho_fatura_encomenda, blank=True, default='', db_default='',
                                       validators=[FileExtensionValidator(['pdf'])])
    fatura_registada_em = models.DateTimeField(null=True, blank=True)
    # comprovativo (documento interno, utils/documentos.py) enviado por email ao cliente — uma vez, ao pagar
    comprovativo_enviado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return f'Encomenda #{self.pk} — {self.comprador} @ {self.loja}'

    @property
    def valor_devido(self):
        """O que o cliente paga: o total menos os artigos esgotados descontados antes de pagar (dinheiro)."""
        from django.db.models import Sum
        abatido = (self.reembolsos.filter(estado='reembolsado', metodo='abatido')
                   .aggregate(t=Sum('valor_aprovado'))['t'] or 0) if self.pk else 0
        return self.valor_total - abatido

    @property
    def percentagem_comissao_aplicavel(self):
        """% de comissão desta encomenda: 0 se foi feita com a loja em subscrição."""
        if (self.modelo_cobranca or 'comissao') == 'subscricao':
            return Decimal('0')
        return self.loja.percentagem_comissao


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
    # custo unitário (preço de custo do inventário) no momento da venda — a margem dos relatórios não muda
    # se o custo for alterado depois. Vazio nas vendas antigas e nos menus/conjuntos.
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


    def __str__(self):
        return f'{self.quantidade}x {self.produto} (enc. #{self.encomenda_id})'


# ══════════════════════════════════════════════════════════════
# ENTREGA & CONDUTOR  (opcionais por loja)
# ══════════════════════════════════════════════════════════════

class OpcaoEntrega(models.Model):
    loja            = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='opcoes_entrega')
    nome            = models.CharField(max_length=100)          # ex: 'Standard', 'Expresso'
    preco           = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tempo_estimado  = models.CharField(max_length=100, blank=True, default='')  # ex: '30–45 min'
    area_cobertura  = models.CharField(max_length=300, blank=True, default='')
    ativa           = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.nome} ({self.loja.nome})'


class HorarioLoja(models.Model):
    """
    Um intervalo em que a loja está aberta num dia da semana (0 = segunda … 6 = domingo).
    Vários intervalos no mesmo dia = pausas (ex.: 08:00–12:00 e 14:00–22:00).
    fecha <= abre → passa da meia-noite (18:00–02:00 fecha às 02:00 do dia seguinte).
    """
    DIAS = [(0, 'Segunda'), (1, 'Terça'), (2, 'Quarta'), (3, 'Quinta'),
            (4, 'Sexta'), (5, 'Sábado'), (6, 'Domingo')]

    loja       = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.PositiveSmallIntegerField(choices=DIAS)
    abre       = models.TimeField()
    fecha      = models.TimeField()

    class Meta:
        ordering = ['dia_semana', 'abre']
        indexes  = [models.Index(fields=['loja', 'dia_semana'])]

    def __str__(self):
        return f'{self.loja} · {self.get_dia_semana_display()} {self.abre:%H:%M}–{self.fecha:%H:%M}'


class ExcecaoHorario(models.Model):
    """
    Dias especiais (feriados, férias, horário diferente) de `inicio` a `fim` (inclusive).
    intervalos vazio = fechado; senão substitui o horário da semana nesses dias
    ([{"abre": "08:00", "fecha": "16:00"}], como HorarioLoja).
    """
    loja       = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='excecoes')
    inicio     = models.DateField()
    fim        = models.DateField()
    intervalos = models.JSONField(default=list, blank=True)
    mensagem   = models.CharField(max_length=120, blank=True, default='')

    class Meta:
        ordering = ['inicio']
        indexes  = [models.Index(fields=['loja', 'fim'])]

    def __str__(self):
        return f'{self.loja} · {self.inicio}–{self.fim} {"fechado" if not self.intervalos else "horário especial"}'


class ConfiguracaoPlataforma(models.Model):
    """Definições globais do site (uma só linha — ConfiguracaoPlataforma.atual())."""
    fuso_horario     = models.CharField(max_length=64, default='Atlantic/Cape_Verde')
    # dias grátis das lojas novas em subscrição (0 = paga desde a aprovação)
    subscricao_dias_teste = models.PositiveSmallIntegerField(default=30, db_default=30)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração da plataforma'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        from django.core.cache import cache
        cache.delete('configuracao_plataforma')

    @classmethod
    def atual(cls):
        from django.core.cache import cache
        cfg = cache.get('configuracao_plataforma')
        if cfg is None:
            cfg, _ = cls.objects.get_or_create(pk=1)
            cache.set('configuracao_plataforma', cfg, 300)
        return cfg

    def __str__(self):
        return f'Plataforma ({self.fuso_horario})'


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
        ('reembolsado_parcial', 'Parcialmente reembolsado'),
    ]

    encomenda           = models.OneToOneField(Encomenda, on_delete=models.PROTECT, related_name='pagamento')   # registo financeiro
    metodo              = models.ForeignKey(MetodoPagamento, on_delete=models.SET_NULL,
                                            null=True, blank=True)
    valor               = models.DecimalField(max_digits=10, decimal_places=2)
    status              = models.CharField(max_length=20, choices=STATUS, default='pendente')
    referencia_transacao= models.CharField(max_length=255, blank=True, default='')
    data_criacao        = models.DateTimeField(auto_now_add=True)
    # quando o dinheiro entrou (cartão: logo; dinheiro: na entrega) — os relatórios de recebimentos contam por aqui
    data_pagamento      = models.DateTimeField(null=True, blank=True, db_index=True)

    def save(self, *args, **kwargs):
        if self.status == 'aprovado' and not self.data_pagamento:
            from django.utils import timezone
            self.data_pagamento = timezone.now()
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = {*kwargs['update_fields'], 'data_pagamento'}
        super().save(*args, **kwargs)

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
        return f'Comissao #{self.pk} — {self.loja.nome} — {self.valor_comissao} CVE ({self.status})'
 
    @classmethod
    def registar(cls, encomenda):
        """
        Cria o registo de comissao para uma encomenda.
        Chama isto apos pagamento confirmado (cartao/mbway)
        ou quando encomenda.status = concluido (dinheiro).
        Evita duplicados com get_or_create.
        """
        if (encomenda.modelo_cobranca or 'comissao') == 'subscricao':
            return None, False          # loja em subscrição quando a encomenda foi feita → sem comissão
        loja = encomenda.loja
        percentagem   = loja.percentagem_comissao
        valor = encomenda.valor_devido      # sem os artigos esgotados descontados antes de pagar
        valor_comissao = (valor * percentagem / 100).quantize(
            __import__('decimal').Decimal('0.01')
        )
        comissao, criada = cls.objects.get_or_create(
            encomenda=encomenda,
            defaults={
                'loja':           loja,
                'valor_encomenda': valor,
                'percentagem':    percentagem,
                'valor_comissao': valor_comissao,
                'status':         'pendente',
            }
        )
        return comissao, criada


class FaturaComissoes(models.Model):
    """
    Fatura legal (e-Fatura) que o Bende emite a uma loja pelas comissões de um mês — uma por loja/mês.
    O extrato (documento interno com as comissões do mês) é gerado na hora (utils/documentos.py);
    aqui fica só a fatura que o admin registou.
    """
    loja           = models.ForeignKey(Loja, on_delete=models.PROTECT, related_name='faturas_comissoes')
    mes            = models.DateField()     # dia 1 do mês
    fatura_numero  = models.CharField(max_length=60)
    fatura_pdf     = models.FileField(upload_to=caminho_fatura_bende, blank=True, default='', db_default='',
                                      validators=[FileExtensionValidator(['pdf'])])
    fatura_registada_em = models.DateTimeField()
    # total das comissões (menos créditos) do mês quando a fatura foi registada: reembolsos depois → diferença à vista
    valor_faturado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-mes']
        constraints = [models.UniqueConstraint(fields=['loja', 'mes'], name='fatura_comissoes_loja_mes')]

    def __str__(self):
        return f'Fatura de comissões {self.mes:%Y-%m} — {self.loja} — {self.fatura_numero}'


class HistoricoFatura(models.Model):
    """
    Arquivo de todas as faturas registadas (vendas das lojas, dos POS e marcações, e faturas do Bende) — nada se apaga.
    Alterar ou remover uma fatura ANULA o registo (quem, quando, motivo) e o PDF fica aqui guardado
    (limpeza.em_uso vê este FileField, por isso o ficheiro nunca vai para a fila de limpeza).
    A fatura em vigor continua também nos campos fatura_* do documento (utils/fiscal.py).
    """
    TIPOS = [
        ('encomenda',   'Venda da loja'),
        ('mensalidade', 'Mensalidade (Bende)'),
        ('comissoes',   'Comissões do mês (Bende)'),
        ('venda_pos',   'Venda do POS'),
        ('marcacao',    'Marcação (serviço)'),
    ]
    tipo         = models.CharField(max_length=12, choices=TIPOS)
    referencia   = models.CharField(max_length=40, db_index=True)    # E-<id>, S-<id>, C-<loja>-<AAAAMM>, V-<conta>, M-<marcação>
    loja         = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True, related_name='historico_faturas')
    pos          = models.ForeignKey('pos.ConfiguracaoPOS', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='historico_faturas')
    encomenda    = models.ForeignKey('Encomenda', on_delete=models.SET_NULL, null=True, blank=True, related_name='historico_faturas')
    conta        = models.ForeignKey('pos.ContaMesa', on_delete=models.SET_NULL, null=True, blank=True, related_name='historico_faturas')
    marcacao     = models.ForeignKey('servicos.Marcacao', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='historico_faturas')
    fatura_subscricao = models.ForeignKey('FaturaSubscricao', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='historico_faturas')
    mes          = models.DateField(null=True, blank=True)            # comissões: dia 1 do mês
    numero       = models.CharField(max_length=60, db_index=True)
    pdf          = models.FileField(upload_to=caminho_fatura_bende, blank=True, default='',
                                    validators=[FileExtensionValidator(['pdf'])])
    registada_em = models.DateTimeField()
    registada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    anulada_em   = models.DateTimeField(null=True, blank=True)
    anulada_por  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    motivo       = models.CharField(max_length=300, blank=True, default='')

    class Meta:
        ordering = ['-registada_em', '-id']

    def __str__(self):
        return f'{self.referencia} — fatura {self.numero}' + (' (anulada)' if self.anulada_em else '')


class HistoricoDadosFiscais(models.Model):
    """Cada vez que uma loja/POS grava NIF + regime + declaração fica aqui uma linha (o que valia e desde quando)."""
    loja        = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True, related_name='historico_fiscal')
    pos         = models.ForeignKey('pos.ConfiguracaoPOS', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='historico_fiscal')
    nome        = models.CharField(max_length=200)                  # nome do vendedor nesse momento
    nif         = models.CharField(max_length=9)
    regime_fiscal = models.CharField(max_length=12, choices=REGIMES)
    aceites_em  = models.DateTimeField()
    alterado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['-aceites_em', '-id']

    def __str__(self):
        return f'{self.nome} — NIF {self.nif} ({self.regime_fiscal}) desde {self.aceites_em:%d/%m/%Y}'

    
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
        ('reembolso_pedido',         'Pedido de reembolso'),
        ('reembolso_atualizado',     'Reembolso actualizado'),
        ('reembolso_disputa',        'Reembolso em disputa'),
        ('encomenda_concluida_loja', 'Encomenda concluída na loja'),
        ('encomenda_cancelada_loja', 'Encomenda cancelada na loja'),
        ('stock_baixo',              'Stock baixo'),
        ('novo_staff',               'Novo membro de staff'),
        ('avaliacao_recebida',       'Nova avaliação recebida'),
        # Condutor
        ('entrega_atribuida',        'Entrega atribuída'),
        ('entrega_cancelada',        'Entrega cancelada'),
        ('agendadas_hoje',           'Encomendas agendadas para hoje'),
        ('subscricao_fatura',        'Fatura da subscrição'),
        ('subscricao_paga',          'Subscrição paga'),
        # Comprador
        ('encomenda_paga',           'Encomenda paga'),
        ('encomenda_enviada',        'Encomenda enviada'),
        ('encomenda_concluida',      'Encomenda concluída'),
        ('encomenda_cancelada',      'Encomenda cancelada'),
        # Staff
        ('encomenda_atualizada',     'Encomenda actualizada'),
        # Dono / admin
        ('exportacao_pronta',        'Exportação de dados pronta'),
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


# ══════════════════════════════════════════════════════════════
# SUBSCRIÇÕES — a loja paga uma mensalidade em vez de comissão (utils/subscricoes.py)
# ══════════════════════════════════════════════════════════════

class PlanoSubscricao(models.Model):
    """Planos gerais definidos pelo admin (mensal / trimestral / anual)."""
    PERIODICIDADES = [('mensal', 'Mensal'), ('trimestral', 'Trimestral'), ('anual', 'Anual')]
    MESES = {'mensal': 1, 'trimestral': 3, 'anual': 12}
    # o que o plano cobre: a loja online, o POS, ou a loja e o POS ligado a ela
    TIPOS = [('loja', 'Loja online'), ('pos', 'POS'), ('loja_pos', 'Loja + POS'), ('servicos', 'Serviços')]

    nome          = models.CharField(max_length=80)
    tipo          = models.CharField(max_length=10, choices=TIPOS, default='loja', db_default='loja', db_index=True)
    periodicidade = models.CharField(max_length=10, choices=PERIODICIDADES)
    preco         = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    descricao     = models.CharField(max_length=300, blank=True, default='')
    ativo         = models.BooleanField(default=True)
    ordem         = models.PositiveSmallIntegerField(default=0)
    # planos de Serviços (ex.: o plano de entrada): vazio = sem limite
    limite_marcacoes_mes = models.PositiveIntegerField(null=True, blank=True)
    limite_profissionais = models.PositiveSmallIntegerField(null=True, blank=True)
    data_criacao  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'preco']

    @property
    def meses(self):
        return self.MESES[self.periodicidade]

    def __str__(self):
        return f'{self.nome} ({self.get_periodicidade_display()} · {self.preco} CVE)'


class Subscricao(models.Model):
    """
    A subscrição de uma loja OU de um POS (uma por cada). `preco` e `meses` ficam fixos no
    contrato — mudar o preço do plano só vale para quem o escolha depois (ou na renovação).
    pago_ate = até quando o serviço está pago (ou o fim do período de teste).
    Um POS pode estar sem plano (plano vazio) no período grátis — escolhe-o antes de acabar.
    """
    ESTADOS = [
        ('aguarda',   'Aguarda aprovação da loja'),
        ('teste',     'Período de teste'),
        ('ativa',     'Em dia'),
        ('em_atraso', 'Em atraso'),
        ('suspensa',  'Suspensa'),
        ('cancelada', 'Cancelada'),
    ]
    # PROTECT: o histórico de faturas depende disto
    loja         = models.OneToOneField(Loja, on_delete=models.PROTECT, related_name='subscricao', null=True, blank=True)
    # CASCADE: um POS sem faturas apaga-se com a subscrição; com faturas, elas (PROTECT) impedem-no
    pos          = models.OneToOneField('pos.ConfiguracaoPOS', on_delete=models.CASCADE, related_name='subscricao',
                                        null=True, blank=True)
    # a subscrição do módulo Serviços de uma loja em comissão (as faturas levam loja = esta loja)
    loja_servicos = models.OneToOneField(Loja, on_delete=models.PROTECT, related_name='subscricao_servicos',
                                         null=True, blank=True)
    plano        = models.ForeignKey(PlanoSubscricao, on_delete=models.PROTECT, related_name='subscricoes', null=True, blank=True)
    preco        = models.DecimalField(max_digits=10, decimal_places=2)
    meses        = models.PositiveSmallIntegerField()
    estado       = models.CharField(max_length=10, choices=ESTADOS, default='teste', db_index=True)
    inicio       = models.DateField()
    pago_ate     = models.DateField()               # exclusivo: o primeiro dia já não pago
    teste_ate    = models.DateField(null=True, blank=True)   # exclusivo: fim do período grátis (vazio = sem teste)
    auto_renovar = models.BooleanField(default=True)
    # o dono pediu para passar a comissão: acontece neste dia (o fim do período pago)
    fim_agendado = models.DateField(null=True, blank=True)
    # o dono mudou de plano: vale a partir da renovação seguinte
    plano_seguinte = models.ForeignKey(PlanoSubscricao, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    # POS: incluído no plano Loja + POS da loja ligada (a subscrição da loja). Enquanto estiver,
    # o POS não tem faturas próprias; quando deixa de estar, tem 30 dias para pagar o seu plano.
    coberta_por  = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_cobertos')
    # último dia em que o POS ganhou os 30 dias por deixar de estar incluído (só um a cada 90 dias)
    cobertura_fim_em = models.DateField(null=True, blank=True)
    # avisos já enviados que não pertencem a uma fatura (POS sem plano: 'sp_d7', 'sp_fim'…)
    avisos       = models.JSONField(default=list, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(
            check=models.Q(loja__isnull=False, pos__isnull=True, loja_servicos__isnull=True)
            | models.Q(loja__isnull=True, pos__isnull=False, loja_servicos__isnull=True)
            | models.Q(loja__isnull=True, pos__isnull=True, loja_servicos__isnull=False),
            name='subscricao_loja_pos_ou_servicos')]

    @property
    def alvo(self):
        """A loja ou o POS desta subscrição (a loja, na de Serviços)."""
        if self.loja_servicos_id:
            return self.loja_servicos
        return self.loja if self.loja_id else self.pos

    @property
    def servicos(self):
        return bool(self.loja_servicos_id)

    def __str__(self):
        return f'Subscrição {self.alvo} · {self.plano.nome if self.plano_id else "sem plano"} · {self.estado} até {self.pago_ate}'


class FaturaSubscricao(models.Model):
    """Uma fatura por período. Registo financeiro — nunca se apaga (anula-se)."""
    ESTADOS = [('pendente', 'Por pagar'), ('paga', 'Paga'), ('anulada', 'Anulada')]
    METODOS = [('simulado', 'Pagamento simulado'), ('dinheiro', 'Dinheiro'), ('transferencia', 'Transferência'),
               ('oferta', 'Oferta da plataforma'), ('outro', 'Outro')]

    loja           = models.ForeignKey(Loja, on_delete=models.PROTECT, related_name='faturas_subscricao', null=True, blank=True)
    pos            = models.ForeignKey('pos.ConfiguracaoPOS', on_delete=models.PROTECT, related_name='faturas_subscricao',
                                       null=True, blank=True)
    subscricao     = models.ForeignKey(Subscricao, on_delete=models.PROTECT, related_name='faturas')
    plano          = models.ForeignKey(PlanoSubscricao, on_delete=models.PROTECT, related_name='faturas', null=True, blank=True)
    descricao      = models.CharField(max_length=200)
    periodo_inicio = models.DateField()
    periodo_fim    = models.DateField()           # exclusivo: o dia em que o período seguinte começa
    valor          = models.DecimalField(max_digits=10, decimal_places=2)
    estado         = models.CharField(max_length=10, choices=ESTADOS, default='pendente', db_index=True)
    vencimento     = models.DateField()
    paga_em        = models.DateTimeField(null=True, blank=True)
    metodo         = models.CharField(max_length=15, choices=METODOS, blank=True, default='')
    referencia     = models.CharField(max_length=100, blank=True, default='')
    notas          = models.CharField(max_length=300, blank=True, default='')
    # avisos já enviados ('d3', 'd0', 'atraso', 'a7'…, 'suspensa') — o worker não os repete
    avisos         = models.JSONField(default=list, blank=True)
    data_criacao   = models.DateTimeField(auto_now_add=True)
    # fatura legal do Bende (e-Fatura) registada pelo admin — utils/fiscal.py; o comprovativo é automático
    fatura_numero  = models.CharField(max_length=60, blank=True, default='', db_default='')
    fatura_pdf     = models.FileField(upload_to=caminho_fatura_bende, blank=True, default='', db_default='',
                                      validators=[FileExtensionValidator(['pdf'])])
    fatura_registada_em = models.DateTimeField(null=True, blank=True)
    comprovativo_enviado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-periodo_inicio', '-id']
        indexes  = [models.Index(fields=['loja', 'estado'])]

    @property
    def alvo(self):
        return self.loja if self.loja_id else self.pos

    @property
    def servicos(self):
        """Fatura da subscrição de Serviços (a loja é a mesma, a subscrição é outra)."""
        return bool(self.subscricao.loja_servicos_id)

    def __str__(self):
        return f'Fatura #{self.pk} — {self.alvo} — {self.periodo_inicio}→{self.periodo_fim} — {self.valor} CVE ({self.estado})'


# ══════════════════════════════════════════════════════════════
# HOME — secções montadas pelo admin (utils/home.py)
# ══════════════════════════════════════════════════════════════

class HomeSeccao(models.Model):
    """Rascunho da home: o admin edita estas linhas e publica (HomePublicacao guarda a cópia em uso)."""
    TIPOS = [
        ('hero',          'Hero (topo)'),
        ('lojas',         'Lojas'),
        ('produtos',      'Produtos'),
        ('loja_destaque', 'Loja em destaque'),
        ('categorias',    'Categorias de lojas'),
        ('banner',        'Banner'),
        ('cabecalho',     'Cabeçalho / divisor'),
        # grupos: cada um mostra um slider por categoria / tipo / categoria em destaque
        ('lojas_por_categoria',          'Lojas por categoria'),
        ('produtos_por_tipo',            'Produtos por tipo'),
        ('produtos_categorias_destaque', 'Produtos das categorias em destaque'),
        ('servicos',      'Serviços (marcações)'),
    ]
    FONTES = [
        ('manual', 'Escolhidos à mão'),
        ('auto',   'Automático'),
        ('misto',  'Fixados + automático'),
    ]

    tipo       = models.CharField(max_length=30, choices=TIPOS)
    titulo     = models.CharField(max_length=120, blank=True, default='')
    subtitulo  = models.CharField(max_length=200, blank=True, default='')
    ordem      = models.PositiveSmallIntegerField(default=0)
    ativa      = models.BooleanField(default=True)
    inicio     = models.DateTimeField(null=True, blank=True)   # só aparece a partir de…
    fim        = models.DateTimeField(null=True, blank=True)   # …e até (exclusivo)
    fonte      = models.CharField(max_length=10, choices=FONTES, default='auto')
    criterio   = models.CharField(max_length=30, blank=True, default='')   # utils/home.py CRITERIOS_*
    parametros = models.JSONField(default=dict, blank=True)               # categoria, tipo_id, loja_id, dias…
    limite     = models.PositiveSmallIntegerField(default=12)
    data_criacao  = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordem', 'id']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.titulo or "(sem título)"}'


class HomeImagem(models.Model):
    """Imagem carregada no construtor da home (banners). Fica guardada enquanto existir: as publicações
    antigas podem usá-la (o worker de limpeza só apaga ficheiros sem nenhum registo)."""
    ficheiro  = models.ImageField(upload_to='home/%Y/%m/',
                                  validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])])
    criado_em = models.DateTimeField(auto_now_add=True)


class HomeItem(models.Model):
    """Loja, produto ou banner escolhido à mão para uma secção."""
    seccao  = models.ForeignKey(HomeSeccao, on_delete=models.CASCADE, related_name='itens')
    ordem   = models.PositiveSmallIntegerField(default=0)
    loja    = models.ForeignKey(Loja, on_delete=models.CASCADE, null=True, blank=True, related_name='itens_home')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=True, blank=True, related_name='itens_home')
    # secção de serviços escolhidos à mão
    servico = models.ForeignKey('servicos.Servico', on_delete=models.CASCADE, null=True, blank=True, related_name='itens_home')
    # banner próprio (sem loja nem produto)
    titulo  = models.CharField(max_length=120, blank=True, default='')
    texto   = models.CharField(max_length=300, blank=True, default='')
    link    = models.CharField(max_length=300, blank=True, default='')
    imagem  = models.ForeignKey(HomeImagem, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['ordem', 'id']


class HomePublicacao(models.Model):
    """Cópia publicada das secções — é o que a home pública lê. A mais recente está em uso."""
    dados         = models.JSONField(default=list)
    publicado_em  = models.DateTimeField(auto_now_add=True)
    publicado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['-publicado_em', '-id']


# ══════════════════════════════════════════════════════════════
# DEVOLUÇÕES / REEMBOLSOS  (regras em utils/devolucoes.py)
# ══════════════════════════════════════════════════════════════

def _armazenamento_privado():
    # as fotos dos pedidos são privadas, como as imagens do chat (bucket/pasta sem acesso público)
    from .chat.imagens import armazenamento_privado
    return armazenamento_privado()


def foto_reembolso_upload(instance, filename):
    return f'reembolsos_privado/{now():%Y/%m}/{filename}'


class Reembolso(models.Model):
    """
    Pedido de reembolso de uma encomenda (total ou de alguns artigos). Registo financeiro: nunca se apaga.
    cancelamento → antes de receber (a encomenda é cancelada); devolucao → depois de concluída.
    """
    TIPOS = [
        ('cancelamento', 'Cancelamento antes de receber'),
        ('devolucao',    'Devolução depois de receber'),
    ]
    MOTIVOS = [
        ('cancelado_cliente', 'Cancelado pelo cliente'),
        ('cancelado_loja',    'Cancelado pela loja'),
        ('pagamento_tardio',  'Pago depois de cancelada'),
        ('defeito',           'Produto com defeito ou danificado'),
        ('errado',            'Produto errado'),
        ('em_falta',          'Faltou algo'),
        ('nao_chegou',        'A encomenda não chegou'),
        ('mudei_ideias',      'Mudei de ideias'),
        ('esgotado',          'Artigo esgotado'),          # a loja não tem o artigo (antes de enviar)
    ]
    ESTADOS = [
        ('pedido',          'A aguardar a loja'),
        ('proposta',        'A loja propôs outro valor'),
        ('em_disputa',      'Em análise pela Bendi'),
        ('aguarda_produto', 'A aguardar o produto'),
        ('a_devolver',      'A devolver em mão'),       # pago em dinheiro: a loja devolve, o cliente confirma
        ('reembolsado',     'Reembolsado'),
        ('recusado',        'Recusado'),
        ('cancelado',       'Desistiu'),
    ]
    ORIGENS = [('cliente', 'Cliente'), ('loja', 'Loja'), ('sistema', 'Automático')]
    METODOS = [('gateway', 'Pelo meio de pagamento'), ('manual', 'Em mão pela loja'),
               ('abatido', 'Descontado no valor a pagar')]   # ainda não estava pago (dinheiro na entrega)

    encomenda       = models.ForeignKey(Encomenda, on_delete=models.PROTECT, related_name='reembolsos')
    loja            = models.ForeignKey(Loja, on_delete=models.PROTECT, related_name='reembolsos')
    comprador       = models.ForeignKey(Utilizador, on_delete=models.PROTECT, related_name='reembolsos')
    tipo            = models.CharField(max_length=15, choices=TIPOS)
    motivo          = models.CharField(max_length=20, choices=MOTIVOS)
    origem          = models.CharField(max_length=10, choices=ORIGENS, default='cliente')
    descricao       = models.TextField(blank=True, default='')
    estado          = models.CharField(max_length=15, choices=ESTADOS, default='pedido', db_index=True)

    valor_pedido    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_entrega   = models.DecimalField(max_digits=10, decimal_places=2, default=0)   # parte de valor_pedido
    valor_aprovado  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    devolver_produto  = models.BooleanField(default=False)
    produto_recebido_em = models.DateTimeField(null=True, blank=True)
    stock_reposto     = models.BooleanField(default=False)

    metodo          = models.CharField(max_length=10, choices=METODOS, blank=True, default='')
    referencia      = models.CharField(max_length=255, blank=True, default='')

    prazo_resposta  = models.DateTimeField(null=True, blank=True)    # a loja tem até aqui; depois vai à Bendi
    escalado_em     = models.DateTimeField(null=True, blank=True)
    motivo_recusa   = models.TextField(blank=True, default='')
    # o que a loja respondeu (fica mesmo depois de a Bendi decidir — é o histórico do pedido)
    RESPOSTAS_LOJA = [('aceite', 'Aceitou'), ('recusado', 'Recusou'), ('proposta', 'Propôs outro valor'),
                      ('sem_resposta', 'Não respondeu a tempo')]
    resposta_loja      = models.CharField(max_length=12, choices=RESPOSTAS_LOJA, blank=True, default='')
    data_resposta_loja = models.DateTimeField(null=True, blank=True)
    decidido_por    = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='reembolsos_decididos')
    decisao_admin   = models.BooleanField(default=False)             # decisão final da Bendi
    data_decisao    = models.DateTimeField(null=True, blank=True)
    # data_reembolso = quando o dinheiro passou a ser devido ao cliente (pagamento e comissão já acertados)
    data_reembolso  = models.DateTimeField(null=True, blank=True)
    # dinheiro em mão: a loja diz que entregou → o cliente confirma (ou fecha sozinho em 7 dias)
    entregue_em     = models.DateTimeField(null=True, blank=True)
    recebido_em     = models.DateTimeField(null=True, blank=True)
    recebido_auto   = models.BooleanField(default=False)
    # o cliente diz que não recebeu o dinheiro (em mão, ou do gateway depois de 10 dias) → Bendi
    nao_recebido_em = models.DateTimeField(null=True, blank=True)
    data_criacao    = models.DateTimeField(auto_now_add=True)
    data_atualizacao= models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_criacao']
        indexes = [models.Index(fields=['loja', 'estado'])]

    def __str__(self):
        return f'Reembolso #{self.pk} — encomenda #{self.encomenda_id} ({self.estado})'


class ItemReembolso(models.Model):
    reembolso  = models.ForeignKey(Reembolso, on_delete=models.CASCADE, related_name='itens')
    item       = models.ForeignKey(ItemEncomenda, on_delete=models.PROTECT, related_name='reembolsos')
    quantidade = models.PositiveIntegerField()
    valor      = models.DecimalField(max_digits=10, decimal_places=2)


class MensagemReembolso(models.Model):
    """Conversa do pedido (cliente, loja e, em disputa, a Bendi) — separada do chat privado loja↔cliente."""
    PAPEIS = [('cliente', 'Cliente'), ('loja', 'Loja'), ('admin', 'Bendi'), ('sistema', 'Sistema')]

    reembolso = models.ForeignKey(Reembolso, on_delete=models.CASCADE, related_name='mensagens')
    autor     = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    papel     = models.CharField(max_length=10, choices=PAPEIS)
    texto     = models.TextField(blank=True, default='')
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']


class FotoReembolso(models.Model):
    reembolso = models.ForeignKey(Reembolso, on_delete=models.CASCADE, related_name='fotos')
    mensagem  = models.ForeignKey(MensagemReembolso, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='fotos')
    autor     = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    ficheiro  = models.FileField(upload_to=foto_reembolso_upload, storage=_armazenamento_privado)
    criada_em = models.DateTimeField(auto_now_add=True)


class CreditoComissao(models.Model):
    """
    Comissão a devolver à loja por um reembolso de uma encomenda cuja comissão já foi liquidada.
    Desconta-se na próxima liquidação. (Se a comissão ainda está pendente, recalcula-se nela.)
    """
    ESTADOS = [('pendente', 'Por descontar'), ('descontado', 'Descontado')]

    loja           = models.ForeignKey(Loja, on_delete=models.PROTECT, related_name='creditos_comissao')
    comissao       = models.ForeignKey(Comissao, on_delete=models.PROTECT, related_name='creditos')
    reembolso      = models.OneToOneField(Reembolso, on_delete=models.PROTECT, related_name='credito_comissao')
    valor          = models.DecimalField(max_digits=10, decimal_places=2)
    estado         = models.CharField(max_length=12, choices=ESTADOS, default='pendente', db_index=True)
    data_criacao   = models.DateTimeField(auto_now_add=True)
    data_desconto  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-data_criacao']


class RelatorioGerado(models.Model):
    """Registo de cada exportação de um relatório (quem, quando, o quê e com que filtros) — auditoria."""
    utilizador = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True, related_name='relatorios_gerados')
    loja       = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True, related_name='relatorios_gerados')
    pos        = models.ForeignKey('pos.ConfiguracaoPOS', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='relatorios_gerados')
    autor      = models.CharField(max_length=150, blank=True, default='')   # nome de quem gerou (membros do POS não são Utilizador)
    relatorio  = models.CharField(max_length=40)
    formato    = models.CharField(max_length=5)
    inicio     = models.DateField()
    fim        = models.DateField()
    filtros    = models.JSONField(default=dict, blank=True)
    linhas     = models.PositiveIntegerField(default=0)
    data_criacao = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return f'{self.relatorio} ({self.formato}) por {self.utilizador_id} em {self.data_criacao:%Y-%m-%d %H:%M}'


class BackupBD(models.Model):
    """Backup completo da base de dados (pg_dump) guardado fora do Railway — utils/backups.py."""
    TIPOS   = [('automatico', 'Automático'), ('manual', 'Manual')]
    ESTADOS = [('a_correr', 'A correr'), ('ok', 'Concluído'), ('erro', 'Falhou')]

    tipo       = models.CharField(max_length=12, choices=TIPOS)
    estado     = models.CharField(max_length=10, choices=ESTADOS, default='a_correr')
    chave      = models.CharField(max_length=255, blank=True, default='')   # caminho do ficheiro no armazenamento
    tamanho    = models.BigIntegerField(default=0)                          # bytes
    duracao_s  = models.FloatField(default=0)
    erro       = models.TextField(blank=True, default='')
    pedido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='backups_pedidos')
    criado_em  = models.DateTimeField(auto_now_add=True, db_index=True)
    apagado_em = models.DateTimeField(null=True, blank=True)                # ficheiro removido pela política de retenção
    # ensaio de reposição: o ficheiro foi reposto numa base temporária e conferido (utils/backups.ensaiar_reposicao)
    ensaio_em      = models.DateTimeField(null=True, blank=True)
    ensaio_ok      = models.BooleanField(null=True, blank=True)
    ensaio_detalhe = models.JSONField(default=dict, blank=True, null=True)   # null: o código antigo continua a gravar durante o deploy

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'backup {self.tipo} {self.estado} {self.criado_em:%Y-%m-%d %H:%M}'


class CopiaMedia(models.Model):
    """Uma passagem da cópia incremental das fotos e vídeos para o armazenamento de backups — utils/backup_media.py."""
    TIPOS   = BackupBD.TIPOS
    ESTADOS = BackupBD.ESTADOS

    tipo         = models.CharField(max_length=12, choices=TIPOS)
    estado       = models.CharField(max_length=10, choices=ESTADOS, default='a_correr')
    pedido_por   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='copias_media_pedidas')
    criado_em    = models.DateTimeField(auto_now_add=True, db_index=True)
    duracao_s    = models.FloatField(default=0)
    copiados     = models.IntegerField(default=0)        # ficheiros novos ou alterados copiados nesta passagem
    bytes_copiados = models.BigIntegerField(default=0)
    guardados_apagados = models.IntegerField(default=0)  # apagados nas lojas → passaram para media-apagados/
    purgados     = models.IntegerField(default=0)        # apagados há mais de BACKUP_MEDIA_APAGADOS_DIAS → removidos da cópia
    falhas       = models.IntegerField(default=0)
    ficheiros    = models.IntegerField(default=0)        # na cópia, no fim da passagem
    bytes        = models.BigIntegerField(default=0)
    bytes_apagados = models.BigIntegerField(default=0)   # media-apagados/
    bytes_total  = models.BigIntegerField(default=0)     # tudo o que está no armazenamento de backups (base + exportações + media)
    erro         = models.TextField(blank=True, default='')
    aviso_espaco = models.BooleanField(default=False)    # foi enviado o email de espaço quase cheio

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'cópia media {self.tipo} {self.estado} {self.criado_em:%Y-%m-%d %H:%M}'


class DescargaBackup(models.Model):
    """Quem descarregou um backup e quando: o ficheiro tem os dados pessoais de toda a gente."""
    backup        = models.ForeignKey(BackupBD, on_delete=models.CASCADE, related_name='descargas')
    utilizador    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='backups_descarregados')
    ip            = models.GenericIPAddressField(null=True, blank=True)
    data_criacao  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_criacao']


class ExportacaoLoja(models.Model):
    """
    ZIP com os dados de uma loja (CSV legíveis, não é para repor) — utils/exportacao_loja.py.
    Pedido pelo dono (backoffice) ou pelo admin; gerado pelo worker; o ficheiro vai para o bucket
    privado dos backups e apaga-se ao fim de DIAS_VALIDADE.
    """
    ESTADOS = [('pendente', 'Na fila'), ('a_correr', 'A preparar'), ('ok', 'Pronta'), ('erro', 'Falhou'),
               ('expirada', 'Expirada')]

    loja        = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='exportacoes')
    pedido_por  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='exportacoes_pedidas')
    pelo_admin  = models.BooleanField(default=False)
    com_imagens = models.BooleanField(default=False)
    estado      = models.CharField(max_length=10, choices=ESTADOS, default='pendente', db_index=True)
    chave       = models.CharField(max_length=255, blank=True, default='')
    tamanho     = models.BigIntegerField(default=0)
    erro        = models.TextField(blank=True, default='')
    avisos      = models.TextField(blank=True, default='')       # ficheiros que faltaram, imagens cortadas pelo limite
    criado_em   = models.DateTimeField(auto_now_add=True, db_index=True)
    iniciado_em = models.DateTimeField(null=True, blank=True)
    concluido_em = models.DateTimeField(null=True, blank=True)
    expira_em   = models.DateTimeField(null=True, blank=True)
    descargas   = models.PositiveIntegerField(default=0)
    ultima_descarga_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'exportação loja {self.loja_id} {self.estado} {self.criado_em:%Y-%m-%d %H:%M}'


class ModeracaoUtilizador(models.Model):
    """Histórico de suspensões e bans de uma conta (quem, quando, porquê). Nunca se apaga."""
    ACOES = [
        ('suspender', 'Suspensa'),
        ('banir',     'Banida'),
        ('levantar',  'Reactivada'),
        ('expirou',   'Suspensão terminou'),
    ]
    utilizador = models.ForeignKey(Utilizador, on_delete=models.CASCADE, related_name='moderacoes')
    acao       = models.CharField(max_length=10, choices=ACOES)
    motivo     = models.CharField(max_length=500, blank=True, default='')
    ate        = models.DateTimeField(null=True, blank=True)
    feito_por  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    criado_em  = models.DateTimeField(auto_now_add=True)
    # ban: as lojas e POS do dono que o ban suspendeu e como estavam antes (levantar o ban repõe-nos)
    afetados   = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-criado_em', '-id']
