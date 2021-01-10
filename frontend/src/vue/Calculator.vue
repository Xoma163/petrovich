<template>
  <main class="container-fluid" id="calculator" v-if="session">
    <h1>{{ session.name }}</h1>
    <div class="item">
      <CalculatorProduct
          v-for="product in session.products"
          :key="product.id"
          :product="product"
          :uomList="session.uom_list"
          :users="session.users"
          @delete-product="deleteProduct"
      >
      </CalculatorProduct>
    </div>
    <a v-on:click="addProduct" class="cursor-pointer">Добавить</a>
    <a v-on:click="calculate" class="cursor-pointer">Расчитать</a>
    <div class="result" data-fancybox style="display:none">
      <div v-for="transaction in result.transactions">
        <span>{{ transaction.from }}</span>
        <span>&#9;&#9;→&#9;&#9;</span>
        <span>{{ transaction.to }}</span>
        <span>&#9;<b>{{ transaction.money }}</b></span>
        <span>&#9;{{ result.currency }}.</span>
      </div>
      <div></div>
      <div>Общий чек: <b>{{ result.total_money }}</b> {{ result.currency }}.</div>
      <div>Средний чек: <b>{{ result.avg_money }}</b> {{ result.currency }}.</div>
    </div>
  </main>
</template>


<script>
import CalculatorProduct from './CalculatorProduct.vue';
import axios from "axios";
import 'notifyjs-browser';

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
      result: "",
    }
  },

  methods: {
    addProduct: function () {
      const data = {
        name: "",
        count: 0,
        price: 0,
        calculatorsession: this.session.id,
      }
      axios.defaults.xsrfCookieName = 'csrftoken';
      axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
      axios.post("/calculator_session/api/calculator_product/", data)
          .then(response => {
            this.session.products.push(response.data)
          });
    },
    deleteProduct: function (product) {
      for (let i = 0; i < this.session.products.length; i += 1) {
        if (this.session.products[i].id === product.product.id) {
          this.session.products.splice(i, 1);
          break;
        }
      }
    },
    calculate: function () {
      const users = $('.user select');
      for (let i = 0; i < users.length; i += 1) {
        if (!users[i].value) {
          $.notify("Заполните всех людей, которые покупали продукты", "warn");
          return;
        }
      }

      const sessionId = window.location.pathname.split("/").slice(-1)[0];
      axios.get(`/calculator_session/api/calculator_session/${sessionId}/calculate/`)
          .then(response => {
            this.result = response.data.data
            $.fancybox.open($('.result'));
          })
    }
  },
  mounted() {
    const sessionId = window.location.pathname.split("/").slice(-1)[0];
    axios.get(`/calculator_session/api/calculator_session/${sessionId}/`)
        .then(response => {
          this.session = response.data
        })
  },
}
</script>

<style scoped>

</style>
