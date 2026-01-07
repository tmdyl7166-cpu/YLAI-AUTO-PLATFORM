// stripped module (to be unified later)
void 0;
// 通用 Toast 组件
export function showToast(msg, type = 'info', duration = 2200) {
  let toast = document.createElement('div');
  toast.className = 'yl-toast yl-toast-' + type;
  toast.textContent = msg;
  Object.assign(toast.style, {
    position: 'fixed', left: '50%', top: '16px', transform: 'translateX(-50%)',
    background: type === 'error' ? '#ff7b7b' : (type === 'success' ? '#42e695' : '#2563eb'),
    color: '#fff', padding: '8px 18px', borderRadius: '8px', fontSize: '15px', zIndex: 9999,
    boxShadow: '0 2px 12px #0002', opacity: 0.96, pointerEvents: 'none',
  });
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.opacity = 0.2; }, duration - 400);
  setTimeout(() => { toast.remove(); }, duration);
}
