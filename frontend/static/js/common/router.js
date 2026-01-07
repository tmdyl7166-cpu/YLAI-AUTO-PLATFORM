// Page script router: auto-load /static/js/pages/<name>.js based on location
(function(){
  const m = location.pathname.match(/\/pages\/(.+?)\.html$/);
  const name = m ? m[1] : 'index';
  const url = `/static/js/pages/${name}.js?v=${document.querySelector('link[rel="modulepreload"]')?.href.split('v=')[1]||'dev'}`;
  import(url).catch(err=>console.warn('[router] failed to load page script', name, err));
})();
