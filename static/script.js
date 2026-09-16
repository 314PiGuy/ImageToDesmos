const fileInput = document.querySelector('#file');
const drop = document.querySelector('#drop');
const preview = document.querySelector('#preview');
const image = document.querySelector('#preview-image');
const launch = document.querySelector('#launch');
const status = document.querySelector('#status');
const details = document.querySelector('#details');
const controls = [...document.querySelectorAll('input[name], select[name]')];
let file, result, stage = 'traced', timer, requestNumber = 0;

document.querySelectorAll('.slider').forEach(label => {
  const input = label.querySelector('input');
  const output = label.querySelector('output');
  const show = () => output.value = input.value;
  input.addEventListener('input', show); show();
});

function setMode() {
  const edges = document.querySelector('[name=mode]:checked').value === 'canny';
  document.querySelectorAll('.edges').forEach(el => el.hidden = !edges);
  document.querySelectorAll('.ink').forEach(el => el.hidden = edges);
}

function setStages() {
  document.querySelectorAll('[data-controls]').forEach(toggle => {
    const control = document.querySelector(`[name="${toggle.dataset.controls}"]`);
    control.disabled = !toggle.checked;
    control.closest('.slider').classList.toggle('disabled', !toggle.checked);
  });
  document.querySelectorAll('[data-section]').forEach(toggle => {
    const options = document.querySelector(`[data-stage-options="${toggle.dataset.section}"]`);
    options.classList.toggle('disabled', !toggle.checked);
    options.querySelectorAll('input, select').forEach(control => control.disabled = !toggle.checked);
  });
}

function useFile(next) {
  if (!next || !next.type.startsWith('image/')) return;
  file = next;
  drop.querySelector('.drop-title').textContent = next.name;
  drop.querySelector('.drop-note').textContent = `${(next.size / 1048576).toFixed(1)} MB · click to replace`;
  result = { original: URL.createObjectURL(next) };
  update();
}

async function update() {
  if (!file) return;
  const current = ++requestNumber;
  preview.classList.remove('empty'); preview.classList.add('loading');
  status.textContent = 'Updating preview…'; launch.disabled = true;
  const data = new FormData(); data.append('image', file);
  controls.forEach(control => {
    if (control.type === 'radio' && !control.checked) return;
    data.append(control.name, control.type === 'checkbox' ? control.checked : control.value);
  });
  try {
    const response = await fetch('/api/preview', { method: 'POST', body: data });
    const next = await response.json();
    if (!response.ok) throw new Error(next.error || 'Preview failed');
    if (current !== requestNumber) return;
    result = { ...result, ...next };
    showStage();
    status.textContent = next.trace_enabled ? 'Ready for Desmos' : 'Potrace is disabled';
    details.textContent = next.trace_enabled
      ? `${next.width} × ${next.height} · ${next.segments.toLocaleString()} curve segments`
      : `${next.width} × ${next.height} · preprocessing preview only`;
    launch.disabled = !next.expressions.length;
  } catch (error) {
    if (current !== requestNumber) return;
    status.textContent = error.message; details.textContent = 'Try another image or different settings.';
  } finally {
    if (current === requestNumber) preview.classList.remove('loading');
  }
}

function showStage() {
  if (result && result[stage]) image.src = result[stage];
}

controls.forEach(control => control.addEventListener('input', () => {
  setMode(); setStages(); clearTimeout(timer); timer = setTimeout(update, 280);
}));
document.querySelectorAll('[data-stage]').forEach(button => button.addEventListener('click', () => {
  document.querySelector('.tabs .active').classList.remove('active'); button.classList.add('active');
  stage = button.dataset.stage; showStage();
}));
fileInput.addEventListener('change', () => useFile(fileInput.files[0]));
['dragenter', 'dragover'].forEach(event => drop.addEventListener(event, e => { e.preventDefault(); drop.classList.add('drag'); }));
['dragleave', 'drop'].forEach(event => drop.addEventListener(event, e => { e.preventDefault(); drop.classList.remove('drag'); }));
drop.addEventListener('drop', e => useFile(e.dataTransfer.files[0]));
launch.addEventListener('click', () => {
  sessionStorage.setItem('imageToDesmos', JSON.stringify({ expressions: result.expressions, width: result.width, height: result.height }));
  location.href = '/desmos';
});
setMode(); setStages();
