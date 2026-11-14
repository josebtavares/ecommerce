// Depois do build: envia os source maps ao Sentry (erros do site com ficheiro e linha reais) e APAGA-OS do dist,
// para o código-fonte não ficar público. Só corre com SENTRY_AUTH_TOKEN (posto na Railway pelo dono, nunca no git);
// sem ele não faz nada. Se o envio falhar, o deploy segue na mesma (os erros só ficam "comprimidos").
// O "inject" escreve um debug id em cada .js e no seu .map: o Sentry liga-os sem depender da versão.
const fs = require('fs')
const path = require('path')
const { execFileSync } = require('child_process')

const dist = process.env.SENTRY_DIST || path.join(__dirname, '..', 'dist')

function mapas (dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => {
    const p = path.join(dir, e.name)
    return e.isDirectory() ? mapas(p) : (p.endsWith('.map') ? [p] : [])
  })
}

function apagarMapas () {
  const lista = fs.existsSync(dist) ? mapas(dist) : []
  for (const f of lista) fs.unlinkSync(f)
  return lista.length
}

if (!process.env.SENTRY_AUTH_TOKEN) {
  console.log('Sentry: sem SENTRY_AUTH_TOKEN, source maps não enviados')
} else {
  const cli = require.resolve('@sentry/cli/bin/sentry-cli')
  const org = process.env.SENTRY_ORG
  const projeto = process.env.SENTRY_PROJECT
  const versao = process.env.VUE_APP_VERSAO || (process.env.RAILWAY_GIT_COMMIT_SHA || '').slice(0, 12)
  const correr = (args) => execFileSync(process.execPath, [cli, ...args], { stdio: 'inherit', env: process.env })
  try {
    if (!org || !projeto) throw new Error('faltam SENTRY_ORG / SENTRY_PROJECT')
    const js = path.join(dist, 'js')
    correr(['sourcemaps', 'inject', '--quiet', js])
    correr(['sourcemaps', 'upload', '--org', org, '--project', projeto, ...(versao ? ['--release', versao] : []), js])
    console.log('Sentry: source maps enviados')
  } catch (e) {
    console.warn('Sentry: envio dos source maps falhou (o site publica-se na mesma):', e.message)
  }
}
// sempre: nenhum .map vai para o site
console.log(`Sentry: ${apagarMapas()} ficheiros .map apagados do dist`)
