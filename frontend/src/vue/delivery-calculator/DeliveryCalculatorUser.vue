<template>
  <main class="user w-100">
    <div class="text col">
      <input type="text" v-model="name" class="form-control no-arrows">
    </div>
    <div class="price col">
      <input type="number" v-model.number="price" class="form-control no-arrows">
      <VueInputCalculator enableKeyboard auto-apply v-model.number="price" class="vue-calculator">
        <i style="background-image: url('data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48IURPQ1RZUEUgc3ZnIFBVQkxJQyAiLS8vVzNDLy9EVEQgU1ZHIDEuMS8vRU4iICJodHRwOi8vd3d3LnczLm9yZy9HcmFwaGljcy9TVkcvMS4xL0RURC9zdmcxMS5kdGQiPjxzdmcgaGVpZ2h0PSczMDBweCcgd2lkdGg9JzMwMHB4JyAgZmlsbD0iIzAwMDAwMCIgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB4PSIwcHgiIHk9IjBweCIgdmlld0JveD0iMCAwIDg0Ljk1MyAxMDAiIGVuYWJsZS1iYWNrZ3JvdW5kPSJuZXcgMCAwIDg0Ljk1MyAxMDAiIHhtbDpzcGFjZT0icHJlc2VydmUiPjxwYXRoIGZpbGw9IiMwMDAwMDAiIGQ9Ik03Mi41NTUsMEwxMi4zOTcsMC4wMzJDNS41NDgsMC4wMzIsMCw1LjU3NCwwLDEyLjQyOXY2My42NzV2MTEuNTA0QzAsOTQuNDUsNS41NDksMTAwLDEyLjM5NywxMDANCglsNjAuMTU4LTAuMDMzYzYuODUxLDAsMTIuMzk3LTUuNTQ5LDEyLjM5Ny0xMi4zOTJWNzYuMTA0VjEyLjM5OEM4NC45NTMsNS41NDgsNzkuNDA2LDAsNzIuNTU1LDB6IE0yMS43MDYsODcuMTU5DQoJYzAsMS43LTEuMzc4LDMuMDg4LTMuMDc3LDMuMDg4aC02Ljk1N2MtMS43LDAtMy4wNzYtMS4zODgtMy4wNzYtMy4wODh2LTMuMDhjMC0xLjY5MywxLjM3NS0zLjA3MywzLjA3Ni0zLjA3M2g2Ljk1Nw0KCWMxLjY5OSwwLDMuMDc3LDEuMzc5LDMuMDc3LDMuMDczVjg3LjE1OXogTTIxLjcwNiw3NC4zNDFjMCwxLjY5MS0xLjM3OCwzLjA4LTMuMDc3LDMuMDhoLTYuOTU3Yy0xLjcsMC0zLjA3Ni0xLjM4LTMuMDc2LTMuMDhWNzEuMjYNCgljMC0xLjcwMSwxLjM3NS0zLjA4MiwzLjA3Ni0zLjA4Mmg2Ljk1N2MxLjY5OSwwLDMuMDc3LDEuMzgsMy4wNzcsMy4wODJWNzQuMzQxeiBNMjEuNzA2LDYxLjUxNGMwLDEuNjkxLTEuMzc4LDMuMDgtMy4wNzcsMy4wOA0KCWgtNi45NTdjLTEuNywwLTMuMDc2LTEuMzgtMy4wNzYtMy4wOHYtMy4wODJjMC0xLjcsMS4zNzUtMy4wNzEsMy4wNzYtMy4wNzFoNi45NTdjMS42OTksMCwzLjA3NywxLjM3MSwzLjA3NywzLjA3MVY2MS41MTR6DQoJIE0yMS43MDYsNDMuNDY3YzAsMS43MDEtMS4zNzgsMy4wODQtMy4wNzcsMy4wODRoLTYuOTU3Yy0xLjcsMC0zLjA3Ni0xLjM3OS0zLjA3Ni0zLjA4NHYtMy4wNzJjMC0xLjcsMS4zNzUtMy4wODEsMy4wNzYtMy4wODENCgloNi45NTdjMS42OTksMCwzLjA3NywxLjM4LDMuMDc3LDMuMDgxVjQzLjQ2N3ogTTM5LjU0NSw4Ny4xNTljMCwxLjctMS4zODQsMy4wODgtMy4wODEsMy4wODhoLTYuOTUNCgljLTEuNzA1LDAtMy4wODItMS4zODgtMy4wODItMy4wODh2LTMuMDhjMC0xLjY5MywxLjM3Ny0zLjA3MywzLjA4Mi0zLjA3M2g2Ljk1YzEuNjk2LDAsMy4wODEsMS4zNzksMy4wODEsMy4wNzNWODcuMTU5eg0KCSBNMzkuNTQ1LDc0LjM0MWMwLDEuNjkxLTEuMzg0LDMuMDgtMy4wODEsMy4wOGgtNi45NWMtMS43MDUsMC0zLjA4Mi0xLjM4LTMuMDgyLTMuMDhWNzEuMjZjMC0xLjcwMSwxLjM3Ny0zLjA4MiwzLjA4Mi0zLjA4Mmg2Ljk1DQoJYzEuNjk2LDAsMy4wODEsMS4zOCwzLjA4MSwzLjA4MlY3NC4zNDF6IE0zOS41NDUsNjEuNTE0YzAsMS42OTEtMS4zODQsMy4wOC0zLjA4MSwzLjA4aC02Ljk1Yy0xLjcwNSwwLTMuMDgyLTEuMzgtMy4wODItMy4wOA0KCXYtMy4wODJjMC0xLjcsMS4zNzctMy4wNzEsMy4wODItMy4wNzFoNi45NWMxLjY5NiwwLDMuMDgxLDEuMzcxLDMuMDgxLDMuMDcxVjYxLjUxNHogTTM5LjU0NSw0My40NjcNCgljMCwxLjcwMS0xLjM4NCwzLjA4NC0zLjA4MSwzLjA4NGgtNi45NWMtMS43MDUsMC0zLjA4Mi0xLjM3OS0zLjA4Mi0zLjA4NHYtMy4wNzJjMC0xLjcsMS4zNzctMy4wODEsMy4wODItMy4wODFoNi45NQ0KCWMxLjY5NiwwLDMuMDgxLDEuMzgsMy4wODEsMy4wODFWNDMuNDY3eiBNNTcuMzc0LDg3LjE1OWMwLDEuNy0xLjM3OSwzLjA4OC0zLjA4LDMuMDg4aC02Ljk0NWMtMS43LDAtMy4wODItMS4zODgtMy4wODItMy4wODh2LTMuMDgNCgljMC0xLjY5MywxLjM3OS0zLjA3MywzLjA4Mi0zLjA3M2g2Ljk0NWMxLjcsMCwzLjA4LDEuMzc5LDMuMDgsMy4wNzNWODcuMTU5eiBNNTcuMzc0LDc0LjM0MWMwLDEuNjkxLTEuMzc5LDMuMDgtMy4wOCwzLjA4aC02Ljk0NQ0KCWMtMS43LDAtMy4wODItMS4zOC0zLjA4Mi0zLjA4VjcxLjI2YzAtMS43MDEsMS4zNzktMy4wODIsMy4wODItMy4wODJoNi45NDVjMS43LDAsMy4wOCwxLjM4LDMuMDgsMy4wODJWNzQuMzQxeiBNNTcuMzc0LDYxLjUxNA0KCWMwLDEuNjkxLTEuMzc5LDMuMDgtMy4wOCwzLjA4aC02Ljk0NWMtMS43LDAtMy4wODItMS4zOC0zLjA4Mi0zLjA4di0zLjA4MmMwLTEuNywxLjM3OS0zLjA3MSwzLjA4Mi0zLjA3MWg2Ljk0NQ0KCWMxLjcsMCwzLjA4LDEuMzcxLDMuMDgsMy4wNzFWNjEuNTE0eiBNNTcuMzc0LDQzLjQ2N2MwLDEuNzAxLTEuMzc5LDMuMDg0LTMuMDgsMy4wODRoLTYuOTQ1Yy0xLjcsMC0zLjA4Mi0xLjM3OS0zLjA4Mi0zLjA4NHYtMy4wNzINCgljMC0xLjcsMS4zNzktMy4wODEsMy4wODItMy4wODFoNi45NDVjMS43LDAsMy4wOCwxLjM4LDMuMDgsMy4wODFWNDMuNDY3eiBNNzUuMjA1LDg3LjE1OWMwLDEuNy0xLjM3OCwzLjA4OC0zLjA3NiwzLjA4OGgtNi45NQ0KCWMtMS43LDAtMy4wODEtMS4zODgtMy4wODEtMy4wODhWNzEuMjZjMC0xLjcwMSwxLjM4MS0zLjA4MiwzLjA4MS0zLjA4Mmg2Ljk1YzEuNjk3LDAsMy4wNzYsMS4zOCwzLjA3NiwzLjA4MlY4Ny4xNTlMNzUuMjA1LDg3LjE1OXoNCgkgTTc1LjIwNSw2MS41MTRjMCwxLjY5MS0xLjM3OCwzLjA4LTMuMDc2LDMuMDhoLTYuOTVjLTEuNywwLTMuMDgxLTEuMzgtMy4wODEtMy4wOHYtMy4wODJjMC0xLjcsMS4zODEtMy4wNzEsMy4wODEtMy4wNzFoNi45NQ0KCWMxLjY5NywwLDMuMDc2LDEuMzcxLDMuMDc2LDMuMDcxVjYxLjUxNEw3NS4yMDUsNjEuNTE0eiBNNzUuMjA1LDQzLjQ2N2MwLDEuNzAxLTEuMzc4LDMuMDg0LTMuMDc2LDMuMDg0aC02Ljk1DQoJYy0xLjcsMC0zLjA4MS0xLjM3OS0zLjA4MS0zLjA4NHYtMy4wNzJjMC0xLjcsMS4zODEtMy4wODEsMy4wODEtMy4wODFoNi45NWMxLjY5NywwLDMuMDc2LDEuMzgsMy4wNzYsMy4wODFWNDMuNDY3TDc1LjIwNSw0My40Njd6DQoJIE03NS4yMDUsMjYuNzk1YzAsMS43MDEtMS4zNzgsMy4wODEtMy4wNzYsMy4wODFIMTEuNjcyYy0xLjcsMC0zLjA3Ni0xLjM3OS0zLjA3Ni0zLjA4MVYxMy4yMDRjMC0xLjcwMiwxLjM3NS0zLjA3NywzLjA3Ni0zLjA3Nw0KCWg2MC40NTdjMS42OTcsMCwzLjA3NiwxLjM3NSwzLjA3NiwzLjA3N1YyNi43OTV6Ij48L3BhdGg+PC9zdmc+');"></i>
      </VueInputCalculator>
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
import VueInputCalculator from "vue-input-calculator";


export default {
  name: "DeliveryCalculatorUser",
  components: {VueInputCalculator},

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
    };
  },
  methods: {
    deleteUser: function () {
      this.$emit("delete-user", this);
    },
    getPrice: function () {
      return this.price;
    }
  },
  watch: {
    price: function () {
      this.$emit("update-price", this);
    }
  },
  computed: {
    totalPrice: function () {
      const discount = this.discount ? this.discount : 0;
      const deliveryCost = this.deliveryCost ? this.deliveryCost : 0;
      // Стоимость заказа с учётом скидки + пропорциональная цена за доставку
      const res = this.price * ((1 - discount / 100) + deliveryCost / this.sumPrice);
      return Math.round(res * 100) / 100;
    }
  }
}
</script>

<style scoped>

</style>