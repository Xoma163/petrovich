<template>
  <main id="delivery-calculator" class="container">
    <h3>Расчёт заказа за деливери с учётом доставки и скидки</h3>
    <div class="row">
      <div class="col-sm col-12">
        <label for="deliveryCost">Стоимость доставки</label>
        <input type="number" id="deliveryCost" class="form-control no-arrows" v-model.number="deliveryCost">
      </div>
      <div class="col-sm col-12">
        <label for="discount">Процент скидки</label>
        <input type="number" id="discount" class="form-control no-arrows" v-model.number="discount">
      </div>
    </div>
    <div class="row">
      <div class="head w-100">
        <div class="col">
          <div class="text">Имя</div>
        </div>
        <div class="col">
          <div class="price">Сумма заказа</div>
        </div>
        <div class="col">
          <div class="totalPrice">Итог</div>
        </div>
        <div class="col delete">
        </div>
      </div>
      <div class="users w-100" v-for="user in users" :key="user.id">
        <DeliveryCalculatorUser
            :id="user.id"
            :deliveryCost="deliveryCost"
            :discount="discount"
            :sumPrice="sumPrice"
            @delete-user="deleteUser"
            @update-price="updatePrice"
        ></DeliveryCalculatorUser>
      </div>
    </div>

    <div class="buttons flex-end">
      <a class="cursor-pointer btn btn-success"
         @click="addUser"

      >Добавить</a>
    </div>
    <div class="total" v-if="sumPrice!==0">
      <div> Общая сумма заказа - {{ sumPrice }}</div>
      <div v-if="discount !==0"> Общая сумма заказа со скидкой - {{ sumPriceDiscount }}</div>
      <div v-if="deliveryCost!==0"> Общая сумма заказа с доставкой - {{ sumPriceDelivery }}</div>
      <div v-if="deliveryCost!==0 && discount !==0"> Общая сумма заказа со скидкой и с доставкой - {{ sumPriceDiscountDelivery}}</div>
    </div>
  </main>
</template>

<script>
import DeliveryCalculatorUser from "./DeliveryCalculatorUser.vue";

export default {

  name: "DeliveryCalculator",
  components: {
    DeliveryCalculatorUser,
  },
  data() {
    return {
      id: 0,
      users: [],
      deliveryCost: 0,
      discount: 0,
    };
  },
  methods: {
    addUser: function () {
      this.users.push({ id: this.id, price: 0 });
      this.id += 1;
    },
    deleteUser: function (user) {
      for (let i = 0; i < this.users.length; i += 1) {
        if (this.users[i].id === user.id) {
          this.users.splice(i, 1);
          break;
        }
      }
    },
    updatePrice: function (user) {
      for (let i = 0; i < this.users.length; i += 1) {
        if (this.users[i].id === user.id) {
          this.users[i].price = user.price;
          break;
        }
      }
    }

  },
  computed: {
    sumPrice: function () {
      let sum = 0;
      for (let i = 0; i < this.users.length; i++) {
        sum += this.users[i].price;
      }
      return sum;
    },
    sumPriceDiscount: function () {
      return Math.round(this.sumPrice * (100 - this.discount) / 100 * 100) / 100;
    },
    sumPriceDelivery: function () {
      return this.sumPrice + this.deliveryCost;
    },
    sumPriceDiscountDelivery: function () {
      return Math.round((this.sumPrice * (100 - this.discount) / 100 + this.deliveryCost) * 100) / 100;
    },

  },
  watch: {
    discount: function (val) {
      if (val > 100) {
        this.discount = 100;
      }
      if (val < 0) {
        this.discount = 0;
      }
    },
  }
}
</script>

<style scoped>

</style>