<template>
  <div class="mb-2 calculator-product">
    <div class="name">
      <input type="text" class="form-control" v-model="product.name">
    </div>
    <div class="count">
      <input type="number" class="form-control no-arrows" v-model="product.count">
    </div>
    <div class="uom">
      <select v-model="product.uom" class="form-control">
        <option selected value="null">---</option>
        <template v-for="uom in uomList">
          <option :value="uom.value">{{ uom.label }}</option>
        </template>
      </select>
    </div>
    <div class="is-bought vertical-center">
      <input type="checkbox" v-model="product.is_bought" class="form-control">
    </div>
    <div class="user">
      <select v-model="product.bought_by.id" class="form-control">
        <option selected value="null">---</option>
        <template v-for="user in users">
          <option :value="user.id">{{ user.name }}</option>
        </template>
      </select>
    </div>
    <div class="price">
      <input type="number" v-model="product.price" class="form-control no-arrows">
    </div>
    <div class="delete text-center vertical-center">x</div>
  </div>
</template>

<script>
export default {
  name: "CalculatorItem",
  props: {
    product: {
      type: Object,
    },
    uomList: {
      type: Array,

    },
    users: {
      type: Object,
    }
  },
  watch: {
    product: {
      handler(val) {
        val.bought_by.name = this.users[val.bought_by.id].name;
      },
      deep: true,
    }
  }
}
</script>

<style scoped>

</style>