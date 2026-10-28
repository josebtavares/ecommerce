// Páginas institucionais (Ajuda, Contacto, FAQ, Termos, …) e dados do rodapé.
import api from '@/services/api'

/** Converte o texto livre em blocos: "## Título", linhas "- item" e parágrafos. */
export function parseConteudo (texto) {
  const blocos = []
  String(texto || '').replace(/\r\n/g, '\n').split(/\n{2,}/).forEach(par => {
    const linhas = par.split('\n').map(l => l.trimEnd()).filter(l => l.trim())
    if (!linhas.length) return
    let paragrafo = []
    const fecharParagrafo = () => {
      if (paragrafo.length) blocos.push({ tipo: 'paragrafo', texto: paragrafo.join('\n') })
      paragrafo = []
    }
    linhas.forEach(l => {
      const t = l.trim()
      if (/^#{1,3}\s+/.test(t)) {
        fecharParagrafo()
        blocos.push({ tipo: 'titulo', texto: t.replace(/^#{1,3}\s+/, '') })
      } else if (/^[-*•]\s+/.test(t)) {
        fecharParagrafo()
        const item = t.replace(/^[-*•]\s+/, '')
        const ultimo = blocos[blocos.length - 1]
        if (ultimo?.tipo === 'lista') ultimo.itens.push(item)
        else blocos.push({ tipo: 'lista', itens: [item] })
      } else {
        paragrafo.push(t)
      }
    })
    fecharParagrafo()
  })
  return blocos
}

/** { email, telefone, whatsapp, morada, horario } → lista para mostrar, com links (vazios saem). */
export function listaContactos (d) {
  d = d || {}
  const so = v => String(v || '').replace(/[^\d+]/g, '')
  return [
    d.email    && { chave: 'email',    icone: 'envelope',     label: 'Email',    valor: d.email,    href: `mailto:${d.email}` },
    d.telefone && { chave: 'telefone', icone: 'phone',        label: 'Telefone', valor: d.telefone, href: `tel:${so(d.telefone)}` },
    d.whatsapp && { chave: 'whatsapp', icone: 'comment-dots', label: 'WhatsApp', valor: d.whatsapp, href: `https://wa.me/${so(d.whatsapp).replace('+', '')}`, externo: true },
    d.morada   && { chave: 'morada',   icone: 'location-dot', label: 'Morada',   valor: d.morada,   href: `https://maps.google.com/?q=${encodeURIComponent(d.morada)}`, externo: true },
    d.horario  && { chave: 'horario',  icone: 'clock',        label: 'Horário',  valor: d.horario },
  ].filter(Boolean)
}

// titular, contactos e páginas activas — um pedido por visita, partilhado por todos os rodapés
let pedido = null
export function dadosPlataforma () {
  if (!pedido) {
    pedido = api.get('/app/plataforma/publica/').then(r => r.data).catch(() => { pedido = null; return null })
  }
  return pedido
}
