// stripped page controller
void 0;
(function(){
  if (!window.ProgressBar) {
    console.warn('ProgressBar not found; skipping api-doc-progress attach');
    return;
  }
  function init(){
    var el = document.getElementById('api-progress');
    if (!el) return;
    try {
      window.ProgressBar.attach(el, { percent: 75, color: '#667eea', text: '75%' });
    } catch (e) {
      console.warn('ProgressBar.attach error:', e);
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
