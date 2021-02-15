<template>
  <div class="mb-2 calculator-product">
    <div class="is-bought vertical-center">
      <input type="checkbox" v-model="product.is_bought" class="form-control no-focus no-select">
    </div>
    <div class="name">
      <input type="text" class="form-control" v-model="product.name">
    </div>
    <div class="count">
      <input type="number" class="form-control no-arrows" v-model="product.count">
    </div>
    <div class="uom">
      <select v-model="product.uom" class="form-control">
        <option selected :value="null">---</option>
        <template v-for="uom in uomList">
          <option :value="uom.value">{{ uom.label }}</option>
        </template>
      </select>
    </div>
    <div class="price">
      <input type="number" v-model="product.price" class="form-control no-arrows">
    </div>
    <div class="user">
      <select v-model="product.bought_by" class="form-control">
        <option selected :value="null">---</option>
        <template v-for="user in users">
          <option :value="user.id">{{ user.name }}</option>
        </template>
      </select>
    </div>
    <div class="delete text-center vertical-center cursor-pointer btn-danger" @click="deleteProduct"><span>x</span>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "CalculatorProduct",
  props: {
    product: {
      type: Object,
    },
    uomList: {
      type: Array,

    },
    users: {
      type: Array,
    }
  },

  methods: {
    deleteProduct: function () {
      axios.delete(`/calculator_session/api/calculator_product/${this.product.id}/`);
      this.$emit("delete-product", this);
    }
  },
  watch: {
    product: {
      handler(val) {
        axios.put(`/calculator_session/api/calculator_product/${this.product.id}/`, this.product)
      },
      deep: true,
    }
  }
}
</script>

<style scoped>

</style>