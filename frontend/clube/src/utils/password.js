// Regras de password forte — as mesmas validadas no backend (app/utils/password.py)
export function regrasPassword (p = '') {
  return [
    { key: 'length',  label: 'Mínimo 8 caracteres',     valid: p.length >= 8 },
    { key: 'upper',   label: 'Letra maiúscula',          valid: /[A-Z]/.test(p) },
    { key: 'lower',   label: 'Letra minúscula',          valid: /[a-z]/.test(p) },
    { key: 'number',  label: 'Um número',                valid: /[0-9]/.test(p) },
    { key: 'special', label: 'Símbolo especial (!@#$…)', valid: /[^A-Za-z0-9]/.test(p) },
  ]
}

export function passwordValida (p = '') {
  return regrasPassword(p).every(r => r.valid)
}
