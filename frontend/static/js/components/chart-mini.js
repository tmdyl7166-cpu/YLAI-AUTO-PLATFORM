// stripped module (to be unified later)
void 0;
// Lightweight chart helpers using Canvas API (no external deps)
export function renderLineChart(canvas, series = [], options = {}){
  if(!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const w = (options.width || canvas.clientWidth || 320);
  const h = (options.height || canvas.clientHeight || 160);
  canvas.width = Math.max(1, Math.floor(w * dpr));
  canvas.height = Math.max(1, Math.floor(h * dpr));
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0,0,w,h);
  // background
  ctx.fillStyle = options.bg || '#0d1328';
  ctx.fillRect(0,0,w,h);
  // border
  ctx.strokeStyle = options.border || 'rgba(29,240,255,0.25)';
  ctx.strokeRect(0.5,0.5,w-1,h-1);
  const m = {l:24,r:10,t:10,b:18};
  const xs = series.map((_,i)=>i), ys = series;
  if(ys.length<2){ return; }
  const min = Math.min(...ys), max = Math.max(...ys);
  const xr = xs.length-1 || 1;
  const yr = (max-min) || 1;
  const xw = w - m.l - m.r, yh = h - m.t - m.b;
  ctx.beginPath();
  ctx.lineWidth = 2;
  ctx.strokeStyle = options.color || '#42e695';
  xs.forEach((x,i)=>{
    const px = m.l + (x/xr)*xw;
    const py = m.t + yh - ((ys[i]-min)/yr)*yh;
    if(i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py);
  });
  ctx.stroke();
}

export function renderCandleChart(canvas, candles = [], options = {}){
  // candles: [{t,o,h,l,c}...]
  if(!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const w = (options.width || canvas.clientWidth || 320);
  const h = (options.height || canvas.clientHeight || 160);
  canvas.width = Math.max(1, Math.floor(w * dpr));
  canvas.height = Math.max(1, Math.floor(h * dpr));
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0,0,w,h);
  ctx.fillStyle = options.bg || '#0d1328';
  ctx.fillRect(0,0,w,h);
  ctx.strokeStyle = options.border || 'rgba(29,240,255,0.25)';
  ctx.strokeRect(0.5,0.5,w-1,h-1);
  const m = {l:24,r:10,t:10,b:18};
  const xw = w - m.l - m.r, yh = h - m.t - m.b;
  if(candles.length<1) return;
  const highs = candles.map(c=>c.h), lows = candles.map(c=>c.l);
  const max = Math.max(...highs), min = Math.min(...lows);
  const yr = (max-min) || 1;
  const bw = Math.max(3, Math.floor(xw / Math.max(1,candles.length) * 0.6));
  candles.forEach((c,i)=>{
    const x = m.l + (i/(candles.length-1||1))*xw;
    const yHigh = m.t + yh - ((c.h-min)/yr)*yh;
    const yLow  = m.t + yh - ((c.l-min)/yr)*yh;
    const yOpen = m.t + yh - ((c.o-min)/yr)*yh;
    const yClose= m.t + yh - ((c.c-min)/yr)*yh;
    const up = c.c>=c.o;
    const color = up ? (options.upColor||'#42e695') : (options.downColor||'#ef4444');
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(x, yHigh); ctx.lineTo(x, yLow); ctx.stroke();
    ctx.fillStyle = color;
    const rectY = Math.min(yOpen,yClose);
    const rectH = Math.max(1, Math.abs(yClose-yOpen));
    ctx.fillRect(x - bw/2, rectY, bw, rectH);
  });
}
