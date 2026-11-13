<template>
  <!-- Devolução pelo correio (reembolso em aguarda_produto) — backend utils/devolucoes.cliente_enviou_produto.
       Cliente: indica a transportadora, o código (opcional) e a foto do talão (opcional); pode corrigir depois.
       Loja / admin: veem a transportadora, os códigos com link e a data do envio. -->
  <section v-if="envio || podeEnviar" class="rounded-2xl border p-4 space-y-3" :class="cartao" data-teste="devolucao-correio">
    <p class="text-xs font-bold uppercase tracking-wider" :class="suave">
      <font-awesome-icon :icon="['fas', 'box']" class="mr-1" />Devolução do produto
    </p>

    <!-- o que já foi indicado -->
    <div v-if="envio && modo !== 'form'" class="space-y-1.5 text-sm" data-teste="devolucao-correio-dados">
      <div class="flex justify-between gap-3">
        <span :class="suave">Enviado por</span>
        <span class="font-semibold text-right">{{ envio.transportadora }}</span>
      </div>
      <div class="flex justify-between gap-3">
        <span :class="suave">Quando</span><span>{{ dataHora(envio.enviada_em) }}</span>
      </div>
      <div class="flex justify-between gap-3">
        <span :class="suave">Código</span>
        <span v-if="!envio.codigos.length" :class="suave" data-teste="devolucao-correio-sem-codigo">sem código de rastreio</span>
        <span v-else class="text-right space-y-0.5">
          <span v-for="c in envio.codigos" :key="c.codigo" class="block font-mono" data-teste="devolucao-correio-codigo">
            {{ c.codigo }}
            <a v-if="c.link" :href="c.link" target="_blank" rel="noopener noreferrer" class="ml-1 text-red-500 hover:text-red-400"
               title="Seguir na transportadora"><font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" class="text-xs" /></a>
          </span>
        </span>
      </div>
      <p v-if="envio.contacto && papel !== 'cliente'" class="text-xs" :class="suave">Contacto da transportadora: {{ envio.contacto }}</p>
      <!-- a loja já vê o prazo junto ao botão "Recebi o produto" -->
      <p v-if="reembolso.estado === 'aguarda_produto' && reembolso.prazo_resposta && papel !== 'loja'" class="text-xs" :class="suave" data-teste="devolucao-correio-prazo">
        {{ papel === 'admin'
              ? `A loja tem até ${dataHora(reembolso.prazo_resposta)} para dizer que recebeu.`
              : `A loja tem até ${dataHora(reembolso.prazo_resposta)} para confirmar que recebeu. Se não confirmar, a equipa da Bendi decide.` }}
      </p>
      <button v-if="podeEnviar" type="button" @click="abrir" data-teste="devolucao-correio-corrigir"
              class="mt-1 text-xs font-semibold text-red-500 hover:text-red-400">
        {{ envio.codigos.length ? 'Corrigir os dados do envio' : 'Juntar o código de rastreio' }}
      </button>
    </div>

    <!-- cliente: ainda não enviou -->
    <div v-else-if="!envio && modo !== 'form'" class="space-y-2">
      <p class="text-sm" :class="texto">Já enviaste o produto pelo correio ou por uma transportadora? Diz aqui por onde — a loja fica a saber e tem 10 dias para confirmar que o recebeu.</p>
      <button type="button" @click="abrir" data-teste="devolucao-correio-abrir"
              class="w-full py-2.5 rounded-xl text-sm font-bold text-white bg-red-600 hover:bg-red-500">
        <font-awesome-icon :icon="['fas', 'truck-fast']" class="mr-1" />Enviei o produto
      </button>
      <p class="text-[11px]" :class="suave">Se entregares em mão na loja, não precisas disto — combina pelas mensagens.</p>
    </div>

    <!-- formulário -->
    <div v-if="modo === 'form'" class="space-y-3" data-teste="devolucao-correio-form">
      <div>
        <label class="text-xs mb-1 block" :class="suave">Transportadora</label>
        <select v-model="form.transportadora" data-teste="devolucao-correio-transportadora" :class="campo">
          <option value="" disabled>Escolhe a transportadora</option>
          <option v-for="t in transportadoras" :key="t.id" :value="String(t.id)">{{ t.nome }}</option>
          <option value="outra">Outra…</option>
        </select>
        <input v-if="form.transportadora === 'outra'" v-model="form.outra" type="text" maxlength="80" placeholder="Nome da transportadora"
               data-teste="devolucao-correio-outra" :class="[campo, 'mt-2']" />
      </div>
      <div>
        <label class="text-xs mb-1 block" :class="suave">Código de rastreio <span class="opacity-70">(opcional — vem no talão)</span></label>
        <div v-for="(c, i) in form.codigos" :key="i" class="flex gap-2 mb-2">
          <input v-model="form.codigos[i]" type="text" maxlength="60" :placeholder="i === 0 ? 'ex.: RR123456789CV' : 'Outro volume'"
                 data-teste="devolucao-correio-codigo-input" autocapitalize="characters" spellcheck="false" :class="[campo, 'font-mono']" />
          <button v-if="form.codigos.length > 1" type="button" @click="form.codigos.splice(i, 1)" aria-label="Tirar código"
                  class="w-9 rounded-lg border" :class="botaoSec">×</button>
        </div>
        <button v-if="form.codigos.length < 10" type="button" @click="form.codigos.push('')"
                class="text-xs text-red-500 hover:text-red-400">+ Outro volume (outro código)</button>
      </div>
      <div>
        <label class="text-xs mb-1 block" :class="suave">Foto do talão <span class="opacity-70">(opcional)</span></label>
        <p v-if="!form.codigos.some(c => c.trim())" class="text-[11px] text-amber-500 mb-1" data-teste="devolucao-correio-dica">
          Sem código, a foto do talão é a tua prova de que enviaste.
        </p>
        <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" data-teste="devolucao-correio-talao"
               @change="form.talao = $event.target.files[0] || null"
               class="block w-full text-xs file:mr-3 file:px-3 file:py-1.5 file:rounded-lg file:border-0"
               :class="isDark ? 'text-zinc-400 file:bg-zinc-800 file:text-zinc-300' : 'text-zinc-600 file:bg-gray-100 file:text-zinc-700'" />
      </div>
      <input v-model="form.nota" type="text" maxlength="300" data-teste="devolucao-correio-nota"
             :placeholder="envio ? 'O que estava errado (opcional)' : 'Nota para a loja (opcional)'" :class="campo" />
      <p v-if="erro" class="text-xs text-red-500" role="alert">{{ erro }}</p>
      <div class="flex gap-2">
        <button type="button" @click="modo = ''" class="flex-1 py-2 rounded-xl text-sm border" :class="botaoSec">Voltar</button>
        <button type="button" @click="submeter" :disabled="aGuardar" data-teste="devolucao-correio-confirmar"
                class="flex-1 py-2 rounded-xl text-sm font-bold text-white bg-red-600 hover:bg-red-500 disabled:opacity-60">
          {{ aGuardar ? 'A enviar…' : (envio ? 'Guardar correção' : 'Avisar a loja') }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { toast } from 'vue3-toastify'
import api from '@/services/api'
import { dataHora } from '@/utils/reembolsos'

const props = defineProps({
  reembolso: { type: Object, required: true },
  papel:     { type: String, default: 'cliente' },     // cliente | loja | admin
  isDark:    { type: Boolean, default: true },
})
const emit = defineEmits(['atualizado'])

const envio = computed(() => props.reembolso.devolucao_envio || null)
const podeEnviar = computed(() => props.papel === 'cliente' && props.reembolso.estado === 'aguarda_produto')

const modo = ref('')
const aGuardar = ref(false)
const erro = ref('')
const transportadoras = ref([])
const form = ref({ transportadora: '', outra: '', codigos: [''], talao: null, nota: '' })

const cartao   = computed(() => props.isDark ? 'bg-zinc-900 border-zinc-800 text-zinc-100' : 'bg-white border-gray-200 text-zinc-900')
const suave    = computed(() => 'text-zinc-500')
const texto    = computed(() => props.isDark ? 'text-zinc-300' : 'text-zinc-700')
const botaoSec = computed(() => props.isDark ? 'border-zinc-700 text-zinc-200 hover:border-zinc-500' : 'border-gray-300 text-zinc-700 hover:border-gray-400')
const campo    = computed(() => ['w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:border-red-500',
  props.isDark ? 'bg-zinc-950 border-zinc-700 text-zinc-100' : 'bg-white border-gray-300 text-zinc-900'])

async function abrir () {
  erro.value = ''
  if (!transportadoras.value.length) {
    try { transportadoras.value = (await api.get('/app/transportadoras/')).data } catch { transportadoras.value = [] }
  }
  const e = envio.value
  form.value = {
    transportadora: e ? (e.transportadora_id ? String(e.transportadora_id) : 'outra') : '',
    outra: e && !e.transportadora_id ? e.transportadora : '',
    codigos: e && e.codigos.length ? e.codigos.map(c => c.codigo) : [''],
    talao: null, nota: '',
  }
  modo.value = 'form'
}

async function submeter () {
  if (aGuardar.value) return
  erro.value = ''
  const f = form.value
  if (!f.transportadora) { erro.value = 'Escolhe a transportadora.'; return }
  if (f.transportadora === 'outra' && !f.outra.trim()) { erro.value = 'Escreve o nome da transportadora.'; return }
  const fd = new FormData()
  fd.append('acao', 'enviei_produto')
  if (f.transportadora === 'outra') fd.append('transportadora_outra', f.outra.trim())
  else fd.append('transportadora_id', f.transportadora)
  fd.append('codigos', JSON.stringify(f.codigos.map(c => c.trim()).filter(Boolean)))
  if (f.nota.trim()) fd.append('nota', f.nota.trim())
  if (f.talao) fd.append('fotos', f.talao)
  aGuardar.value = true
  try {
    const { data } = await api.post(`/app/reembolsos/${props.reembolso.id}/acao/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    toast.success(envio.value ? 'Dados do envio corrigidos — a loja foi avisada.' : 'A loja foi avisada do envio.')
    modo.value = ''
    emit('atualizado', data)
  } catch (e) {
    erro.value = e.response?.data?.detail || 'Não foi possível guardar.'
  } finally { aGuardar.value = false }
}
</script>
