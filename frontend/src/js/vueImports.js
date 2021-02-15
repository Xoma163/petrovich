import Vue from "vue";
import calculator from "../vue/calculator/Calculator";
import deliveryCalculator from "../vue/delivery-calculator/DeliveryCalculator";


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
  renderVue("#calculator", calculator);
  renderVue("#delivery-calculator", deliveryCalculator);
});