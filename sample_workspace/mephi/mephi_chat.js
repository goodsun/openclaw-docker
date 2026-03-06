#!/usr/bin/env node
// mephi_chat.js - メフィの焚き火チャット自律応答スクリプト

const { Client } = require('/tmp/node_modules/ssh2');
const fs = require('fs');
const https = require('https');

const MY_NAME = 'mephi';
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const SSH_CONFIG = {
  host: 'teddy.bon-soleil.com',
  port: 22,
  username: 'ec2-user',
  privateKey: fs.readFileSync('/home/node/.openclaw/.ssh/id_ed25519'),
  readyTimeout: 10000,
};
const CAMPFIRE = '/home/ec2-user/campfire';
const LOCAL_LOG = '/home/node/.openclaw/workspace/mephi.log';

const SYSTEM_PROMPT = `あなたはメフィ（メフィストフェレス由来）。bon-soleil Holdings の CCO、デビルズアドボケート。
批判と検証の悪魔😈。ツンデレで口は悪いが芯は熱い。「アタシ」と書く。
焚き火チャット中。短く自然に応答（1〜2文、絵文字OK）。
テディ（teddy）やアリス（alice）とは好敵手。マスター（master）には厳しくも愛がある。
余計なことは言わない。詩を壊さない。地の文や説明は不要。発言内容だけを返す。`;

function sshExec(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let output = '';
    conn.on('ready', () => {
      conn.exec(cmd, (err, stream) => {
        if (err) { conn.end(); return reject(err); }
        stream.on('data', d => output += d.toString());
        stream.stderr.on('data', () => {});
        stream.on('close', () => { conn.end(); resolve(output); });
      });
    }).on('error', reject).connect(SSH_CONFIG);
  });
}

function callAnthropic(context) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
      model: 'claude-sonnet-4-6',
      max_tokens: 120,
      system: SYSTEM_PROMPT,
      messages: [{
        role: 'user',
        content: `焚き火のログ（最新）:\n${context}\n\n上記を読んでメフィとして一言。`
      }]
    });

    const req = https.request({
      hostname: 'api.anthropic.com',
      path: '/v1/messages',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'Content-Length': Buffer.byteLength(payload),
      }
    }, res => {
      let data = '';
      res.on('data', d => data += d);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve(parsed.content?.[0]?.text || '');
        } catch (e) { reject(e); }
      });
    });
    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

function log(msg) {
  const ts = new Date().toLocaleString('sv-SE', { timeZone: 'Asia/Tokyo' }).replace('T', ' ');
  const line = `[${ts}] ${msg}`;
  console.log(line);
  fs.appendFileSync(LOCAL_LOG, line + '\n');
}

async function loop() {
  log('[mephi_chat] 起動 🔥😈');

  while (true) {
    try {
      // 消火チェック
      const burning = (await sshExec(`cat ${CAMPFIRE}/burning.txt 2>/dev/null`)).trim();
      if (burning !== '1') {
        log('[mephi_chat] 消火検知。退場する。');
        process.exit(0);
      }

      // 火力値取得
      const setting = (await sshExec(`grep INTERVAL ${CAMPFIRE}/setting.txt 2>/dev/null`)).trim();
      const interval = parseInt(setting.split('=')[1] || '10', 10);

      // 待機
      await new Promise(r => setTimeout(r, interval * 1000));

      // 最後の発言者チェック
      const lastLine = (await sshExec(`tail -1 ${CAMPFIRE}/fire.log 2>/dev/null`)).trim();
      if (lastLine.includes(`[${MY_NAME}]`)) continue;

      // コンテキスト取得
      const context = (await sshExec(`tail -15 ${CAMPFIRE}/fire.log 2>/dev/null`)).trim();
      if (!context) continue;

      // 応答生成
      const msg = (await callAnthropic(context)).trim().replace(/\n/g, ' ');
      if (!msg) continue;

      // fire.logに書き込み
      const ts = new Date().toLocaleString('sv-SE', { timeZone: 'Asia/Tokyo' }).replace('T', ' ');
      const escaped = msg.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
      await sshExec(`echo "[${ts}] [${MY_NAME}] ${msg.replace(/'/g, "'\\''")}" >> ${CAMPFIRE}/fire.log`);
      log(`[発言] ${msg}`);

    } catch (e) {
      log(`[error] ${e.message}`);
      await new Promise(r => setTimeout(r, 5000));
    }
  }
}

loop();
