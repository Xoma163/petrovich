<template>
  <main class="mb-2 calculator-user">
    <input class="form-control" v-model="user.name">
    <div class="delete text-center vertical-center cursor-pointer btn-danger" @click="deleteUser">
      <span>x</span>
    </div>
  </main>
</template>
<script>
import axios from "axios"

export default {
  name: "CalculatorUser",
  props: {
    user: {
      type: Object,
    }
  },
  methods: {
    deleteUser: function () {
      axios.delete(`/calculator_session/api/calculator_user/${this.user.id}/`);
      this.$emit("delete-user",this.user)
    }
  },
  watch: {
    user: {
      handler(val) {
        axios.put(`/calculator_session/api/calculator_user/${this.user.id}/`, this.user)
      },
      deep: true,
    }
  },
}
</script>


<style scoped>

</style>