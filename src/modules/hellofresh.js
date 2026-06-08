const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const CAPTCHA_KEY = 'b9738acd8f43cb56c503f68fd4ea4389';
const REFERRAL_CODE = 'FIH-S4Z0J9Z3R1LK';
const ACCOUNTS_FILE = path.join(process.cwd(), 'src', 'data', 'hellofresh_accounts.json');

const FIRST_NAMES = ['James','Mary','John','Patricia','Robert','Jennifer','Michael','Linda','David','Elizabeth','William','Barbara','Richard','Susan','Joseph','Jessica','Thomas','Sarah','Christopher','Karen','Daniel','Lisa','Matthew','Nancy','Anthony','Betty','Mark','Margaret','Donald','Sandra','Steven','Ashley','Paul','Kimberly','Andrew','Emily','Joshua','Donna','Kenneth','Michelle','Kevin','Carol','Brian','Amanda','George','Dorothy','Timothy','Melissa'];
const LAST_NAMES = ['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez','Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin','Lee','Perez','Thompson','White','Harris','Sanchez','Clark','Ramirez','Lewis','Robinson','Walker','Young','Allen','King','Wright','Scott','Torres','Nguyen','Hill','Flores','Green','Adams','Nelson','Baker','Hall','Rivera','Campbell','Mitchell','Carter'];

const ADDRESSES = [
  { street: '123 Main St', city: 'Austin', state: 'TX', zip: '73301' },
  { street: '456 Oak Ave', city: 'Portland', state: 'OR', zip: '97201' },
  { street: '789 Pine Rd', city: 'Denver', state: 'CO', zip: '80201' },
  { street: '321 Elm Dr', city: 'Phoenix', state: 'AZ', zip: '85001' },
  { street: '654 Maple Ln', city: 'Chicago', state: 'IL', zip: '60601' },
  { street: '987 Cedar Ct', city: 'Miami', state: 'FL', zip: '33101' },
  { street: '147 Birch Blvd', city: 'Seattle', state: 'WA', zip: '98101' },
  { street: '258 Walnut Way', city: 'Atlanta', state: 'GA', zip: '30301' },
  { street: '369 Spruce St', city: 'Dallas', state: 'TX', zip: '75201' },
  { street: '741 Cherry Ave', city: 'Nashville', state: 'TN', zip: '37201' },
];

function rand(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
function pick(arr) { return arr[rand(0, arr.length - 1)]; }
function genPassword() { return crypto.randomBytes(12).toString('base64').replace(/[^a-zA-Z0-9]/g, '') + 'A1!'; }
function genPhone() { return `512${rand(100,999)}${rand(1000,9999)}`; }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

class CookieJar {
  constructor() { this.cookies = {}; }
  setFromHeaders(headers) {
    const setCookie = headers['set-cookie'];
    if (!setCookie) return;
    (Array.isArray(setCookie) ? setCookie : [setCookie]).forEach(c => {
      const parts = c.split(';')[0].split('=');
      if (parts.length >= 2) this.cookies[parts[0].trim()] = parts.slice(1).join('=');
    });
  }
  getHeader() { return Object.entries(this.cookies).map(([k, v]) => `${k}=${v}`).join('; '); }
}

function httpsGet(url, opts = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const client = url.startsWith('https') ? https : http;
    const headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.9',
      ...(opts.headers || {})
    };
    if (opts.cookieJar && opts.cookieJar.cookies) headers['Cookie'] = opts.cookieJar.getHeader();
    client.get(url, { headers, rejectUnauthorized: false }, res => {
      if (opts.cookieJar) opts.cookieJar.setFromHeaders(res.headers);
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: d }));
    }).on('error', reject);
  });
}

function httpsPost(url, data, opts = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const client = url.startsWith('https') ? https : http;
    const body = typeof data === 'string' ? data : JSON.stringify(data);
    const headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
      'Content-Type': opts.json !== false ? 'application/json' : (opts.contentType || 'application/x-www-form-urlencoded'),
      'Content-Length': Buffer.byteLength(body),
      'Accept': 'application/json, text/plain, */*',
      'Accept-Language': 'en-US,en;q=0.9',
      ...(opts.headers || {})
    };
    if (opts.cookieJar && Object.keys(opts.cookieJar.cookies).length > 0) headers['Cookie'] = opts.cookieJar.getHeader();
    if (opts.origin) headers['Origin'] = opts.origin;
    if (opts.referer) headers['Referer'] = opts.referer;
    const req = client.request(url, { method: 'POST', headers, rejectUnauthorized: false }, res => {
      if (opts.cookieJar) opts.cookieJar.setFromHeaders(res.headers);
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: d }));
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// mail.tm API
async function createTempEmail() {
  const domRes = await httpsGet('https://api.mail.tm/domains');
  const domains = JSON.parse(domRes.body);
  const domain = domains['hydra:member']?.[0]?.domain || 'mail.tm';
  const id = crypto.randomBytes(8).toString('hex');
  const email = `${id}@${domain}`;
  const password = genPassword();
  await httpsPost('https://api.mail.tm/accounts', { address: email, password });
  const tokRes = await httpsPost('https://api.mail.tm/token', { address: email, password });
  const token = JSON.parse(tokRes.body).token || JSON.parse(tokRes.body).id;
  return { email, password, token };
}

async function pollTempInbox(token, timeoutMs = 90000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const res = await httpsGet('https://api.mail.tm/messages', { headers: { Authorization: `Bearer ${token}` } });
    try {
      const data = JSON.parse(res.body);
      const msgs = data['hydra:member'] || [];
      if (msgs.length > 0) {
        const msgRes = await httpsGet(`https://api.mail.tm${msgs[0]['@id']}`, { headers: { Authorization: `Bearer ${token}` } });
        return JSON.parse(msgRes.body);
      }
    } catch {}
    await sleep(3000);
  }
  return null;
}

