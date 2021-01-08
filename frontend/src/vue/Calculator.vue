<template>
  <main class="container-fluid" id="calculator" v-if="session">
    <h1>{{ session.name }}</h1>
    <div class="item">
      <CalculatorProduct
          v-for="product in session.products"
          :key="product.id"
          :product="product"
          :uomList="uomList"
          :users="session.users"
      >
      </CalculatorProduct>
    </div>
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
      session: undefined,
      uomList: undefined,
    }
  },

  methods: {},
  mounted() {
    const $elem = $('#calculator-data');
    this.session = $elem.data('session');

    this.uomList = $elem.data('uom-list');
  },
}
</script>

<style scoped>

</style>
