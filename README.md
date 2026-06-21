## IP Cleaner Bot

Telegram bot for managing clean IP lists and syncing to GitHub.

## Deploy on Railway

1. Fork this repo to your GitHub account
2. Go to [railway.app](https://railway.app) and sign in with GitHub
3. Click "New Project" > "Deploy from GitHub repo"
4. Select your forked repo
5. Go to "Variables" tab and add:

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `GITHUB_TOKEN` | GitHub Personal Access Token |
| `GITHUB_REPO` | Repo name (e.g., `username/repo-name`) |
| `GITHUB_BRANCH` | Branch name (default: `main`) |
| `CHANNEL_ID` | Your Telegram channel ID |
| `ADMIN_IDS` | Comma-separated Telegram user IDs |
| `IPS_FILE_PATH` | File path in repo (default: `ips.txt`) |

6. Railway will deploy automatically

## Local Development

```bash
pip install -r requirements.txt
python bot.py
```

## Commands

- `/start` - Show bot menu

## Features

- Inline buttons: Add Admin, Send IP File
- Accepts .txt files with clean IPs
- Updates `ips.txt` in GitHub repository
- Sends notifications to Telegram channel
- Tokens stored as environment variables