// 2captcha API
async function solveCaptcha(siteKey, pageUrl) {
  console.log('[HF] Submitting CAPTCHA to 2captcha...');
  const createRes = await httpsPost('https://api.2captcha.com/createTask', {
    clientKey: CAPTCHA_KEY,
    task: { type: 'RecaptchaV2TaskProxyless', websiteURL: pageUrl, websiteKey: siteKey }
  });
  const createData = JSON.parse(createRes.body);
  if (createData.errorId !== 0) throw new Error(`2captcha create error: ${createData.errorDescription}`);
  const taskId = createData.taskId;
  for (let i = 0; i < 60; i++) {
    await sleep(5000);
    const pollRes = await httpsPost('https://api.2captcha.com/getTaskResult', { clientKey: CAPTCHA_KEY, taskId });
    const pollData = JSON.parse(pollRes.body);
    if (pollData.status === 'ready') return pollData.solution.gRecaptchaResponse;
    if (pollData.errorId !== 0) throw new Error(`2captcha poll error: ${pollData.errorDescription}`);
  }
  throw new Error('2captcha timeout after 5 minutes');
}

function loadAccounts() {
  try { if (fs.existsSync(ACCOUNTS_FILE)) return JSON.parse(fs.readFileSync(ACCOUNTS_FILE, 'utf8')); } catch {}
  return [];
}

function saveAccounts(accounts) {
  const dir = path.dirname(ACCOUNTS_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(ACCOUNTS_FILE, JSON.stringify(accounts, null, 2), 'utf8');
}

async function createAccount() {
  const user = {
    firstName: pick(FIRST_NAMES),
    lastName: pick(LAST_NAMES),
    email: null,
    password: genPassword(),
    phone: genPhone(),
    address: pick(ADDRESSES),
    referralCode: REFERRAL_CODE,
    createdAt: new Date().toISOString()
  };

  console.log('[HF] Creating temp email...');
  const temp = await createTempEmail();
  user.email = temp.email;
  user.tempPassword = temp.password;
  console.log(`[HF] Email: ${user.email}`);

  console.log('[HF] Fetching HelloFresh homepage...');
  const jar = new CookieJar();
  const homeRes = await httpsGet('https://www.hellofresh.com', { cookieJar: jar });
  const siteKey = homeRes.body.match(/data-sitekey=["']([^"']+)/i)?.[1] || '';
  console.log(`[HF] Sitekey: ${siteKey ? 'found' : 'not found'}`);

  if (siteKey) {
    const captchaToken = await solveCaptcha(siteKey, 'https://www.hellofresh.com/pages/raf_lp11?c=' + REFERRAL_CODE);

    console.log('[HF] Registering account...');
    const regData = {
      email: user.email,
      password: user.password,
      firstName: user.firstName,
      lastName: user.lastName,
      address: {
        street: user.address.street,
        city: user.address.city,
        state: user.address.state,
        zip: user.address.zip
      },
      phone: user.phone,
      referralCode: user.referralCode,
      acceptedTerms: true,
      'g-recaptcha-response': captchaToken
    };

    const regRes = await httpsPost('https://www.hellofresh.com/gw/register', regData, {
      cookieJar: jar, origin: 'https://www.hellofresh.com', referer: 'https://www.hellofresh.com/pages/raf_lp11?c=' + REFERRAL_CODE
    });

    if (regRes.status >= 200 && regRes.status < 400) {
      console.log(`[HF] Registration response: ${regRes.status}`);
    } else {
      console.log(`[HF] Registration failed: ${regRes.status} - ${regRes.body.slice(0, 200)}`);
    }
  }

  console.log('[HF] Waiting for verification email...');
  const msg = await pollTempInbox(temp.token);
  let verified = false;
  if (msg) {
    const html = msg.html || msg.text || '';
    const verifyLink = html.match(/https?:\/\/[^\s"']*verify[^\s"']*/i)?.[0] ||
                       html.match(/https?:\/\/[^\s"']*confirm[^\s"']*/i)?.[0] ||
                       html.match(/https?:\/\/[^\s"']+/)?.[0];
    if (verifyLink) {
      console.log('[HF] Clicking verification link...');
      const jar2 = new CookieJar();
      await httpsGet(verifyLink, { cookieJar: jar2 });
      verified = true;
      console.log('[HF] Email verified');
    }
  }

  const account = {
    email: user.email,
    password: user.password,
    firstName: user.firstName,
    lastName: user.lastName,
    address: user.address,
    phone: user.phone,
    referralCode: user.referralCode,
    verified,
    createdAt: user.createdAt
  };

  return account;
}

async function createMultiple(amount, onProgress) {
  const accounts = loadAccounts();
  const results = [];
  for (let i = 0; i < amount; i++) {
    console.log(`[HF] Creating account ${i + 1}/${amount}...`);
    try {
      const acct = await createAccount();
      accounts.push(acct);
      saveAccounts(accounts);
      results.push({ ...acct, success: true, error: null });
      if (onProgress) onProgress(i + 1, amount, acct);
    } catch (e) {
      console.error(`[HF] Account ${i + 1} failed:`, e.message);
      results.push({ success: false, error: e.message });
      if (onProgress) onProgress(i + 1, amount, { success: false, error: e.message });
    }
    if (i < amount - 1) await sleep(rand(10000, 20000));
  }
  return results;
}

module.exports = { createAccount, createMultiple, REFERRAL_CODE };
