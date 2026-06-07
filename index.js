require('dotenv').config();

const db = require('./db');
const redditMonitor = require('./reddit_monitor');
const autoClaim = require('./auto_claim');
const streamerSniper = require('./streamer_sniper');

const POLL_INTERVAL = parseInt(process.env.POLL_INTERVAL_SECONDS || '10', 10);

console.log('');
console.log('╔══════════════════════════════════════╗');
console.log('║     CASINO BONUS MONITOR v2          ║');
console.log('╚══════════════════════════════════════╝');
console.log('');
console.log('── Modules ──────────────────────────────');
console.log(`  RSS Monitor:    active (${POLL_INTERVAL}s interval)`);
console.log(`  Auto-Claim:     loaded (${require('./data/claim_profiles.json').filter(p => p.enabled).length} casinos enabled)`);
console.log(`  Streamer Sniper: loaded`);
console.log('');
console.log('── Discord ──────────────────────────────');
console.log(`  CMD Channel:     <#${process.env.CMD_CHANNEL_ID || 'not set'}>`);
console.log(`  Monitor Channel: <#${process.env.MONITOR_CHANNEL_ID || 'not set'}>`);
console.log(`  CMD Webhook:     ${process.env.DISCORD_WEBHOOK_CMD ? 'configured' : 'NOT SET'}`);
console.log(`  Monitor Webhook: ${process.env.DISCORD_WEBHOOK_MONITOR ? 'configured' : 'NOT SET'}`);
console.log(`  Role Ping:       ${process.env.MONITOR_PING_ROLE_ID ? 'configured' : 'not set'}`);
console.log('');

redditMonitor.start(POLL_INTERVAL);
autoClaim.start();
streamerSniper.start();

process.on('SIGINT', () => {
  console.log('\nShutting down...');
  redditMonitor.stop();
  autoClaim.stop();
  streamerSniper.stop();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\nShutting down...');
  redditMonitor.stop();
  autoClaim.stop();
  streamerSniper.stop();
  process.exit(0);
});
