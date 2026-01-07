// Phone analysis module entry
import PhonePanel from './components/PhonePanel.vue';

export default {
  name: 'phone-analysis',
  component: PhonePanel,
  routes: [
    { path: '/phone', component: PhonePanel }
  ]
};