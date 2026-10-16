const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  // sem .js.map na produção: publicavam o código-fonte inteiro do frontend
  productionSourceMap: false,
})
