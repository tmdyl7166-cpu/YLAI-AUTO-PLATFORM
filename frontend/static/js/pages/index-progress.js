// stripped page controller
void 0;
// Attach main progress bar after DOM loaded
(function(){
  document.addEventListener('DOMContentLoaded', function(){
    try{
      const host = document.getElementById('main-progress');
      if(host && window.ProgressBar){
        window.ProgressBar.attach(host, { percent: 0, color: '#42e695', text: '0%' });
      }
    }catch(_){ }
  });
})();
