// A ficha aberta de um módulo vai no endereço (/admin/<módulo>/<id>, /loja/:id/backoffice/<módulo>/<id>):
// refresh mantém-na aberta, voltar do browser fecha-a e o link pode ser partilhado.
export const COM_FICHA = {
  admin:      ['lojas', 'encomendas', 'devolucoes', 'utilizadores'],
  backoffice: ['encomendas', 'devolucoes'],
}

export function fichaDaRota (route) {
  const f = route.params.ficha
  return /^\d+$/.test(f || '') ? Number(f) : null
}

// id → abre essa ficha; null → fecha (volta à lista do módulo). substituir: sem nova entrada no histórico
export function irParaFicha (router, route, id, substituir = false) {
  const { ficha, ...params } = route.params
  if (String(ficha || '') === String(id ?? '')) return
  router[substituir ? 'replace' : 'push']({ name: route.name, params: id ? { ...params, ficha: String(id) } : params })
}

// Para onde corrigir o endereço do painel (null = já está certo). `valida` é o módulo que fica aberto;
// a ficha só passa se for desse módulo e ele a tiver; ?seccao= e ?reembolso= dos links antigos passam para o caminho.
export function enderecoCerto (route, base, valida, comFicha) {
  if (!valida) return null
  const { seccao, reembolso, ...resto } = route.query
  const pedida = route.params.seccao || seccao
  let ficha = valida === pedida ? String(route.params.ficha || '') : ''
  if (valida === pedida && valida === 'devolucoes' && !ficha && reembolso) ficha = String(reembolso)
  if (!comFicha.includes(valida) || !/^\d+$/.test(ficha)) ficha = ''
  const query = valida !== pedida ? {}
    : (reembolso === undefined || valida === 'devolucoes') ? resto : { ...resto, reembolso }
  const mudou = valida !== route.params.seccao || ficha !== String(route.params.ficha || '')
    || Object.keys(query).length !== Object.keys(route.query).length
  return mudou ? { path: `${base}/${valida}${ficha ? '/' + ficha : ''}`, query } : null
}
