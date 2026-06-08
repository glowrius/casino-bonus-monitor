const fs = require('fs');
const path = require('path');
const envPath = path.join(process.cwd(), '.env');
try {
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split('\n').filter(l => l.trim() && !l.startsWith('#')).forEach(l => {
    const eqIdx = l.indexOf('=');
    if (eqIdx > 0) { process.env[l.slice(0, eqIdx).trim()] = l.slice(eqIdx + 1).trim(); }
  });
} catch (e) { console.log('No .env found at', envPath); }

if (process.argv.includes('--update')) {
  try { const u = require('./updater'); u.runUpdateCheck(false).then(() => process.exit(0)); } catch (e) { console.log('Updater unavailable:', e.message); process.exit(1); }
  return;
}

const bot = require('./bot');
const db = require('./db');
const redditMonitor = require('./reddit_monitor');
const autoClaim = require('./auto_claim');
const streamerSniper = require('./streamer_sniper');
const hellofresh = require('./modules/hellofresh');

const POLL_INTERVAL = parseInt(process.env.POLL_INTERVAL_SECONDS || '10', 10);
const enabledClaimCount = (() => { try { return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'src', 'data', 'claim_profiles.json'), 'utf8')).filter(p => p.enabled).length; } catch { return 0; } })();

console.log('');
console.log('╔══════════════════════════════════════╗');
console.log('║     CASINO BONUS MONITOR v2          ║');
console.log('╚══════════════════════════════════════╝');
console.log('');
console.log('── Modules ──────────────────────────────');
console.log(`  RSS Monitor:    active (${POLL_INTERVAL}s interval)`);
console.log(`  Auto-Claim:     loaded (${enabledClaimCount} casinos enabled)`);
console.log(`  Streamer Sniper: loaded`);
console.log(`  Updater:        enabled (auto-checks daily)`);
console.log('');
console.log('── Discord ──────────────────────────────');
console.log(`  Bot Token:  ${process.env.DISCORD_BOT_TOKEN ? 'configured' : 'NOT SET'}`);
console.log(`  Monitor Channel: <#${process.env.MONITOR_CHANNEL_ID || 'not set'}>`);
console.log(`  CMD Channel:     <#${process.env.CMD_CHANNEL_ID || 'not set'}>`);
console.log('');

async function main() {
  await bot.init();
  await bot.waitForReady();

  bot.onCommand('status', async (interaction) => {
    const uptime = Math.floor((Date.now() - bot.startTime) / 1000);
    const mins = Math.floor(uptime / 60);
    const secs = uptime % 60;
    await interaction.reply({
      embeds: [{
        title: '📊 Casino Bonus Monitor Status',
        color: 0x57F287,
        fields: [
          { name: 'Uptime', value: `${mins}m ${secs}s`, inline: true },
          { name: 'RSS Monitor', value: `active (${POLL_INTERVAL}s)`, inline: true },
          { name: 'Auto-Claim', value: `${enabledClaimCount} casinos`, inline: true },
          { name: 'Streamer Sniper', value: 'loaded', inline: true },
        ],
        timestamp: new Date().toISOString()
      }],
      ephemeral: true
    });
  });

  bot.onCommand('claim', async (interaction) => {
    await interaction.reply({ content: '⏳ Running daily claim...', ephemeral: true });
    try {
      const results = await autoClaim.runDailyClaim();
      const ok = results.filter(r => r.success).length;
      await interaction.editReply({ content: `✅ Claim run complete: ${ok}/${results.length} successful` });
    } catch (e) {
      await interaction.editReply({ content: `❌ Claim run failed: ${e.message}` });
    }
  });

  bot.onCommand('create', async (interaction) => {
    const service = interaction.options.getString('service');
    const amount = interaction.options.getInteger('amount');
    await interaction.reply({ content: `⏳ Creating ${amount} ${service} account(s)... This may take several minutes.`, ephemeral: true });

    if (service === 'hellofresh') {
      try {
        const results = await hellofresh.createMultiple(amount, (done, total, acct) => {
          bot.sendCmdMessage(`**${service}** | ${done}/${total}: ${acct.email || 'failed'}`);
        });
        const ok = results.filter(r => r.success).length;
        const fail = results.filter(r => !r.success).length;

        const lines = results.slice(0, 5).map(r =>
          r.success ? `✅ ${r.email} | ${r.password}` : `❌ ${r.error}`
        );
        await bot.sendCmdMessage(`**${service} | Create Complete** — ${ok} success, ${fail} failed\n\`\`\`${lines.join('\n')}\`\`\``);

        const msg = ok > 0
          ? `✅ **${service}**: Created ${ok}/${amount} accounts. Details posted in <#${process.env.CMD_CHANNEL_ID}>`
          : `❌ **${service}**: All ${amount} accounts failed. Check logs.`;
        await interaction.editReply({ content: msg });
      } catch (e) {
        await interaction.editReply({ content: `❌ **${service}** error: ${e.message}` });
      }
    }
  });

  redditMonitor.start(POLL_INTERVAL);
  autoClaim.start();
  streamerSniper.start();
  try { require('./updater').startAutoCheck(); } catch (e) { console.log('Updater unavailable:', e.message); }
}

main().catch(e => console.log('Init error:', e.message));

process.on('SIGINT', () => {
  console.log('\nShutting down...');
  redditMonitor.stop();
  autoClaim.stop();
  streamerSniper.stop();
  bot.stop();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\nShutting down...');
  redditMonitor.stop();
  autoClaim.stop();
  streamerSniper.stop();
  bot.stop();
  process.exit(0);
});
