<template>
  <main class="calculator-users">
    <div v-for="user in users">
      <CalculatorUser
          :user="user"
          @delete-user="deleteUser"
      ></CalculatorUser>
    </div>
    <div class="flex-end">
      <div class="add-user btn btn-primary" @click="addUser">Добавить</div>
    </div>
  </main>
</template>

<script>
import CalculatorUser from "./CalculatorUser.vue";
import axios from "axios";

export default {
  name: "CalculatorUsers",
  components: {
    CalculatorUser,
  },
  methods: {
    addUser: function () {
      const data = {
        name: "",
        calculatorsession: this.sessionId,
      }
      axios.post("/calculator_session/api/calculator_user/", data)
          .then((response) => {
            this.users.push(response.data);
          });
    },
    deleteUser: function (user) {
      this.$emit("delete-user", user);
    },
  },
  props: {
    users: {
      type: Array,
    },
    sessionId: {
      type: Number
    }
  },
}
</script>

<style scoped>

</style>