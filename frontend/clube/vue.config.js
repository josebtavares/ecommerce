const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false,  // ← adicionar esta linha
  // sem .js.map na produção: publicavam o código-fonte inteiro do frontend
  productionSourceMap: false,
})
