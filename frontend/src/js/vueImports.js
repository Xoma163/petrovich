import Vue from "vue";
import calculator from '../vue/Calculator'


function renderVue(selector, component) {
  const $app = $(selector);
  if ($app.length) {
    new Vue({
      el: selector,
      render: (h) => h(component),
    });
  }
}

$(() => {
  renderVue('#calculator', calculator);
});