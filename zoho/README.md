# Zoho Cliq Crypto Monitoring App (Bot Participation Handler Version)

## Overview
This application monitors crypto prices, detects volatility, and sends alerts to Zoho Cliq via a Bot. It uses a **Participation Handler** architecture instead of Incoming Webhooks.

## Architecture
1. **Backend (Flask)**: Handles logic, DB, and external APIs.
2. **Cliq Bot**: Forwards user commands to Backend and receives alerts.
3. **Worker**: Runs periodically to check prices and push alerts to the Bot.

## Setup Instructions

### 1. Backend Setup
1. Navigate to `backend/`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure `.env`:
   - `BOT_TOKEN`: Your Zoho Cliq Bot Token (zapikey).
   - `BOT_ID`: Your Bot's Unique Name (e.g., `cryptobot`).
   - `NEWS_API_KEY`: API Key for news service.
4. Initialize DB:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```
5. Run Server:
   ```bash
   python run.py
   ```
6. Run Worker:
   ```bash
   python worker.py
   ```

### 2. Zoho Cliq Bot Setup
1. Create a Bot in Zoho Cliq Developer Console.
2. **Handlers**:
   - Use the code in `cliq_extension/bot/participation_handler.js`.
   - If using Zoho Sigma, paste the code there.
   - **IMPORTANT**: Update `BACKEND_URL` in the JS file to point to your deployed backend (e.g., `https://your-app.com/api/cliq/event`).
3. **Manifest**:
   - Use `cliq_extension/manifest.json` as a reference for commands and permissions.

### 3. How it Works
- **Commands**: User types `/price bitcoin` -> Bot Handler -> Backend `/api/cliq/event` -> Backend replies with text -> Bot displays text.
- **Alerts**: Worker detects volatility -> Calls `ZohoService.send_message` -> Uses Zoho REST API to post message to user's default channel.

## Troubleshooting
- **Bot not replying**: Check `BACKEND_URL` in `participation_handler.js`. Ensure backend is reachable (use ngrok for local).
- **No Alerts**: Ensure `BOT_TOKEN` is correct and the bot is in the channel.
