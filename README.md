<div align="center">

<img src="https://giffiles.alphacoders.com/349/34964.gif" alt="Yui" width="40%" />

# 🎸 Yui Discord Bot

</div>

<!-- Language Switcher Bar -->
<p align="center">
  <a href="#-tiếng-việt"><b>Tiếng Việt</b></a> •
  <a href="#-english"><b>English</b></a>
</p>

<!-- Badges -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/discord.py-v2.x-5865F2.svg?style=flat-square&logo=discord&logoColor=white" alt="discord.py" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker&logoColor=white" alt="Docker Ready" />
  <img src="https://img.shields.io/badge/yt--dlp-SoundCloud-FF5500.svg?style=flat-square&logo=soundcloud&logoColor=white" alt="yt-dlp SoundCloud" />
  <a href="https://discord.gg/ErGMVF77Pc"><img src="https://img.shields.io/badge/Support_Server-Join_Discord-5865F2.svg?style=flat-square&logo=discord&logoColor=white" alt="Discord Support Server" /></a>
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License" />
</p>

---

<p align="center">
  <b>Một Discord bot phong cách Yui Hirasawa (K-ON!): phát nhạc SoundCloud, chơi nối từ tiếng Việt, thông báo ra vào voice và xem avatar.</b>
</p>

</div>

---

<a name="-tiếng-việt"></a>
## Tiếng Việt

### 📑 Mục Lục

