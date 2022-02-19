<template>
  <main v-if="session" id="calculator" class="container-fluid">
    <h3>{{ session.name }}</h3>
    <div v-if="session.products.length>0" class="calculator-product header">
      <div class="is-bought vertical-center"></div>
      <div class="name">Название</div>
      <div class="count">Кол-во</div>
      <div class="uom">Ед. изм.</div>
      <div class="price">Цена</div>
      <div class="user">Кем куплено</div>
      <div class="delete"></div>
    </div>

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
    <div class="buttons flex-end">
      <a class="cursor-pointer btn btn-secondary" @click="users">Пользователи</a>
      <a class="cursor-pointer btn btn-success" @click="addProduct">Добавить</a>
      <a class="cursor-pointer btn btn-primary" @click="calculate">Рассчитать</a>
    </div>
    <div class="result fancybox">
      <div v-for="transaction in result.transactions">
        <span>{{ transaction.from }}</span>
        <span class="strelochka">&#9;&#9;→&#9;&#9;</span>
        <span>{{ transaction.to }}</span>
        <span>&#9;<b>{{ transaction.money }}</b></span>
        <span>&#9;{{ result.currency }}.</span>
      </div>
      <br>
      <div>Общий чек: <b>{{ result.total_money }}</b> {{ result.currency }}.</div>
      <div>Средний чек: <b>{{ result.avg_money }}</b> {{ result.currency }}.</div>
    </div>
    <div class="users fancybox">
      <CalculatorUsers
          :sessionId="session.id"
          :users="session.users"
          @delete-user="deleteUser"
      ></CalculatorUsers>
    </div>
  </main>
</template>


<script>
import CalculatorUsers from "./CalculatorUsers.vue";
import CalculatorProduct from "./CalculatorProduct.vue";
import axios from "axios";
import "notifyjs-browser";

export default {
  name: "Calculator",
  components: {
    CalculatorProduct,
    CalculatorUsers,
  },
  data() {
    return {
      session: null,
      result: "",
    };
  },

  methods: {
    users() {
      $.fancybox.open($(".users"), {touch: false});
    },

    addProduct() {
      const data = {
        name: "",
        count: 0,
        price: 0,
        calculatorsession: this.session.id,
      };
      axios.post("/calculator_session/api/calculator_product/", data)
          .then((response) => {
            this.session.products.push(response.data);
          });
    },
    deleteUser(user) {
      for (let i = 0; i < this.session.users.length; i += 1) {
        if (this.session.users[i].id === user.id) {
          this.session.users.splice(i, 1);
          break;
        }
      }
      for (let i = 0; i < this.session.products.length; i += 1) {
        if (this.session.products[i].bought_by === user.id) {
          this.session.products[i].bought_by = null;
        }
      }
    },
    deleteProduct(product) {
      for (let i = 0; i < this.session.products.length; i += 1) {
        if (this.session.products[i].id === product.product.id) {
          this.session.products.splice(i, 1);
          break;
        }
      }
    },
    calculate() {
      const users = $(".user select");
      for (let i = 0; i < users.length; i += 1) {
        if (!users[i].value) {
          $.notify("Заполните всех людей, которые покупали продукты", "warn");
          return;
        }
      }

      const sessionId = window.location.pathname.split("/").slice(-1)[0];
      axios.get(`/calculator_session/api/calculator_session/${sessionId}/calculate/`)
          .then((response) => {
            this.result = response.data.data;
            $.fancybox.open($(".result"), {touch: false});
          });
    }
  },
  mounted() {
    const sessionId = window.location.pathname.split("/").slice(-1)[0];
    axios.get(`/calculator_session/api/calculator_session/${sessionId}/`)
        .then((response) => {
          this.session = response.data;
        });
  },
};
</script>

<style scoped>

</style>
