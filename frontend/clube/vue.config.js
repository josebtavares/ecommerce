const { defineConfig } = require('@vue/cli-service')
// versão do site para o Sentry (utils/sentry.js): o commit do deploy na Railway
process.env.VUE_APP_VERSAO = process.env.VUE_APP_VERSAO || (process.env.RAILWAY_GIT_COMMIT_SHA || '').slice(0, 12)
module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false,  // ← adicionar esta linha
  // sem .js.map na produção: publicavam o código-fonte inteiro do frontend
  productionSourceMap: false,
})
