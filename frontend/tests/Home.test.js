import Home from '../static/js/components/Home.vue';

test('Home component exists', () => {
  expect(Home).toBeDefined();
  expect(Home.name).toBe('Home');
});