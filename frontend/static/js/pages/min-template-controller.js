import { runNLP } from '../core/logic.js';
import { register } from '../core/registry.js';

async function onRun() {
  const input = document.querySelector('#prompt');
  const output = document.querySelector('#output');
  const btn = document.querySelector('#runBtn');
  btn.disabled = true;
  output.textContent = 'Running...';
  try {
    const text = await runNLP(input.value);
    output.textContent = text;
  } catch (e) {
    output.textContent = String(e);
  } finally {
    btn.disabled = false;
  }
}

function init() {
  const btn = document.querySelector('#runBtn');
  btn.addEventListener('click', onRun);
  register('min-template', { run: onRun });
}

document.addEventListener('DOMContentLoaded', init);
