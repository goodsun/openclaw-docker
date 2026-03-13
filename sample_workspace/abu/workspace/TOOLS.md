# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## labo_portal

- パス: `/home/node/labo_portal`
- アクセス: `http://172.21.0.2:8800/` または `http://172.20.0.3:8800/`
- パスワード: `mie_portal_2026`（環境変数 LABO_PASSWORD が優先される）
- 起動: `cd /home/node/labo_portal && npm run dev`
- ログ: `/tmp/labo.log`

## openclaw agent（シェルから呼びかけ）

```bash
openclaw agent --agent main --message "メッセージ"
```

Add whatever helps you do your job. This is your cheat sheet.