1. [Tổng quan](#tong-quan)
2. [Tính năng nổi bật](#tinh-nang-noi-bat)
3. [Yêu cầu hệ thống](#yeu-cau-he-thong)
4. [Hướng dẫn cài đặt & Triển khai](#cai-dat-trien-khai)
5. [Danh sách lệnh (Commands)](#danh-sach-lenh)
6. [Triển khai 24/7 miễn phí (Render)](#trien-khai-24-7)
7. [Xử lý sự cố (Troubleshooting)](#xu-ly-su-co)
8. [Công nghệ sử dụng](#cong-nghe-su-dung)
9. [Giấy phép & Bản quyền](#giay-phep-ban-quyen)

---

<a id="tong-quan"></a>
### 🌟 Tổng quan

**Yui** là một Discord bot self-hosted lấy cảm hứng từ nhân vật **Yui Hirasawa** trong anime *K-ON!*, phản hồi hoàn toàn bằng tiếng Việt với văn phong dễ thương, thân thiện. Bot chạy gọn trong **một container duy nhất**, phù hợp để tự host trên VPS nhẹ hoặc các nền tảng miễn phí như Render.

> ⚠️ **Lưu ý về phương thức điều khiển:** Bot sử dụng hoàn toàn **Slash Commands (`/`)** của Discord, không dùng lệnh tiền tố (prefix) truyền thống — trừ tính năng nối từ, vốn đọc trực tiếp tin nhắn thường trong kênh đang chơi.

---

<a id="tinh-nang-noi-bat"></a>
### ✨ Tính năng nổi bật

* **🎵 Phát nhạc từ SoundCloud:** Tìm kiếm theo từ khóa hoặc dán link SoundCloud trực tiếp, phát qua `yt-dlp` + `FFmpeg`, có hàng đợi, shuffle và 2 chế độ lặp (1 bài / toàn bộ hàng đợi).
* **🔤 Nối từ tiếng Việt:** Trò chơi nối từ ngay trong kênh chat, có kiểm tra từ điển, chống lặp từ trong 50 lượt gần nhất, và không cho một người nối liên tiếp 2 lượt.
* **💰 Hệ thống Yui Coin:** Điểm danh nhận thưởng mỗi ngày (`/daily`), xem ví (`/cash`), bảng xếp hạng (`/top`) và chuyển tiền cho nhau (`/give`), có giới hạn chống lạm dụng.
* **🎲 Minigame cá cược:** Dò Mìn (`/mine`) và Tung đồng xu (`/coinflip`) — cược Yui Coin để nhân thưởng.
* **🛠️ Công cụ tiện ích (Độc quyền):** Tự động cày nhiệm vụ Discord (`/quest`), cày huy hiệu Games Played (`/badge`), và đổi nhà HypeSquad nhanh chóng (`/hypesquad`).
* **🖼️ Avatar & Banner:** `/avatar` và `/banner` xem ảnh đại diện/banner cá nhân lẫn ảnh riêng theo từng server (nếu người dùng có đặt).
* **🤗 Tương tác vui:** Loạt lệnh tương tác kiểu "anime" (`/hug`, `/kiss`, `/pat`, `/slap`, `/dance`...) và các máy "soi" troll bạn bè (`/soichieucao`, `/soiiq`, `/soimayman`...).
* **🔔 Thông báo ra/vào voice:** Lệnh `/thongbao` (cần quyền Manage Server) cho phép bật/tắt thông báo cho toàn server khi có người vào/ra kênh thoại, với tin nhắn ngẫu nhiên theo phong cách Yui.
* **📖 Menu lệnh:** `/help` mở menu chọn danh mục để tra cứu lệnh ngay trong Discord.
* **Kiến trúc nhẹ:** Không cần Lavalink hay database ngoài — chỉ một tiến trình Python duy nhất, dễ triển khai và bảo trì.

---

<a id="yeu-cau-he-thong"></a>
### 📦 Yêu cầu hệ thống

- **Python** `>= 3.11` (nếu chạy trực tiếp) hoặc **Docker** `>= 20.10`.
- **FFmpeg** đã cài trong hệ thống (nếu không dùng Docker).
- **Discord Bot Token:** Tạo tại [Discord Developer Portal](https://discord.com/developers/applications) *(cần bật **Message Content Intent**)*.

---

<a id="cai-dat-trien-khai"></a>
### 🚀 Hướng dẫn cài đặt & Triển khai

#### 1. Clone mã nguồn
```bash
git clone https://github.com/2amkeyl/yui-bot.git
cd yui-bot
```

#### 2. Thiết lập biến môi trường
Tạo file `.env` ở thư mục gốc của repo với nội dung:
```env
BOT_TOKEN=your_discord_bot_token_here
```

> 🔒 **Cảnh báo bảo mật:** Tuyệt đối không đẩy file `.env` lên GitHub hoặc chia sẻ token bot cho bất kỳ ai. Repo hiện **chưa có file `.gitignore`**, nên hãy tự tạo một file `.gitignore` chứa dòng `.env` trước khi commit, để tránh lỡ tay đẩy token lên GitHub.

#### 3a. Chạy bằng Docker (khuyên dùng)
```bash
docker build -t yui-bot .
docker run -d --name yui-bot --env-file .env yui-bot
```

#### 3b. Hoặc chạy trực tiếp bằng Python
```bash
pip install -r requirements.txt
python main.py
```

---

<a id="danh-sach-lenh"></a>
### 🕹️ Danh sách lệnh (Commands)

**🎵 Nhạc**

| Lệnh | Mô tả |
| :--- | :--- |
| `/play <từ khóa / link SoundCloud>` | Tìm và phát nhạc từ SoundCloud, hoặc nạp vào hàng đợi nếu đang phát. |
| `/skip` | Bỏ qua bài đang phát, chuyển sang bài tiếp theo. |
| `/pause` | Tạm dừng phát nhạc. |
| `/resume` | Tiếp tục phát bài đang tạm dừng. |
| `/stop` | Dừng hẳn, xoá hàng chờ và rời voice. |
| `/queue` | Xem danh sách hàng chờ hiện tại. |
| `/nowplaying` | Xem thông tin bài đang phát. |
| `/loop [track \| all \| off]` | Lặp 1 bài / lặp cả hàng đợi / tắt lặp. |
| `/shuffle` | Xáo trộn ngẫu nhiên hàng chờ. |
| `/remove <số thứ tự>` | Xoá 1 bài khỏi hàng chờ theo số thứ tự trong `/queue`. |

**🔤 Nối từ**

| Lệnh | Mô tả |
| :--- | :--- |
| `/noitu` | Bắt đầu ván nối từ trong kênh hiện tại. |
| `/noitu_stop` | Dừng ván nối từ đang diễn ra. |

**💰 Kinh tế (Yui Coin)**

| Lệnh | Mô tả |
| :--- | :--- |
| `/daily` | Điểm danh nhận Yui Coin miễn phí mỗi ngày. |
| `/cash [thành viên]` | Xem số dư ví và số trận thắng nối từ (mặc định là chính bạn). |
| `/top <coins \| wins>` | Xem bảng xếp hạng đại gia Yui Coin hoặc cao thủ nối từ. |
| `/give <thành viên> <số tiền>` | Chuyển Yui Coin cho người khác (tối đa 5,000,000/ngày, gõ `all` để chuyển hết ví). |

**🖼️ Hồ sơ**

| Lệnh | Mô tả |
| :--- | :--- |
| `/avatar [thành viên]` | Xem avatar cá nhân và avatar riêng theo server (nếu có) của một người. |
| `/banner [thành viên]` | Xem banner cá nhân và banner riêng theo server (nếu có) của một người. |

**🎲 Minigame**

| Lệnh | Mô tả |
| :--- | :--- |
| `/mine <cược> <số mìn>` | Dò Mìn — mở ô an toàn để nhân thưởng, trúng mìn là mất cược. |
| `/coinflip <cược> <mặt>` | Tung đồng xu, đoán đúng để x2 tiền cược. |

**🛠️ Công cụ tiện ích (Dành riêng cho Server Hỗ trợ)**

| Lệnh | Mô tả |
| :--- | :--- |
| `/quest <token> <mode>` | Tự động cày mọi loại Discord Quest với tuỳ chọn chạy Siêu tốc hoặc An toàn. |
| `/badge [games_count] [hours_per_game]` | Cày giờ chơi để lấy huy hiệu Games Played (Hỗ trợ Bypass Fingerprint). |
| `/hypesquad <token> <house>` | Gán hoặc thay đổi huy hiệu nhà HypeSquad nhanh chóng. |

**🤗 Tương tác vui**

| Lệnh | Mô tả |
| :--- | :--- |
| `/hug`, `/cuddle`, `/kiss`, `/pat`, `/slap`, `/kill`, `/bully`, `/bonk`, `/poke`, `/highfive`, `/handhold`, `/tickle`, `/cry`, `/dance`, `/lick`, `/nom`, `/stare`, `/greet`, `/punch`, `/pats`, `/snuggle` | Gửi GIF tương tác kiểu anime tới một thành viên khác. |
| `/soichieucao`, `/soidaden`, `/soideptrai`, `/soidodethuong`, `/soidowibu`, `/soiiq`, `/soimayman`, `/soicu` | Loạt "máy soi" đo chỉ số ngẫu nhiên troll bạn bè cho vui, không mang tính nghiêm túc. |
| `/hom-nay-an-gi` | Gợi ý ngẫu nhiên "hôm nay ăn gì" cho người lười nghĩ. |

**🔔 Thông báo voice & trợ giúp**

| Lệnh | Mô tả |
| :--- | :--- |
| `/thongbao <on \| off>` | Bật/tắt thông báo ra vào kênh voice cho toàn server (cần quyền **Manage Server**). |
| `/help` | Mở menu chọn danh mục để xem toàn bộ lệnh của Yui. |

---

<a id="trien-khai-24-7"></a>
### ☁️ Triển khai 24/7 miễn phí (Render)

Bot đã tích hợp sẵn một server Flask nhỏ (`keep_alive()`) lắng nghe ở cổng `8080`, giúp các dịch vụ hosting miễn phí như [Render](https://render.com/) (Web Service) không tắt bot do không có traffic HTTP. Khi deploy trên Render:

1. Chọn **Web Service**, trỏ tới repo của bạn.
2. Build Command: để trống nếu dùng Docker (Render tự nhận `Dockerfile`).
3. Thêm biến môi trường `BOT_TOKEN` trong phần **Environment**.
4. (Khuyến nghị) Dùng một dịch vụ ping định kỳ như [UptimeRobot](https://uptimerobot.com/) trỏ vào URL Render để tránh bị sleep ở gói Free.

---

<a id="xu-ly-su-co"></a>
### 🛠️ Xử lý sự cố (Troubleshooting)

<details>
<summary><b>1. Bot vào voice channel nhưng không phát tiếng rồi tự thoát?</b></summary>

- Kiểm tra `FFmpeg` và `PyNaCl` đã được cài đặt đúng (Docker image đã bao gồm sẵn `ffmpeg`).
- Đảm bảo bot có quyền `Connect` và `Speak` trong server Discord.
</details>

<details>
<summary><b>2. Lệnh Slash (`/`) không hiện ra trong Discord?</b></summary>

- Slash Command cần tối đa vài phút để đồng bộ toàn cục sau lần khởi động đầu tiên — hãy đợi hoặc thử `/` lại sau khi bot báo "Đã đồng bộ Slash Command" trong log.
- Kiểm tra bot đã được mời vào server với scope `applications.commands`.
</details>

<details>
<summary><b>3. Tìm/phát nhạc bị lỗi hoặc không ra kết quả?</b></summary>

- `/play` chỉ tìm kiếm và phát từ **SoundCloud**; hãy thử dán trực tiếp link bài hát SoundCloud nếu tìm theo từ khóa không ra kết quả mong muốn.
</details>

---

<a id="cong-nghe-su-dung"></a>
### 🧰 Công nghệ sử dụng

* **Core Runtime:** [Python 3.11+](https://www.python.org/)
* **Discord API Wrapper:** [discord.py v2.x](https://github.com/Rapptz/discord.py) (Slash Commands)
* **Trích xuất & phát audio:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) & [FFmpeg](https://ffmpeg.org/)
* **Keep-alive server:** [Flask](https://flask.palletsprojects.com/)
* **Containerization:** [Docker](https://www.docker.com/)

---

<a id="giay-phep-ban-quyen"></a>
### 📄 Giấy phép & Bản quyền

Dự án được cấp phép theo **MIT License**. Xem chi tiết tại file [LICENSE](LICENSE).

*Dự án được chia sẻ với mục đích học tập và sử dụng cá nhân phi thương mại. Vui lòng tôn trọng [Điều khoản dịch vụ của SoundCloud](https://soundcloud.com/terms-of-use) và [Discord](https://discord.com/terms).*

---

<div align="center">
  <p>Được thực hiện bởi <b>Keyl</b> • Tham gia <a href="https://discord.gg/ErGMVF77Pc"><b>Discord Support Server</b></a> 🎸</p>
</div>

---
---

<a name="-english"></a>
## English

### 📑 Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Prerequisites](#prerequisites)
4. [Installation & Deployment](#installation)
5. [Command Reference](#commands)
6. [Free 24/7 Hosting (Render)](#hosting)
7. [Troubleshooting](#troubleshooting)
8. [Tech Stack](#tech-stack)
9. [License & Disclaimer](#license)

---

<a id="overview"></a>
### 🌟 Overview

**Yui** is a self-hosted Discord bot inspired by **Yui Hirasawa** from the anime *K-ON!*, responding entirely in friendly, casual Vietnamese. It runs as a **single lightweight container** (no auxiliary services like Lavalink required), making it easy to self-host on a small VPS or a free platform such as Render.

> ⚠️ **Control Mode:** The bot uses Discord's **Slash Commands (`/`)** exclusively — except for the word-chain game, which reads plain messages directly in the active channel.

---

<a id="key-features"></a>
### ✨ Key Features

* **🎵 SoundCloud Music Playback:** Search by keyword or paste a SoundCloud link directly, streamed via `yt-dlp` + `FFmpeg`, with a queue, shuffle, and two loop modes (single track / entire queue).
* **🔤 Vietnamese Word-Chain Game (Nối từ):** A dictionary-checked word-chaining game played directly in chat, with anti-repeat protection over the last 50 turns and a rule preventing the same player from chaining twice in a row.
* **💰 Yui Coin Economy:** Daily rewards (`/daily`), wallet lookup (`/cash`), leaderboards (`/top`), and peer-to-peer transfers (`/give`) with anti-abuse limits.
* **🎲 Betting Minigames:** Minesweeper (`/mine`) and Coinflip (`/coinflip`) — wager Yui Coin for a chance to multiply your winnings.
* **🛠️ Exclusive Utilities:** Automated Discord Quest completion (`/quest`), playtime badge spoofing (`/badge`), and HypeSquad house switcher (`/hypesquad`).
* **🖼️ Avatar & Banner Lookup:** `/avatar` and `/banner` show a member's personal image plus their per-server version, if they've set one.
* **🤗 Fun Interactions:** A set of anime-style interaction commands (`/hug`, `/kiss`, `/pat`, `/slap`, `/dance`, ...) plus a bunch of joke "scanner" commands for roasting friends (`/soichieucao`, `/soiiq`, `/soimayman`, ...).
* **🔔 Voice Join/Leave Notifications:** `/thongbao` (requires the Manage Server permission) toggles server-wide announcements when members join or leave voice channels, with randomized Yui-themed messages.
* **📖 In-Discord Command Menu:** `/help` opens a category picker to browse every command without leaving Discord.
* **🪶 Lightweight Architecture:** No Lavalink or external database needed — a single Python process that's easy to deploy and maintain.

---

<a id="prerequisites"></a>
### 📦 Prerequisites

* **Python** `>= 3.11` (for running directly) or **Docker** `>= 20.10`.
* **FFmpeg** installed on the host (not needed if using Docker).
* **Discord Bot Token** from the [Discord Developer Portal](https://discord.com/developers/applications) *(**Message Content Intent** must be enabled)*.

---

<a id="installation"></a>
### 🚀 Installation & Deployment

#### 1. Clone the Repository
```bash
git clone https://github.com/2amkeyl/yui-bot.git
cd yui-bot
```

#### 2. Configure Environment Variables
Create a `.env` file in the repo root with:
```env
BOT_TOKEN=your_discord_bot_token_here
```

> 🔒 **Security Warning:** Never commit your `.env` file to GitHub or share your bot token with anyone. This repo currently has **no `.gitignore`** — create one containing `.env` before your first commit to avoid accidentally pushing your token.

#### 3a. Run with Docker (recommended)
```bash
docker build -t yui-bot .
docker run -d --name yui-bot --env-file .env yui-bot
```

#### 3b. Or run directly with Python
```bash
pip install -r requirements.txt
python main.py
```

---

<a id="commands"></a>
### 🕹️ Command Reference

**🎵 Music**

| Command | Description |
| :--- | :--- |
| `/play <query / SoundCloud link>` | Searches and streams from SoundCloud, or enqueues if something is already playing. |
| `/skip` | Skips the current track. |
| `/pause` | Pauses playback. |
| `/resume` | Resumes a paused track. |
| `/stop` | Stops playback, clears the queue, and leaves the voice channel. |
| `/queue` | Shows the current playback queue. |
| `/nowplaying` | Shows details of the currently playing track. |
| `/loop [track \| all \| off]` | Loops the current track / the whole queue / disables looping. |
| `/shuffle` | Randomizes the queue order. |
| `/remove <index>` | Removes a track from the queue by its position in `/queue`. |

**🔤 Word Chain**

| Command | Description |
| :--- | :--- |
| `/noitu` | Starts a word-chain round in the current channel. |
| `/noitu_stop` | Stops the ongoing word-chain round. |

**💰 Economy (Yui Coin)**

| Command | Description |
| :--- | :--- |
| `/daily` | Claim your free daily Yui Coin reward. |
| `/cash [member]` | Shows wallet balance and word-chain win count (defaults to yourself). |
| `/top <coins \| wins>` | Shows the Yui Coin or word-chain leaderboard. |
| `/give <member> <amount>` | Transfers Yui Coin to another member (max 5,000,000/day, type `all` to send your full balance). |

**🖼️ Profile**

| Command | Description |
| :--- | :--- |
| `/avatar [member]` | Shows a member's personal avatar and server-specific avatar (if set). |
| `/banner [member]` | Shows a member's personal banner and server-specific banner (if set). |

**🎲 Minigames**

| Command | Description |
| :--- | :--- |
| `/mine <bet> <mine count>` | Minesweeper — reveal safe tiles to multiply your bet, hitting a mine loses it. |
| `/coinflip <bet> <side>` | Flip a coin and call it right to double your bet. |

**🛠️ Utilities (Exclusive to Support Server)**

| Command | Description |
| :--- | :--- |
| `/quest <token> <mode>` | Automatically completes Discord Quests (supports Fast or Safe modes). |
| `/badge [games_count] [hours_per_game]` | Boosts playtime for Games Played badges (supports Fingerprint Bypass). |
| `/hypesquad <token> <house>` | Instantly assigns or changes your HypeSquad house. |

**🤗 Fun Interactions**

| Command | Description |
| :--- | :--- |
| `/hug`, `/cuddle`, `/kiss`, `/pat`, `/slap`, `/kill`, `/bully`, `/bonk`, `/poke`, `/highfive`, `/handhold`, `/tickle`, `/cry`, `/dance`, `/lick`, `/nom`, `/stare`, `/greet`, `/punch`, `/pats`, `/snuggle` | Sends an anime-style reaction GIF targeting another member. |
| `/soichieucao`, `/soidaden`, `/soideptrai`, `/soidodethuong`, `/soidowibu`, `/soiiq`, `/soimayman`, `/soicu` | A set of joke "scanner" commands that generate random, non-serious stats for roasting friends. |
| `/hom-nay-an-gi` | Randomly suggests what to eat today. |

**🔔 Voice Notifications & Help**

| Command | Description |
| :--- | :--- |
| `/thongbao <on \| off>` | Toggles server-wide voice join/leave notifications (requires **Manage Server** permission). |
| `/help` | Opens a category picker covering every command Yui supports. |

---

<a id="hosting"></a>
### ☁️ Free 24/7 Hosting (Render)

The bot ships with a small built-in Flask server (`keep_alive()`) listening on port `8080`, which lets free hosts like [Render](https://render.com/) (Web Service) keep the bot alive by serving HTTP traffic. When deploying on Render:

1. Create a **Web Service** pointed at your repository.
2. Leave the Build Command blank — Render auto-detects the `Dockerfile`.
3. Add the `BOT_TOKEN` environment variable under **Environment**.
4. (Recommended) Use a periodic ping service like [UptimeRobot](https://uptimerobot.com/) against the Render URL to prevent the Free tier from sleeping.

---

<a id="troubleshooting"></a>
### 🛠️ Troubleshooting

<details>
<summary><b>1. Bot joins the voice channel but plays no sound and leaves?</b></summary>

- Verify `FFmpeg` and `PyNaCl` are correctly installed (the Docker image already includes `ffmpeg`).
- Ensure the bot has `Connect` and `Speak` permissions in the server.
</details>

<details>
<summary><b>2. Slash commands (`/`) don't show up in Discord?</b></summary>

- Global slash command sync can take a few minutes after the first startup — wait, or retry after the bot logs "Đã đồng bộ Slash Command" (sync successful).
- Make sure the bot was invited with the `applications.commands` scope.
</details>

<details>
<summary><b>3. Search or playback fails / returns no results?</b></summary>

- `/play` only searches and streams from **SoundCloud** — try pasting a direct SoundCloud track link if keyword search doesn't return what you're looking for.
</details>

---

<a id="tech-stack"></a>
### 🧰 Tech Stack

* **Core Runtime:** [Python 3.11+](https://www.python.org/)
* **Discord API Wrapper:** [discord.py v2.x](https://github.com/Rapptz/discord.py) (Slash Commands)
* **Audio Extraction & Streaming:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) & [FFmpeg](https://ffmpeg.org/)
* **Keep-alive Server:** [Flask](https://flask.palletsprojects.com/)
* **Containerization:** [Docker](https://www.docker.com/)

---

<a id="license"></a>
### 📄 License & Disclaimer

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

*This project is shared for educational and personal, non-commercial use. Please respect [SoundCloud's Terms of Use](https://soundcloud.com/terms-of-use) and [Discord's Terms of Service](https://discord.com/terms).*

---

<div align="center">
  <p>Made by <b>Keyl</b> • Join the <a href="https://discord.gg/ErGMVF77Pc"><b>Discord Support Server</b></a> 🎸</p>
</div>
