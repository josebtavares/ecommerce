from django.urls import path
from ..Views import faturacaoLojaView as v
from ..Views import arquivoFiscalView as af

# aba Faturação do backoffice da loja (ver app/Views/faturacaoLojaView.py)
L = 'loja/<int:loja_id>/faturacao/'
urlpatterns = [
    path(L + 'resumo/',                        v.resumo,       name='loja-faturacao-resumo'),
    path(L + 'vendas/',                        v.vendas,       name='loja-faturacao-vendas'),
    path(L + 'vendas.csv',                     v.vendas_csv,   name='loja-faturacao-csv'),
    path(L + 'exportar/',                      v.exportar,     name='loja-faturacao-exportar'),
    path(L + 'arquivos/',                      af.loja_arquivos, name='loja-faturacao-arquivos'),
    path(L + 'arquivos/<int:aid>/descarregar/', af.loja_arquivo_descarregar, name='loja-faturacao-arquivo-descarregar'),
    path(L + 'pesquisa/',                      v.pesquisa,     name='loja-faturacao-pesquisa'),
    path(L + 'historico/',                     v.historico,    name='loja-faturacao-historico'),
    path(L + 'contas/<int:conta_id>/fatura/',  v.conta_fatura, name='loja-faturacao-conta'),
]
