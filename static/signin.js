const $ = s => document.querySelector(s);
const next = new URLSearchParams(location.search).get('next') || '';

function note(m) { $('#authStatus').textContent = m; }

async function auth(kind) {
  const email = $('#email').value.trim();
  const password = $('#password').value;
  if (!email || password.length < 10) {
    return note('Enter your email and a password of at least 10 characters.');
  }
  const r = await fetch('/api/auth/' + kind, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const d = await r.json();
  if (!r.ok) return note(d.error?.message || 'Could not sign in.');
  if (!d.authenticated) return note(d.message);
  location.href = next ? '/?feature=' + encodeURIComponent(next) : '/';
}

$('#login').onclick = () => auth('login').catch(() => note('Sign-in is unavailable.'));
$('#signup').onclick = () => auth('signup').catch(() => note('Account creation is unavailable.'));
