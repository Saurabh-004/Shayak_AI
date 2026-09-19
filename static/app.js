const $ = s => document.querySelector(s);
let type = 'text';

const cfg = {
  text: ['Paste a message', 'Paste the message here', 'For example: Your bank account will be blocked today...'],
  url: ['Check a website', 'Paste the website address', 'https://example.com'],
  call: ['Describe a call', 'What did the caller say?', 'For example: The caller said my account will close unless I share an OTP.'],
  image: ['Check a screenshot', 'Choose a JPG, PNG, or WEBP screenshot', ''],
  audio: ['Audio deepfake check', 'Choose an MP3, WAV, OGG, or M4A recording', ''],
  first: ['First speaker call check', 'Choose a call recording. We will isolate the first detected speaker turn.', '']
};

function select(t) { openForm(t); }

document.querySelectorAll('[data-type]').forEach(b => b.onclick = () => select(b.dataset.type));

$('#back').onclick = () => {
  $('#formBox').hidden = true;
  $('#choose').hidden = false;
  $('#result').hidden = true;
};

function openForm(t) {
  type = t;
  const c = cfg[t];
  $('#choose').hidden = true;
  $('#formBox').hidden = false;
  $('#result').hidden = true;
  $('#formTitle').textContent = c[0];
  $('#label').textContent = c[1];
  $('#input').placeholder = c[2];
  $('#input').hidden = ['image', 'audio', 'first'].includes(t);
  $('#image').hidden = t !== 'image';
  $('#audio').hidden = !['audio', 'first'].includes(t);
  $('#voice').hidden = !['text', 'call'].includes(t);
}

async function postAudio(path, file) {
  const d = new FormData();
  d.append('audio', file, file.name || 'first-speaker.wav');
  const r = await fetch(path, { method: 'POST', body: d });
  const data = await r.json();
  if (!r.ok) throw Error(data.error?.message || 'Please try again.');
  return data;
}

$('#submit').onclick = async () => {
  try {
    if (type === 'image') {
      const f = $('#image').files[0];
      if (!f) throw Error('Please choose a screenshot first.');
      const d = new FormData();
      d.append('image', f);
      const r = await fetch('/api/analyze/image', { method: 'POST', body: d });
      const x = await r.json();
      if (!r.ok) throw Error(x.error?.message || 'Please try again.');
      return x.message ? showNote(x.message) : show(x.analysis);
    }
    if (type === 'audio' || type === 'first') {
      const f = $('#audio').files[0];
      if (!f) throw Error('Please choose a recording first.');
      if (type === 'first') {
        showNote('Separating the first speaker. This can take up to a minute…');
        const turn = await postAudio('/api/analyze/first-speaker', f);
        const segment = await trimFirstTurn(f, turn.first_speaker.start_ms, turn.first_speaker.end_ms);
        const result = await postAudio('/api/analyze/audio', segment);
        return showAudio(result.analysis, turn.first_speaker);
      }
      const result = await postAudio('/api/analyze/audio', f);
      return showAudio(result.analysis);
    }
    const r = await fetch('/api/analyze/' + (type === 'call' ? 'call' : type === 'url' ? 'url' : 'text'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(type === 'url' ? { url: $('#input').value } : { text: $('#input').value })
    });
    const data = await r.json();
    if (!r.ok) throw Error(data.error?.message || 'Please try again.');
    show(data.analysis);
  } catch (e) {
    showNote(e.message);
  }
};

async function trimFirstTurn(file, startMs, endMs) {
  const C = window.AudioContext || window.webkitAudioContext;
  if (!C) throw Error('This browser cannot isolate the first speaker. Please use a modern browser.');
  const ctx = new C();
  const buffer = await ctx.decodeAudioData(await file.arrayBuffer());
  const start = Math.max(0, Math.floor(startMs * buffer.sampleRate / 1000));
  const end = Math.min(buffer.length, Math.ceil(endMs * buffer.sampleRate / 1000));
  if (end <= start) throw Error('We could not identify a usable first speaker turn.');
  const mono = new Float32Array(end - start);
  for (let c = 0; c < buffer.numberOfChannels; c++) {
    const channel = buffer.getChannelData(c);
    for (let i = 0; i < mono.length; i++) mono[i] += channel[start + i] / buffer.numberOfChannels;
  }
  return new File([wav(mono, buffer.sampleRate)], 'first-speaker.wav', { type: 'audio/wav' });
}

