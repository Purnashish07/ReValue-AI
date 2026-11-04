const form = document.getElementById('uploadForm');
const input = document.getElementById('imageInput');
const dropzone = document.getElementById('dropzone');
const previewWrap = document.getElementById('previewWrap');
const preview = document.getElementById('preview');
const analyzeBtn = document.getElementById('analyzeBtn');
const errorBox = document.getElementById('error');
let currentReport = null;
let currentImage = null;

function showError(msg) { errorBox.textContent = msg; errorBox.classList.remove('hidden'); }
function clearError() { errorBox.textContent = ''; errorBox.classList.add('hidden'); }
function setFile(file) {
  clearError();
  if (!file) return;
  if (!['image/png','image/jpeg','image/webp'].includes(file.type)) return showError('Choose a PNG, JPG, or WEBP image.');
  if (file.size > 10 * 1024 * 1024) return showError('Image must be smaller than 10 MB.');
  const transfer = new DataTransfer(); transfer.items.add(file); input.files = transfer.files;
  preview.src = URL.createObjectURL(file); previewWrap.classList.remove('hidden');
}
input.addEventListener('change', () => setFile(input.files[0]));
document.getElementById('clearImage').addEventListener('click', () => { input.value=''; previewWrap.classList.add('hidden'); preview.removeAttribute('src'); });
dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag'));
dropzone.addEventListener('drop', e => { e.preventDefault(); dropzone.classList.remove('drag'); setFile(e.dataTransfer.files[0]); });

function listInto(id, items, emptyText) {
  const ul = document.getElementById(id); ul.innerHTML = '';
  (items && items.length ? items : [emptyText]).forEach(t => {
    const li = document.createElement('li'); li.textContent = t; ul.appendChild(li);
  });
}
function addText(parent, tag, text, className='') {
  const el = document.createElement(tag); el.textContent = text;
  if (className) el.className = className;
  parent.appendChild(el); return el;
}
function render(data) {
  currentReport = data.report; currentImage = data.image_data;
  document.getElementById('results').classList.remove('hidden');
  document.getElementById('summary').textContent = data.analysis.device_summary || 'No summary available.';
  document.getElementById('componentCount').textContent = data.analysis.items?.length ?? 0;
  document.getElementById('components').innerHTML = '';
  const colors = ['#b6e35e','#57c6a1','#7da8f5','#f4bd62','#c59be8','#f18f83'];
  const svg = document.getElementById('overlay'); svg.innerHTML = '';
  const ns = 'http://www.w3.org/2000/svg';
  (data.analysis.items || []).forEach((item, i) => {
    const card = document.createElement('div'); card.className='component';
    const titleRow = document.createElement('div'); titleRow.className='component-title';
    addText(titleRow,'span',item.name || 'Unspecified component');
    addText(titleRow,'span',item.confidence || 'uncertain','pill');
    card.appendChild(titleRow);
    addText(card,'p',item.visual_evidence || item.reason || 'No visual evidence provided.');
    addText(card,'small',`Potential pathway: ${(item.possible_path || 'unknown').replaceAll('_',' ')} · Verify: ${item.verification_needed || 'physical inspection required'}`);
    document.getElementById('components').appendChild(card);
    if (Array.isArray(item.bbox) && item.bbox.length === 4) {
      const [x1,y1,x2,y2] = item.bbox.map(v => Number(v) / 10);
      const rect = document.createElementNS(ns,'rect');
      rect.setAttribute('x',x1+'%'); rect.setAttribute('y',y1+'%');
      rect.setAttribute('width',Math.max(0,x2-x1)+'%'); rect.setAttribute('height',Math.max(0,y2-y1)+'%');
      rect.setAttribute('fill','none'); rect.setAttribute('stroke',colors[i%colors.length]); rect.setAttribute('stroke-width','3'); rect.setAttribute('vector-effect','non-scaling-stroke');
      svg.appendChild(rect);
      const label = document.createElementNS(ns,'text'); label.setAttribute('x',x1+'%'); label.setAttribute('y',Math.max(4,y1)+'%');
      label.setAttribute('fill',colors[i%colors.length]); label.setAttribute('font-size','14'); label.setAttribute('font-weight','700'); label.setAttribute('paint-order','stroke'); label.setAttribute('stroke','#17231e'); label.setAttribute('stroke-width','2'); label.textContent = item.name || `Item ${i+1}`; svg.appendChild(label);
    }
  });
  document.getElementById('mapImage').src = data.image_data;
  document.getElementById('mapEmpty').classList.add('hidden');
  document.getElementById('mapWrap').classList.remove('hidden');
  const legend = document.getElementById('legend'); legend.innerHTML = '';
  (data.analysis.items || []).forEach((item,i) => { const span=addText(legend,'span',`${i+1}. ${item.name || 'Component'}`); span.style.borderLeft=`3px solid ${colors[i%colors.length]}`; });
  listInto('sorting',data.analysis.sorting_plan,'No sorting recommendations returned.');
  listInto('safety',data.analysis.safety_notes,'Follow qualified e-waste handling procedures.');
  listInto('limitations',data.analysis.limitations,'Visual inspection alone cannot establish component condition.');
  document.getElementById('results').scrollIntoView({behavior:'smooth',block:'start'});
}
form.addEventListener('submit', async e => {
  e.preventDefault(); clearError();
  if (!input.files[0]) return showError('Please choose an image first.');
  analyzeBtn.disabled = true; analyzeBtn.innerHTML = 'Analyzing image… <span>◌</span>';
  try {
    const body = new FormData(); body.append('image',input.files[0]);
    const response = await fetch('/api/analyze',{method:'POST',body});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Analysis failed.');
    render(data);
  } catch(err) { showError(err.message || 'Something went wrong.'); }
  finally { analyzeBtn.disabled = false; analyzeBtn.innerHTML = 'Analyze image <span>→</span>'; }
});
document.getElementById('exportBtn').addEventListener('click', () => {
  if (!currentReport) return;
  const blob = new Blob([JSON.stringify(currentReport,null,2)],{type:'application/json'});
  const url = URL.createObjectURL(blob); const a=document.createElement('a');
  a.href=url; a.download='revalue_recovery_report.json'; a.click(); URL.revokeObjectURL(url);
});
