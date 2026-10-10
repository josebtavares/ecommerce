// Atributos de produto podem vir como valor simples ("médio") ou lista (["médio", "sem picante"]).
// Devolve um objecto { chave: "texto legível" } sem valores vazios, opcionalmente limitado.
export function formatarAtributos (atributos, limite = Infinity) {
  return Object.fromEntries(
    Object.entries(atributos || {})
      .map(([k, v]) => [k, Array.isArray(v)
        ? v.filter(x => x !== null && x !== undefined && String(x).trim()).join(', ')
        : v])
      .filter(([, v]) => v !== null && v !== undefined && String(v).trim() !== '')
      .slice(0, limite)
  )
}

export function temAtributos (atributos) {
  return Object.keys(formatarAtributos(atributos)).length > 0
}
