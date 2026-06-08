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

  bot.onCommand('hellofresh_create', async (interaction) => {
    const amount = interaction.options.getInteger('amount');
    await interaction.deferReply({ ephemeral: true });

    try {
      const pendings = [];
      for (let i = 0; i < amount; i++) {
        const acct = await hellofresh.createAccount();
        pendings.push(acct);
        await interaction.editReply({ content: `⏳ Creating temp emails... ${i + 1}/${amount} done`, ephemeral: true });
      }

      const linkLines = pendings.map((a, i) =>
        `**${i + 1}.** [Referral Link](${a.referralLink})\n   \`${a.email}\` • Password: \`${a.password}\``
      ).join('\n');

      await interaction.editReply({
        embeds: [{
          title: '✅ Registration Links Ready',
          color: 0x4CEA4D,
          description: `${linkLines}\n\n**📧 Instructions**\n1. Click each referral link above\n2. Register with the temp email shown\n3. The bot will auto-verify once the confirmation email arrives\n4. Check back with \`/hellofresh list\``,
          footer: { text: 'Monitoring inboxes for 10 min per account' }
        }]
      });

      // Background verification
      for (let i = 0; i < pendings.length; i++) {
        const acct = pendings[i];
        const msg = await interaction.followUp({ content: `🔍 Monitoring ${acct.email} for verification email...`, ephemeral: true });
        const ok = await hellofresh.verifyAccount(acct);
        if (ok) {
          const saved = hellofresh.loadAccounts();
          saved.push(acct);
          hellofresh.saveAccounts(saved);
          await interaction.followUp({
            content: `✅ **Account ${i + 1} verified!** \`${acct.email}\``,
            ephemeral: true
          });
        } else {
          await interaction.followUp({
            content: `⏰ **Account ${i + 1} timed out** — \`${acct.email}\`\nNo verification email received within 10 min. Try again.`,
            ephemeral: true
          });
        }
      }

      const v = pendings.filter(a => a.verified).length;
      await interaction.followUp({ content: `**Done!** ${v}/${amount} verified. Use \`/hellofresh list\` to see all.`, ephemeral: true });
    } catch (e) {
      await interaction.editReply({ content: `❌ Error: ${e.message}` });
    }
  });

  console.log('[Bot] Command handlers registered (status, claim, hellofresh_create, hellofresh_list)');

  bot.onCommand('hellofresh_list', async (interaction) => {
    await interaction.deferReply({ ephemeral: true });
    try {
      const accounts = hellofresh.loadAccounts();
      if (accounts.length === 0) {
        await interaction.editReply({ content: 'No HelloFresh accounts saved yet. Use `/hellofresh create <amount>` to start.' });
        return;
      }
      const verified = accounts.filter(a => a.verified).length;
      const shown = accounts.slice(-10).reverse();
      const fields = shown.map((a, i) => ({
        name: `${i + 1}. ${a.email}${a.verified ? ' ✅' : ' ⏳'}`,
        value: `Password: \`${a.password}\`\nCreated: <t:${Math.floor(new Date(a.createdAt).getTime() / 1000)}:R>`,
        inline: false
      }));
      if (accounts.length > 10) fields.unshift({ name: `Showing last 10 of ${accounts.length}`, value: `${verified} verified • ${accounts.length - verified} pending`, inline: false });
      await interaction.editReply({ embeds: [{
        title: 'HelloFresh Accounts',
        color: 0x4CEA4D,
        description: `**${accounts.length} total** • ${verified} verified ✅ • ${accounts.length - verified} pending ⏳`,
        fields,
        footer: { text: 'HF Auto Account Creator' }
      }]});
    } catch (e) {
      await interaction.editReply({ content: `❌ Error: ${e.message}` });
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
