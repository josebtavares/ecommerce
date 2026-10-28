<template>
  <ol class="space-y-0">
    <li v-for="(p, i) in passos" :key="p.chave" class="flex gap-3">
      <div class="flex flex-col items-center">
        <span class="h-6 w-6 rounded-full flex items-center justify-center text-[10px] flex-shrink-0"
              :class="{
                'bg-green-500 text-white': p.estado === 'feito',
                'bg-red-500 text-white': p.estado === 'falhou',
                'bg-amber-500 text-white animate-pulse': p.estado === 'atual',
                [isDark ? 'bg-zinc-800 text-zinc-500' : 'bg-gray-200 text-zinc-400']: p.estado === 'futuro',
              }">
          <font-awesome-icon :icon="['fas', p.estado === 'feito' ? 'check' : p.estado === 'falhou' ? 'xmark' : p.estado === 'atual' ? 'clock' : 'circle']"
                             :class="p.estado === 'futuro' ? 'text-[6px]' : ''" />
        </span>
        <span v-if="i < passos.length - 1" class="w-px flex-1 min-h-[16px]"
              :class="p.estado === 'feito' ? 'bg-green-500/50' : (isDark ? 'bg-zinc-800' : 'bg-gray-200')"></span>
      </div>
      <div class="pb-4 min-w-0">
        <p class="text-sm font-semibold" :class="p.estado === 'futuro' ? (isDark ? 'text-zinc-500' : 'text-zinc-400') : (isDark ? 'text-zinc-100' : 'text-zinc-800')">
          {{ p.titulo }}
        </p>
        <p v-if="p.texto" class="text-xs" :class="isDark ? 'text-zinc-500' : 'text-zinc-500'">{{ p.texto }}</p>
      </div>
    </li>
  </ol>
</template>

<script setup>
import { computed } from 'vue'
import { formatarDinheiro } from '@/utils/dinheiro'
import { dataHora } from '@/utils/reembolsos'

const props = defineProps({
  reembolso: { type: Object, required: true },
  isDark:    { type: Boolean, default: true },
  papel:     { type: String, default: 'cliente' },   // os textos mudam para a loja e a Bendi
})

