<template>
  <main class="container" v-if="session">
    <h1>{{ session.name }}</h1>
    Компонент

    <CalculatorProduct
        v-for="product in session.products"
        :key="product.id"
        :product="product"
    >

    </CalculatorProduct>
  </main>
</template>


<script>
import CalculatorProduct from './CalculatorProduct.vue';

export default {
  name: "Calculator",
  components: {
    CalculatorProduct,
  },
  props: {},
  data() {
    return {
      'session': undefined,
    }
  },

  methods: {},
  mounted() {
    const $elem = $('#calculator-data');
    this.session = $elem.data('session');

  },
}
</script>

<style scoped>

</style>
