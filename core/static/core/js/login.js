const waveform = document.getElementById('waveform');
const barCount = 56;
for (let i = 0; i < barCount; i++) {
  const bar = document.createElement('div');
  bar.className = 'bar';
  const hMin = (0.15 + Math.random() * 0.25).toFixed(2);
  const hMax = (0.55 + Math.random() * 0.45).toFixed(2);
  const dur = (1.6 + Math.random() * 1.8).toFixed(2);
  const delay = (Math.random() * 2).toFixed(2);
  bar.style.setProperty('--h-min', hMin);
  bar.style.setProperty('--h-max', hMax);
  bar.style.animationDuration = dur + 's';
  bar.style.animationDelay = delay + 's';
  waveform.appendChild(bar);
}
const ticks = document.getElementById('ticks');
for (let i = 0; i < 70; i++) {
  const t = document.createElement('span');
  t.style.height = (i % 5 === 0 ? 22 : 10) + 'px';
  ticks.appendChild(t);
}
document.getElementById('togglePass').addEventListener('click', function () {
  const pass = document.getElementById('password');
  const isPass = pass.type === 'password';
  pass.type = isPass ? 'text' : 'password';
  this.textContent = isPass ? 'hide' : 'show';
});