<template>
  <div>
    Продукт {{ product.name }}
  </div>
</template>

<script>
export default {
  name: "CalculatorItem",
  props: {
    product: {
      type: Object,
      default: () => ({}),
    },
  },
}
</script>

<style scoped>

</style>