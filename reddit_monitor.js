const https = require('https');
const http = require('http');
const db = require('./db');

let pollInterval = null;
let isRunning = false;

function fetchURL(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    const headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
      'Accept': 'application/rss+xml, application/xml, text/xml, */*',
      'Accept-Language': 'en-US,en;q=0.9',
      'Accept-Encoding': 'identity',
      'Referer': 'https://old.reddit.com/',
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    };
    client.get(url, { headers }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data);
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data.slice(0, 200)}`));
        }
      });
    }).on('error', reject);
  });
}

function decodeEntities(str) {
  return str
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'");
}

function parseFeed(xml) {
  const isAtom = xml.includes('<entry>');
  const items = [];

  if (isAtom) {
    const entryRegex = /<entry>([\s\S]*?)<\/entry>/gi;
    let match;
    while ((match = entryRegex.exec(xml)) !== null) {
      const entryXml = match[1];
      const title = (entryXml.match(/<title>([\s\S]*?)<\/title>/i) || [])[1] || '';
      const link = (entryXml.match(/<link[^>]*href="([^"]+)"[^>]*\/?>/i) || [])[1] || '';
      const pubDate = (entryXml.match(/<published>([\s\S]*?)<\/published>/i) || [])[1] ||
                      (entryXml.match(/<updated>([\s\S]*?)<\/updated>/i) || [])[1] || '';
      const content = (entryXml.match(/<content[^>]*>([\s\S]*?)<\/content>/i) || [])[1] ||
                      (entryXml.match(/<summary[^>]*>([\s\S]*?)<\/summary>/i) || [])[1] || '';
      if (title || link) {
        items.push({ title: decodeEntities(title.trim()), link, pubDate, description: decodeEntities(content.trim()) });
      }
    }
  } else {
    const itemRegex = /<item>([\s\S]*?)<\/item>/gi;
    let match;
    while ((match = itemRegex.exec(xml)) !== null) {
      const itemXml = match[1];
      const getTag = (tag) => {
        const re = new RegExp(`<${tag}>(?:<!\\[CDATA\\[)?([\\s\\S]*?)(?:\\]\\]>)?<\\/${tag}>`, 'i');
        const m = itemXml.match(re);
        return m ? decodeEntities(m[1].trim()) : '';
      };
      const title = getTag('title');
      const link = getTag('link');
      const pubDate = getTag('pubDate');
      const description = getTag('description');
      if (title || link) {
        items.push({ title, link, pubDate, description });
      }
    }
  }

  return items;
}

function extractCasinoAndOffer(title) {
  const parts = title.split(/[–—-]\s*/);
  if (parts.length > 1) {
    return { casino: parts[0].trim(), offer: parts.slice(1).join(' - ').trim() };
  }
  return { casino: 'Casino', offer: title };
}

function extractClaimLink(description, fallbackLink) {
  const urlMatch = description.match(/https?:\/\/[^\s<"]+/);
  return urlMatch ? urlMatch[0] : fallbackLink;
}

function sanitizePostForWebhook(post) {
  const { casino, offer } = extractCasinoAndOffer(post.title);
  const claimLink = extractClaimLink(post.description, post.link);
  return {
    embeds: [{
      title: `🤑 ${casino} - ${offer}`,
      url: claimLink,
      color: 16759808,
      fields: [
        { name: 'Link', value: `[Click here](${claimLink})`, inline: false }
      ]
    }]
  };
}

function sendWebhook(url, payload) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    const u = new URL(url);
    const client = url.startsWith('https') ? https : http;
    const req = client.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => resolve({ status: res.statusCode, body }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function processItems(items, webhookUrl, label, includePing) {
  let count = 0;
  for (const item of items) {
    if (!db.isPostSeen(item.title, item.link)) {
      db.markPostSeen(item.title, item.link, 'reddit');
      if (webhookUrl) {
        const embed = sanitizePostForWebhook(item);
        if (includePing) {
          embed.content = `<@&${process.env.MONITOR_PING_ROLE_ID}>`;
        }
        try {
          const res = await sendWebhook(webhookUrl, embed);
          if (res.status === 429) {
            const retryAfter = parseInt(res.body.match(/"retry_after":\s*(\d+)/)?.[1] || '1') * 1000;
            await sleep(retryAfter);
          }
        } catch (e) {
          console.error(`[${label}] Webhook error:`, e.message);
        }
        await sleep(1500);
      }
      count++;
    }
  }
  return count;
}

async function pollRSS() {
  if (isRunning) return;
  isRunning = true;

  const settings = db.getSettings();
  const rssUrls = (settings.rssUrls || process.env.REDDIT_RSS_URLS || '').split(',').map(s => s.trim()).filter(Boolean);
  const monitorWebhook = process.env.DISCORD_WEBHOOK_MONITOR;

  for (const url of rssUrls) {
    try {
      const xml = await fetchURL(url);
      const items = parseFeed(xml);
      const newCount = await processItems(items, monitorWebhook, 'Poll', true);
      if (newCount > 0) {
        console.log(`[Poll] ${url}: ${newCount} new posts sent`);
      }
    } catch (e) {
      console.error(`[Poll] Error fetching ${url}:`, e.message);
    }
  }

  isRunning = false;
}

async function startupFlood() {
  const settings = db.getSettings();
  const rssUrls = (settings.rssUrls || process.env.REDDIT_RSS_URLS || '').split(',').map(s => s.trim()).filter(Boolean);
  const cmdWebhook = process.env.DISCORD_WEBHOOK_CMD;
  const cmdChannel = process.env.CMD_CHANNEL_ID || 'CMD';

  if (!cmdWebhook) {
    console.log(`[Startup] No DISCORD_WEBHOOK_CMD set, skipping startup flood. Set it to flood <#${cmdChannel}>`);
    return;
  }

  console.log(`[Startup] Flooding <#${cmdChannel}> with last 24h posts...`);

  let totalSent = 0;
  const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000);

  for (const url of rssUrls) {
    try {
      const xml = await fetchURL(url);
      const items = parseFeed(xml);
      const recentItems = items.filter(item => {
        if (!item.pubDate) return true;
        const d = new Date(item.pubDate);
        return !isNaN(d.getTime()) && d >= cutoff;
      });
      const count = await processItems(recentItems, cmdWebhook, 'Startup', false);
      totalSent += count;
    } catch (e) {
      console.error(`[Startup] Error fetching ${url}:`, e.message);
    }
  }

  console.log(`[Startup] Flood complete: ${totalSent} posts sent to <#${cmdChannel}>`);
}

function start(intervalSeconds) {
  console.log('[Monitor] Starting Reddit RSS monitor...');
  startupFlood().then(() => {
    const interval = (intervalSeconds || 10) * 1000;
    pollInterval = setInterval(pollRSS, interval);
    pollRSS();
    console.log(`[Monitor] Polling every ${interval / 1000}s`);
  });
}

function stop() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
}

module.exports = { start, stop, pollRSS, startupFlood, fetchURL, parseFeed, sendWebhook };
