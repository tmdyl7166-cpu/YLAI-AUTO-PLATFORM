// Demo module entry
import DemoPanel from './components/DemoPanel.vue';

export default {
  name: 'module-demo',
  component: DemoPanel,
  routes: [
    { path: '/demo', component: DemoPanel }
  ]
};