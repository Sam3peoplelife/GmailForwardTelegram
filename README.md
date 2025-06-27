<h1 align="center">📧 Gmail Notifications Telegram Bot 🤖</h1>

<p align="center">
  <b>Get instant Gmail notifications in Telegram.<br>
  Multi-account, personal filters, and privacy-first.</b>
</p>

---

## ✨ Features

- **Multi-account support:** Link multiple Gmail accounts per Telegram user.
- **Personal filters:** Whitelist/blacklist email senders and subjects.
- **Custom notification interval:** Choose how often to check for new emails.
- **Privacy:** All user data (tokens, filters) is stored locally.
- **Spam prevention:** No notifications for old emails on first authentication.

---

## 🚀 Getting Started

1. **Start the bot:**  
   Send `/start` to begin authentication.
2. **Authenticate Gmail:**  
   Follow the link, authorize, and send `/authCode <code>` with your code.
3. **Add more accounts:**  
   Use `/addaccount` to link more Gmail accounts.
4. **Manage filters:**  
   - Add sender to blacklist: `/blacklistsender <email>`
   - Add sender to whitelist: `/whitelistsender <email>`
   - Add subject to blacklist: `/blacklistsubject <subject>`
   - Add subject to whitelist: `/whitelistsubject <subject>`
   - Remove from lists:  
     `/blacklistsenderremove <email>`, `/whitelistsenderremove <email>`, etc.
5. **Set notification interval:**  
   `/setinterval <seconds>`

---

## 🛠 Example

<p align="center">
  <img src="https://github.com/user-attachments/assets/63abac28-f052-418c-907e-ca1a629ce594" alt="Bot usage screenshot" width="500">
</p>

---

## 🗺 Planned Features

- Reply to emails directly from Telegram
- Send new emails from the bot

---

> **Note:**  
> This bot is intended for personal/local use.  
> **Never share your `.env` or `user_data.pkl` files.**

---
