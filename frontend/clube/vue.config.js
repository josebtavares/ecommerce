const { defineConfig } = require('@vue/cli-service')
// versão do site para o Sentry (utils/sentry.js): o commit do deploy na Railway
process.env.VUE_APP_VERSAO = process.env.VUE_APP_VERSAO || (process.env.RAILWAY_GIT_COMMIT_SHA || '').slice(0, 12)
module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false,  // prod: sem ESLint no build
  // .js.map só para o Sentry (scripts/sentry-mapas.js envia-os e apaga-os do dist antes de publicar); "hidden": os .js
  // não apontam para eles. Sem SENTRY_AUTH_TOKEN não se geram (publicavam o código-fonte inteiro do frontend)
  productionSourceMap: !!process.env.SENTRY_AUTH_TOKEN,
  chainWebpack: (config) => {
    if (process.env.NODE_ENV === 'production' && process.env.SENTRY_AUTH_TOKEN) config.devtool('hidden-source-map')
  },
  css: { sourceMap: false },
})