// passos a partir do estado e das datas do pedido
const passos = computed(() => {
  const r = props.reembolso
  const cliente = props.papel === 'cliente'
  const out = [{ chave: 'pedido', titulo: r.origem !== 'cliente' ? 'Reembolso automático' : (cliente ? 'Pedido enviado' : 'Pedido do cliente'),
                 texto: dataHora(r.data_criacao), estado: 'feito' }]
  if (r.origem === 'cliente') {
    const quando = dataHora(r.data_resposta_loja)
    const loja = {
      aceite:       { titulo: 'A loja aceitou', estado: 'feito', texto: quando },
      recusado:     { titulo: 'A loja recusou', estado: 'falhou', texto: quando },
      sem_resposta: { titulo: 'A loja não respondeu a tempo', estado: 'falhou', texto: '' },
      proposta:     r.estado === 'proposta'
        ? { titulo: `A loja propôs ${formatarDinheiro(r.valor_aprovado)}`, estado: 'atual',
            texto: cliente ? 'Aceita a proposta ou pede ajuda à Bendi.' : 'À espera da resposta do cliente.' }
        : { titulo: 'A loja propôs outro valor', estado: 'feito', texto: quando },
    }[r.resposta_loja] || (r.estado === 'pedido'
      ? { titulo: 'Resposta da loja', estado: 'atual', texto: r.prazo_resposta ? `A loja tem até ${dataHora(r.prazo_resposta)}` : '' }
      : { titulo: 'Resposta da loja', estado: 'futuro', texto: '' })
    out.push({ chave: 'loja', ...loja })
  }
  // disputa sobre a entrega do dinheiro (depois de acertado o valor): aparece mais abaixo, no sítio dela
  const disputaDepois = r.escalado_em && r.data_reembolso && new Date(r.escalado_em) >= new Date(r.data_reembolso)
  if (r.escalado_em && !disputaDepois) {
    const decidiu = r.decisao_admin
    out.push({ chave: 'bendi', titulo: decidiu ? 'A Bendi decidiu' : 'Em análise pela Bendi',
               texto: decidiu ? dataHora(r.data_decisao) : `Desde ${dataHora(r.escalado_em)}`,
               estado: decidiu ? (r.estado === 'recusado' ? 'falhou' : 'feito') : (r.estado === 'em_disputa' ? 'atual' : 'futuro') })
  }
  if (r.devolver_produto) {
    out.push({ chave: 'produto', titulo: r.produto_recebido_em ? 'A loja recebeu o produto'
                                        : (cliente ? 'Devolver o produto à loja' : 'O cliente devolve o produto'),
               texto: r.produto_recebido_em ? dataHora(r.produto_recebido_em) : '',
               estado: r.produto_recebido_em ? 'feito' : (r.estado === 'aguarda_produto' ? 'atual' : 'futuro') })
  }
  // dinheiro em mão: aceite → a loja entrega → o cliente confirma
  if (r.metodo === 'manual' && r.data_reembolso) {
    out.push({ chave: 'aceite', estado: 'feito', titulo: `Reembolso aceite: ${formatarDinheiro(r.valor_aprovado)} em mão`, texto: dataHora(r.data_reembolso) })
    out.push({ chave: 'entregue', titulo: r.entregue_em ? 'A loja entregou o dinheiro' : 'A loja entrega o dinheiro',
               texto: r.entregue_em ? dataHora(r.entregue_em) : (r.estado === 'a_devolver' ? `Até ${dataHora(r.prazo_resposta)}` : ''),
               estado: r.entregue_em ? 'feito' : (r.estado === 'a_devolver' ? 'atual' : 'futuro') })
    if (r.nao_recebido_em) {
      out.push({ chave: 'nao', estado: 'falhou', titulo: cliente ? 'Disseste que não recebeste' : 'O cliente diz que não recebeu', texto: dataHora(r.nao_recebido_em) })
    } else if (disputaDepois) {
      out.push({ chave: 'nao', estado: 'falhou', titulo: 'A loja não indicou a entrega a tempo', texto: dataHora(r.escalado_em) })
    }
    if (r.estado === 'em_disputa') {
      out.push({ chave: 'bendi', estado: 'atual', titulo: 'A Bendi está a verificar', texto: '' })
    }
    out.push({ chave: 'fim', titulo: r.recebido_auto ? 'Dado como recebido' : 'Dinheiro recebido',
               texto: dataHora(r.recebido_em),
               estado: r.recebido_em ? 'feito' : (r.estado === 'a_devolver' && r.entregue_em ? 'atual' : 'futuro') })
    return out
  }
  if (r.data_reembolso && r.nao_recebido_em) {           // gateway: "não recebi" depois de reembolsado
    out.push({ chave: 'reemb', estado: 'feito', titulo: `Reembolsado ${formatarDinheiro(r.valor_aprovado)}`, texto: dataHora(r.data_reembolso) })
    out.push({ chave: 'nao', estado: r.estado === 'reembolsado' ? 'feito' : 'atual',
               titulo: r.estado === 'reembolsado' ? 'Confirmado pela Bendi' : 'A Bendi está a verificar a devolução',
               texto: dataHora(r.nao_recebido_em) })
    return out
  }
  if (r.estado === 'por_reembolsar') {               // aceite, mas o pagamento online ainda não devolveu
    out.push({ chave: 'aceite', estado: 'feito', titulo: `Reembolso aceite: ${formatarDinheiro(r.valor_aprovado)}`, texto: dataHora(r.data_decisao) })
    out.push({ chave: 'fim', estado: 'atual', titulo: 'A processar a devolução',
               texto: cliente ? 'Houve um atraso — estamos a tratar disso.' : 'O pagamento online recusou — vamos tentar de novo.' })
    return out
  }
  if (r.estado === 'reembolsado') {
    out.push({ chave: 'fim', estado: 'feito', texto: dataHora(r.data_reembolso),
               titulo: Number(r.valor_aprovado) > 0 ? `Reembolsado ${formatarDinheiro(r.valor_aprovado)}` : 'Encomenda cancelada' })
  } else if (r.estado === 'recusado') {
    out.push({ chave: 'fim', estado: 'falhou', titulo: 'Pedido recusado', texto: '' })
  } else if (r.estado === 'cancelado') {
    out.push({ chave: 'fim', estado: 'falhou', titulo: cliente ? 'Desististe do pedido' : 'O cliente desistiu', texto: dataHora(r.data_atualizacao) })
  } else {
    out.push({ chave: 'fim', estado: 'futuro', titulo: 'Reembolso', texto: '' })
  }
  return out
})
</script>
