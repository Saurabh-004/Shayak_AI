from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_health(): assert client.get('/health').json()=={'status':'ok'}
def test_bank_scam_high():
 r=client.post('/api/analyze/text',json={'text':'Your SBI account will be blocked today. Click this link and update KYC immediately with OTP.'});assert r.status_code==200 and r.json()['analysis']['risk_level']=='HIGH'
def test_low_message(): assert client.post('/api/analyze/text',json={'text':'Your appointment is confirmed for tomorrow at 10 AM.'}).json()['analysis']['risk_level']=='LOW'
def test_empty_rejected(): assert client.post('/api/analyze/text',json={'text':'  '}).status_code==400
def test_url(): assert client.post('/api/analyze/url',json={'url':'https://secure-bank-login.xyz/a'}).json()['analysis']['risk_level'] in ('MEDIUM','HIGH')
def test_headers():
 r=client.get('/health');assert r.headers['x-content-type-options']=='nosniff' and r.headers['x-frame-options']=='DENY'
def test_bad_upload(): assert client.post('/api/analyze/image',files={'image':('bad.svg',b'<svg/>','image/svg+xml')}).status_code==400
