import '../scss/main.scss';
import 'jquery';
import Vue from "vue";

$(() => {
  new Vue({
    delimiters: ["[[", "]]"],
    el: '#app',
    data: {
      message: 'Hello Vue!'
    }
  })

})