function wav(samples, rate) {
  const b = new ArrayBuffer(44 + samples.length * 2);
  const v = new DataView(b);
  let p = 0;
  const w = s => { for (let i = 0; i < s.length; i++) v.setUint8(p++, s.charCodeAt(i)); };
  const u = x => { v.setUint32(p, x, true); p += 4; };
  const h = x => { v.setUint16(p, x, true); p += 2; };
  w('RIFF'); u(36 + samples.length * 2); w('WAVEfmt '); u(16); h(1); h(1); u(rate); u(rate * 2); h(2); h(16);
  w('data'); u(samples.length * 2);
  for (const x of samples) { v.setInt16(p, Math.max(-1, Math.min(1, x)) * 32767, true); p += 2; }
  return b;
}

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function list(a, t = 'ul') { return `<${t}>${a.map(x => `<li>${esc(x)}</li>`).join('')}</${t}>`; }

function show(a) {
  $('#formBox').hidden = true;
  $('#result').hidden = false;
  $('#result').className = 'risk ' + a.risk_level;
  const title = a.risk_level === 'HIGH' ? 'Stop and check' : a.risk_level === 'MEDIUM' ? 'Please check before acting' : 'No major warning signs';
  $('#result').innerHTML = `
    <h2>${title}</h2>
    <p class="summary"><strong>${esc(a.summary)}</strong></p>
    <h3>Why?</h3>${list(a.warning_signs)}
    <h3>Do not</h3>${list(a.do_not)}
    <h3>What to do</h3>${list(a.recommended_actions, 'ol')}
    <div class="resultActions">
      <button id="read" class="secondary" type="button">Read this aloud</button>
      <button id="again" type="button">Check another item</button>
    </div>`;
  $('#read').onclick = () => speechSynthesis.speak(new SpeechSynthesisUtterance(a.summary));
  $('#again').onclick = $('#back').onclick;
}

function showAudio(a, turn) {
  $('#formBox').hidden = true;
  $('#result').hidden = false;
  $('#result').className = 'risk ' + a.risk_level;
  $('#result').innerHTML = `
    <h2>Audio risk check</h2>
    <p class="summary"><strong>${esc(a.summary)}</strong></p>
    <p>Risk signal: ${esc(String(a.score))}%</p>
    ${turn ? `<p><strong>First speaker:</strong> Speaker ${esc(turn.speaker)} · ${esc(turn.transcript || 'Speech segment identified')}</p>` : ''}
    <p class="hint">${esc(a.disclaimer)}</p>
    <div class="resultActions"><button id="again" type="button">Check another item</button></div>`;
  $('#again').onclick = $('#back').onclick;
}

function showNote(m) {
  $('#result').hidden = false;
  $('#result').className = 'risk MEDIUM';
  $('#result').innerHTML = `<h2>Please wait</h2><p>${esc(m)}</p>`;
}

$('#voice').onclick = () => {
  const R = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!R) {
    $('#voiceNotice').hidden = false;
    $('#voiceNotice').textContent = 'Voice input is not available in this browser. You can type instead.';
    return;
  }
  const r = new R();
  r.lang = 'en-IN';
  r.onresult = e => { $('#input').value = e.results[0][0].transcript; };
  r.start();
};

async function updateAuthLink() {
  const link = $('.signinLink');
  if (!link) return;
  try {
    const r = await fetch('/api/auth/me');
    if (r.ok) {
      const d = await r.json();
      const email = d.user?.email || '';
      link.textContent = email ? `Signed in as ${email}` : 'Sign out';
      link.href = '#';
      link.onclick = async e => {
        e.preventDefault();
        await fetch('/api/auth/logout', { method: 'POST' });
        location.href = '/';
      };
    }
  } catch (_) {}
}

fetch('/api/status')
  .then(r => r.ok ? r.json() : null)
  .then(s => {
    if (s) {
      $('.demo').textContent = s.demo_mode
        ? 'Demo mode · Your content is not saved.'
        : 'AI analysis enabled · Your content is not saved.';
    }
  })
  .catch(() => {});

updateAuthLink();

const requested = new URLSearchParams(location.search).get('feature');
if (requested && cfg[requested]) openForm(requested);
