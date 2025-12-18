document.addEventListener('DOMContentLoaded', () => {

const FEATURE_ORDER = ['age','sex','cp','trestbps','chol','fbs','restecg','thalach','exang','oldpeak','slope','ca','thal'];
const STORAGE_KEY = 'heart_inputs_v2';

const SAMPLE_NO = [62,0,0,140,268,0,0,160,0,3.6,0,2,2];
const SAMPLE_YES = [63,1,3,145,233,1,0,150,0,2.3,0,0,1];

const q = id => document.getElementById(id);

/* ---------- RENDER INPUTS ---------- */
const inputsBox = q('inputs');
FEATURE_ORDER.forEach(f=>{
  inputsBox.innerHTML += `
    <div>
      <label>${f}</label>
      <input id="${f}" type="text">
    </div>`;
});

/* ---------- COLOR CODING ---------- */
function colorCodeInputs(){
  FEATURE_ORDER.forEach(f=>{
    const el = q(f);
    if(!el) return;

    const val = Number(el.value);
    el.classList.remove('safe','warning','danger');
    if(isNaN(val)) return;

    if (f === 'chol') {
      if (val < 200) el.classList.add('safe');
      else if (val < 240) el.classList.add('warning');
      else el.classList.add('danger');
    }
    else if (f === 'age') {
      if (val < 45) el.classList.add('safe');
      else if (val <= 60) el.classList.add('warning');
      else el.classList.add('danger');
    }
    else if (f === 'thalach') {
      if (val > 150) el.classList.add('safe');
      else if (val >= 120) el.classList.add('warning');
      else el.classList.add('danger');
    }
    else if (f === 'oldpeak') {
      if (val < 1) el.classList.add('safe');
      else if (val < 2) el.classList.add('warning');
      else el.classList.add('danger');
    }
    else {
      if (val < 33) el.classList.add('safe');
      else if (val < 66) el.classList.add('warning');
      else el.classList.add('danger');
    }
  });
}

/* ---------- STORAGE ---------- */
function save(){
  const data = {
    inputs: FEATURE_ORDER.map(f=>q(f).value || null),
    patient: q('patient_name').value || null,
    notes: q('notes').value || null
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function load(){
  const d = JSON.parse(localStorage.getItem(STORAGE_KEY)||'{}');
  (d.inputs||[]).forEach((v,i)=> v!==null && (q(FEATURE_ORDER[i]).value=v));
  if(d.patient) q('patient_name').value=d.patient;
  if(d.notes) q('notes').value=d.notes;
}
load();
colorCodeInputs();

/* ---------- INPUT EVENTS ---------- */
FEATURE_ORDER.forEach(f=>{
  q(f).addEventListener('input', ()=>{
    save();
    colorCodeInputs();
  });
});

q('patient_name').addEventListener('input', save);
q('notes').addEventListener('input', save);

/* ---------- ENTER KEY ---------- */
document.addEventListener('keydown',e=>{
  if(e.key==='Enter'){
    const arr=[...document.querySelectorAll('#predictForm input')];
    const i=arr.indexOf(document.activeElement);
    if(i>-1){
      e.preventDefault();
      (arr[i+1] || q('predictBtn')).focus();
    }
  }
});

/* ---------- AUTOFILL ---------- */
q('autofill-no').onclick=()=>fill(SAMPLE_NO);
q('autofill-yes').onclick=()=>fill(SAMPLE_YES);
q('clear').onclick=()=>{
  FEATURE_ORDER.forEach(f=>q(f).value='');
  q('patient_name').value='';
  q('notes').value='';
  save();
  colorCodeInputs();
};

function fill(arr){
  FEATURE_ORDER.forEach((f,i)=>q(f).value=arr[i]);
  save();
  colorCodeInputs();
}

/* ---------- PREDICT ---------- */
let lastPrediction=null;

q('predictForm').addEventListener('submit', async e=>{
  e.preventDefault();

  const features = FEATURE_ORDER.map(f=>Number(q(f).value));
  q('resultText').innerText='Analyzing…';

  const res = await fetch('/predict',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({features})
  });

  const j = await res.json();
  if(!res.ok){
    q('resultText').innerText=j.error;
    return;
  }

  lastPrediction = j;
  updateUI(j);
});

/* ---------- UI UPDATE ---------- */
function updateUI(j){
  const p1=j.probabilities[1];
  const p0=j.probabilities[0];

  q('meter-fill').style.transform=`rotate(${180-p1*180}deg)`;
  q('meter-label').innerText=Math.round(p1*100)+'%';

  q('barFill').style.width=(p1*100)+'%';
  q('p1').innerText=(p1*100).toFixed(1)+'%';
  q('p0').innerText=(p0*100).toFixed(1)+'%';
  q('probBar').classList.remove('hidden');

  q('resultText').innerHTML=j.prediction_by_threshold
    ? '<span style="color:#e63946">High risk of heart disease</span>'
    : '<span style="color:#28a745">Low risk – no heart disease</span>';

  q('rawJson').innerText=JSON.stringify(j,null,2);
}

/* ---------- JSON ---------- */
q('showRawBtn').onclick=()=>q('rawJson').classList.toggle('hidden');

/* ---------- PDF ---------- */
const modal=q('pdfModal');

q('downloadPdfBtn').onclick=()=>{
  if(!lastPrediction){
    alert('Run prediction first');
    return;
  }
  q('pdfSummary').innerHTML=
    `<b>${q('patient_name').value||'Patient'}</b><br>
     Risk: ${Math.round(lastPrediction.probabilities[1]*100)}%`;
  modal.classList.remove('hidden');
};

q('closePdf').onclick=()=>modal.classList.add('hidden');

q('confirmPdf').onclick=async()=>{
  modal.classList.add('hidden');
  const features=FEATURE_ORDER.map(f=>Number(q(f).value));

  const r=await fetch('/report',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({
      features,
      patient_name:q('patient_name').value,
      notes:q('notes').value
    })
  });

  const b=await r.blob();
  const a=document.createElement('a');
  a.href=URL.createObjectURL(b);
  a.download='heart_report.pdf';
  a.click();
};

});