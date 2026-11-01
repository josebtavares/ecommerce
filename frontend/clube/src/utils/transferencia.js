// Transferências por confirmar: a encomenda cancela-se sozinha no fim do prazo (backend utils/encomendas.py,
// PRAZO_TRANSFERENCIA_H). → "dia 04/11 às 12:00" na hora do browser.
export function formatarPrazo (iso) {
  const d = new Date(iso)
  const p = n => String(n).padStart(2, '0')
  return `dia ${p(d.getDate())}/${p(d.getMonth() + 1)} às ${p(d.getHours())}:${p(d.getMinutes())}`
}
