<template>
  <main class="user w-100">
    <div class="text col">
      <input type="text" v-model="name" class="form-control no-arrows">
    </div>
    <div class="price col">
      <input type="number" v-model.number="price" class="form-control no-arrows">
    </div>
    <div class="totalPrice col">
      <input type="number" disabled v-model.number="totalPrice" class="form-control no-arrows">
    </div>
    <div class="delete text-center vertical-center cursor-pointer btn-danger col" @click="deleteUser">
      <span>x</span>
    </div>
  </main>
</template>

<script>
export default {
  name: "DeliveryCalculatorUser",
  props: {
    id: Number,
    deliveryCost: Number,
    discount: Number,
    sumPrice: Number
  },

  data() {
    return {
      name: "",
      price: 0,
    }
  },
  methods: {
    deleteUser: function () {
      this.$emit('delete-user', this)
    },
    getPrice: function () {
      return this.price
    }
  },
  watch: {
    price: function () {
      this.$emit('update-price', this)
    }
  },
  computed: {
    totalPrice: function () {
      const discount = this.discount ? this.discount : 0
      const deliveryCost = this.deliveryCost ? this.deliveryCost : 0
      // Стоимость заказа с учётом скидки + пропорциональная цена за доставку
      const res = this.price * ((1 - discount / 100) + deliveryCost / this.sumPrice)
      return Math.round(res * 100) / 100;
    }
  }
}
</script>

<style scoped>

</style>