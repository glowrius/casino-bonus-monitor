const { Client, GatewayIntentBits, EmbedBuilder, REST, Routes, SlashCommandBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, ModalBuilder, TextInputBuilder, TextInputStyle } = require('discord.js');

function decodeEntities(str) {
  return str.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&#39;/g, "'").replace(/&apos;/g, "'");
}

function extractCasinoAndOffer(title) {
  const parts = title.split(/[–—-]\s*/);
  if (parts.length > 1) return { casino: parts[0].trim(), offer: parts.slice(1).join(' - ').trim() };
  return { casino: 'Casino', offer: title };
}

function extractClaimLink(description, fallbackLink) {
  const hrefMatch = description.match(/<a[^>]+href="([^"]+)"[^>]*>/i);
  if (hrefMatch) {
    const url = decodeEntities(hrefMatch[1]);
    if (!url.includes('reddit.com')) return url;
  }
  const allUrls = [...description.matchAll(/https?:\/\/[^\s<"']+/g)];
  const nonReddit = allUrls.map(m => m[0]).filter(u => !u.includes('reddit.com') && !u.includes('redd.it'));
  if (nonReddit.length > 0) return decodeEntities(nonReddit[0]);
  if (hrefMatch) return decodeEntities(hrefMatch[1]);
  if (allUrls.length > 0) return decodeEntities(allUrls[0][0]);
  return fallbackLink;
}

function formatCST(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleString('en-US', { timeZone: 'America/Chicago', year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true }) + ' CST';
}

const CASINO_DOMAINS = {
  'chumba': 'chumbacasino.com', 'luckyland': 'luckylandslots.com', 'pulsz': 'pulsz.com', 'stake': 'stake.us',
  'funrize': 'funrize.com', 'global poker': 'globalpoker.com', 'modo': 'modo.us', 'sportzino': 'sportzino.com',
  'realprize': 'realprize.com', 'crown': 'crowncoinscasino.com', 'baba': 'babacasino.com',
};

function getCasinoLogo(casinoName) {
  const name = casinoName.toLowerCase();
  for (const [key, domain] of Object.entries(CASINO_DOMAINS)) {
    if (name.includes(key)) return `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
  }
  if (name.includes('casino') || name.includes('sweep')) return `https://www.google.com/s2/favicons?domain=${name.replace(/[^a-z0-9]/g, '')}.com&sz=64`;
  return null;
}

class DiscordBot {
  constructor() {
    this.client = null;
    this.ready = false;
    this.monitorChannel = null;
    this.cmdChannel = null;
    this.streamerChannel = null;
    this.dailyClaimsChannel = null;
    this.guildId = null;
    this._readyPromise = null;
    this._resolveReady = null;
    this.startTime = null;
    this.commandHandlers = {};
    this.claimRunner = null;
  }

  async init() {
    this.startTime = Date.now();
    this._readyPromise = new Promise(resolve => { this._resolveReady = resolve; });

    const token = process.env.DISCORD_BOT_TOKEN;
    if (!token) {
      console.log('[Bot] No DISCORD_BOT_TOKEN set - console-only mode');
      this.ready = true;
      this._resolveReady();
      return;
    }

    this.client = new Client({ intents: [GatewayIntentBits.Guilds] });

    this.client.once('ready', async () => {
      console.log(`[Bot] Logged in as ${this.client.user.tag}`);
      this.ready = true;

      const monitorId = process.env.MONITOR_CHANNEL_ID;
      const cmdId = process.env.CMD_CHANNEL_ID;
      const streamerId = process.env.STREAMER_CHANNEL_ID;
      const dailyClaimsId = process.env.DAILY_CLAIMS_CHANNEL_ID;
      try {
        if (monitorId) this.monitorChannel = await this.client.channels.fetch(monitorId);
        if (cmdId) this.cmdChannel = await this.client.channels.fetch(cmdId);
        if (streamerId) this.streamerChannel = await this.client.channels.fetch(streamerId);
        if (dailyClaimsId) this.dailyClaimsChannel = await this.client.channels.fetch(dailyClaimsId);
        if (this.monitorChannel) this.guildId = this.monitorChannel.guildId;
        else if (this.cmdChannel) this.guildId = this.cmdChannel.guildId;
        else if (this.streamerChannel) this.guildId = this.streamerChannel.guildId;
        else if (this.dailyClaimsChannel) this.guildId = this.dailyClaimsChannel.guildId;
      } catch (e) {
        console.log('[Bot] Channel fetch error:', e.message);
      }
      if (!this.monitorChannel) console.log(`[Bot] WARNING: Monitor channel ${monitorId} not found`);
      if (!this.cmdChannel) console.log(`[Bot] WARNING: CMD channel ${cmdId} not found`);
      if (!this.streamerChannel) console.log(`[Bot] WARNING: Streamer channel ${streamerId} not found`);
      if (!this.dailyClaimsChannel) console.log(`[Bot] WARNING: Daily claims channel ${dailyClaimsId} not found`);
      if (!this.guildId) this.guildId = this.client.guilds.cache.first()?.id;
      console.log(`[Bot] Guild ID: ${this.guildId || 'N/A'}`);

      await this._registerCommands();
      this._resolveReady();
    });

    this.client.on('interactionCreate', async (interaction) => {
      try {
        if (interaction.isChatInputCommand()) {
          const sub = interaction.options.getSubcommand(false);
          const key = sub ? `${interaction.commandName}_${sub}` : interaction.commandName;
          const handler = this.commandHandlers[key];
          if (handler) {
            await handler(interaction);
          } else {
            console.log(`[Bot] No handler for ${key}`);
            await interaction.reply({ content: `Unknown command: \`/${key}\``, ephemeral: true });
          }
          return;
        }

        if (interaction.isButton()) {
          const handler = this.buttonHandlers[interaction.customId];
          if (handler) {
            await handler(interaction);
          } else {
            await interaction.reply({ content: `Unknown button: \`${interaction.customId}\``, ephemeral: true });
          }
          return;
        }

        if (interaction.isModalSubmit()) {
          const handler = this.modalHandlers[interaction.customId];
          if (handler) {
            await handler(interaction);
          } else {
            await interaction.reply({ content: `Unknown modal: \`${interaction.customId}\``, ephemeral: true });
          }
          return;
        }
      } catch (e) {
        console.error(`[Bot] Interaction error:`, e);
        try {
          if (interaction.replied || interaction.deferred) {
            await interaction.editReply({ content: `❌ Error: ${e.message}` });
          } else {
            await interaction.reply({ content: `❌ Error: ${e.message}`, ephemeral: true });
          }
        } catch {}
      }
    });

    this.client.login(token).catch(err => {
      console.log(`[Bot] Login failed: ${err.message}. Console-only mode.`);
      this.ready = true;
      this._resolveReady();
    });
  }

  async waitForReady() { await this._readyPromise; }

  onCommand(name, handler) { this.commandHandlers[name] = handler; }

  setClaimRunner(fn) { this.claimRunner = fn; }

  async _registerCommands() {
    const commands = [
      new SlashCommandBuilder().setName('status').setDescription('Show bot status and module information'),
      new SlashCommandBuilder().setName('claim').setDescription('Trigger an immediate daily claim run'),
      new SlashCommandBuilder().setName('hellofresh').setDescription('HelloFresh account management')
        .addSubcommand(sub => sub.setName('create').setDescription('Create HelloFresh accounts')
          .addIntegerOption(opt => opt.setName('amount').setDescription('Number of accounts to create').setRequired(true).setMinValue(1).setMaxValue(10)))
        .addSubcommand(sub => sub.setName('list').setDescription('List saved HelloFresh accounts')),
    ];
    try {
      const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_BOT_TOKEN);
      if (this.guildId) {
        await rest.put(Routes.applicationGuildCommands(this.client.user.id, this.guildId), { body: commands.map(c => c.toJSON()) });
        console.log(`[Bot] Guild commands registered for ${this.guildId}`);
      } else {
        await rest.put(Routes.applicationCommands(this.client.user.id), { body: commands.map(c => c.toJSON()) });
        console.log('[Bot] Global commands registered (may take ~1hr to appear)');
      }
    } catch (e) {
      console.log('[Bot] Slash commands failed:', e.message);
    }
  }

  async sendMonitorPost(post) {
    if (!this.monitorChannel) return;
    const embed = this._buildPostEmbed(post);
    await this.monitorChannel.send({ embeds: [embed] }).catch(() => {});
  }

  async sendFloodPost(post) {
    if (!this.cmdChannel) return;
    const embed = this._buildPostEmbed(post);
    await this.cmdChannel.send({ embeds: [embed] }).catch(() => {});
  }

  async sendStreamerAlert(name, url, sender) {
    if (!this.streamerChannel) return;
    const embed = new EmbedBuilder()
      .setTitle(`🎯 ${name}`).setURL(url).setColor(0x57F287)
      .setDescription(`◎ ${sender} dropped a link`)
      .setFooter({ text: '◎ Casino Bonus Monitor™' }).setTimestamp();
    await this.streamerChannel.send({ embeds: [embed] }).catch(() => {});
  }

  async sendClaimResults(results) {
    if (!this.monitorChannel) return;
    const ok = results.filter(r => r.success).length;
    const fail = results.filter(r => !r.success).length;
    const embed = new EmbedBuilder()
      .setTitle('📋 Daily Auto-Claim Results').setColor(fail > 0 ? 0xFFAA00 : 0x57F287).setTimestamp()
      .addFields({ name: '✅ Successful', value: `${ok} / ${results.length}`, inline: true }, { name: '❌ Failed', value: `${fail} / ${results.length}`, inline: true });
    for (const r of results.slice(0, 5)) {
      embed.addFields({ name: `${r.success ? '✅' : '❌'} ${r.casino}`, value: r.success ? 'Claimed successfully' : `Failed (${r.status || r.error || 'unknown'})`, inline: false });
    }
    await this.monitorChannel.send({ embeds: [embed] }).catch(() => {});
  }

  async sendMonitorMessage(content) {
    if (!this.monitorChannel) return;
    await this.monitorChannel.send(content).catch(() => {});
  }

  async sendCmdMessage(content) {
    if (!this.cmdChannel) return;
    await this.cmdChannel.send(content).catch(() => {});
  }

  _buildPostEmbed(post) {
    const { casino, offer } = extractCasinoAndOffer(post.title);
    const claimLink = extractClaimLink(post.description, post.link);
    const logoUrl = getCasinoLogo(casino);
    const pubDate = post.pubDate ? new Date(post.pubDate) : new Date();
    const description = claimLink && claimLink !== post.link
      ? `◎ ${casino}\n**[Claim Here](${claimLink})**`
      : `◎ ${casino}`;
    const embed = new EmbedBuilder()
      .setTitle(offer).setURL(claimLink).setDescription(description)
      .setColor(0x57F287).setFooter({ text: '◎ Casino Bonus Monitor™' }).setTimestamp(pubDate);
    if (logoUrl) embed.setThumbnail(logoUrl);
    return embed;
  }

  stop() {
    if (this.client) { this.client.destroy(); this.client = null; }
    this.ready = false;
  }
}

module.exports = new DiscordBot();
