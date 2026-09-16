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
  <a href="https://discord.gg/ErGMVF77Pc"><img src="https://img.shields.io/badge/Support_Server-Join_Discord-5865F2.svg?style=flat-square&logo=discord&logoColor=white" alt="Discord Support Server" /></a>
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License" />
</p>

---

<p align="center">
  <b>Một Discord bot phong cách Yui Hirasawa (K-ON!)</b>
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
6. [Xử lý sự cố (Troubleshooting)](#xu-ly-su-co)
7. [Công nghệ sử dụng](#cong-nghe-su-dung)
8. [Giấy phép & Bản quyền](#giay-phep-ban-quyen)

---

<a id="tong-quan"></a>
### 🌟 Tổng quan

**Yui** là một Discord bot self-hosted lấy cảm hứng từ nhân vật **Yui Hirasawa** trong anime *K-ON!*, phản hồi hoàn toàn bằng tiếng Việt với văn phong dễ thương, thân thiện.

> ⚠️ **Lưu ý về phương thức điều khiển:** Bot sử dụng hoàn toàn **Slash Commands (`/`)** của Discord, không dùng lệnh tiền tố (prefix) truyền thống — trừ tính năng nối từ, vốn đọc trực tiếp tin nhắn thường trong kênh đang chơi.

---

<a id="tinh-nang-noi-bat"></a>
### ✨ Tính năng nổi bật

* **🎵 Phát nhạc từ YouTube & SoundCloud:** Tìm kiếm theo từ khóa hoặc dán link trực tiếp, phát qua `yt-dlp` + `FFmpeg`, có hàng đợi, shuffle và 2 chế độ lặp (1 bài / toàn bộ hàng đợi).
* **🎨 Quản lý Role riêng cho thành viên (`RoleSetupCog`):** Hệ thống tạo & chỉnh sửa tên, màu sắc (đơn sắc / Gradient 2 màu), icon role cá nhân bằng UI Modal trực quan.
* **🔤 Nối từ tiếng Việt:** Trò chơi nối từ ngay trong kênh chat, có kiểm tra từ điển, chống lặp từ trong 50 lượt gần nhất, và không cho một người nối liên tiếp 2 lượt.
* **💰 Hệ thống Yui Coin:** Điểm danh nhận thưởng mỗi ngày (`/daily`), xem ví (`/cash`), bảng xếp hạng (`/top`) và chuyển tiền cho nhau (`/give`), có giới hạn chống lạm dụng.
* **🎲 Minigame cá cược:** Dò Mìn (`/mine`) và Tung đồng xu (`/coinflip`) — cược Yui Coin để nhân thưởng.
* **🛠️ Công cụ tiện ích (Độc quyền):** Tự động cày nhiệm vụ Discord (`/quest`), cày huy hiệu Game Variety & Play Time (`/badge`), và đổi nhà HypeSquad nhanh chóng (`/hypesquad`).
* **🖼️ Avatar & Banner:** `/avatar` và `/banner` xem ảnh đại diện/banner cá nhân lẫn ảnh riêng theo từng server (nếu người dùng có đặt).
* **🤗 Tương tác vui:** Loạt lệnh tương tác kiểu "anime" (`/hug`, `/kiss`, `/pat`, `/slap`, `/dance`...) và các máy "soi" troll bạn bè (`/soichieucao`, `/soiiq`, `/soimayman`...).
* **🔔 Thông báo ra/vào voice:** Lệnh `/thongbao` (cần quyền Manage Server) cho phép bật/tắt thông báo cho toàn server khi có người vào/ra kênh thoại, với tin nhắn ngẫu nhiên theo phong cách Yui.
* **📖 Menu lệnh:** `/help` mở menu chọn danh mục để tra cứu lệnh ngay trong Discord.

---

<a id="yeu-cau-he-thong"></a>
### 📦 Yêu cầu hệ thống

- **Python** `>= 3.11`.
- **FFmpeg** đã cài trong hệ thống.
- **Discord Bot Token:** Tạo tại [Discord Developer Portal](https://discord.com/developers/applications) *(Cần bật **Message Content Intent** và **Server Members Intent**)*.

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

#### 3. Chạy trực tiếp bằng Python
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
| `/play <từ khóa / link>` | Tìm và phát nhạc từ YouTube hoặc SoundCloud, hoặc nạp vào hàng đợi nếu đang phát. |
| `/skip` | Bỏ qua bài đang phát, chuyển sang bài tiếp theo. |
| `/pause` | Tạm dừng phát nhạc. |
| `/resume` | Tiếp tục phát bài đang tạm dừng. |
| `/stop` | Dừng hẳn, xoá hàng chờ và rời voice. |
| `/queue` | Xem danh sách hàng chờ hiện tại. |
| `/nowplaying` | Xem thông tin bài đang phát. |
| `/loop` | Lặp 1 bài. |
| `/loop [all \| off]` | Lặp cả hàng đợi / tắt lặp. |
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
| `/give <thành viên> <số tiền>` | Chuyển Yui Coin cho người khác. |

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

**🛠️ Công cụ tiện ích độc quyền**

| Lệnh | Mô tả |
| :--- | :--- |
| `/quest <token> <mode>` | Tự động cày mọi loại Discord Quest với tuỳ chọn chạy Siêu tốc hoặc An toàn. |
| `/badge <số game> <số giờ mỗi game>` | Tự động cày huy hiệu Game Variaty & Play Time với tuỳ chọn số game và số giờ tuỳ chỉnh. |
| `/hypesquad <token> <house>` | Gán hoặc thay đổi huy hiệu nhà HypeSquad nhanh chóng. |

**🤗 Tương tác vui**

| Lệnh | Mô tả |
| :--- | :--- |
| `/hug`, `/cuddle`, `/kiss`, `/pat`, `/slap`, `/kill`, `/poke`, `/highfive`, `/handhold`, `/tickle`, `/cry`, `/dance`, `/nom`, `/punch`, `/snuggle`, `/stare` | Gửi GIF tương tác kiểu anime tới một thành viên khác. |
| `/soichieucao`, `/soidaden`, `/soideptrai`, `/soidodethuong`, `/soidowibu`, `/soiiq`, `/soimayman`, `/soicu` | Loạt "máy soi" đo chỉ số ngẫu nhiên troll bạn bè cho vui. |
| `/hom-nay-an-gi` | Gợi ý ngẫu nhiên "hôm nay ăn gì" cho người lười nghĩ. |

**🔔 Thông báo voice & trợ giúp**

| Lệnh | Mô tả |
| :--- | :--- |
| `/thongbao <on \| off>` | Bật/tắt thông báo ra vào kênh voice cho toàn server (cần quyền **Manage Server**). |
| `/help` | Mở menu chọn danh mục để xem toàn bộ lệnh của Yui. |

---

<a id="xu-ly-su-co"></a>
### 🛠️ Xử lý sự cố (Troubleshooting)

<details>
<summary><b>1. Bot vào voice channel nhưng không phát tiếng rồi tự thoát?</b></summary>

- Kiểm tra `FFmpeg` và `PyNaCl` đã được cài đặt đúng.
- Đảm bảo bot có quyền `Connect` và `Speak` trong server Discord.
</details>

<details>
<summary><b>2. Lệnh Slash (`/`) không hiện ra trong Discord?</b></summary>

- Slash Command cần tối đa vài phút để đồng bộ toàn cục sau lần khởi động đầu tiên — hãy đợi hoặc thử `/` lại sau khi bot báo "Đã đồng bộ Slash Command" trong log.
- Kiểm tra bot đã được mời vào server với scope `applications.commands`.
</details>

---

<a id="cong-nghe-su-dung"></a>
### 🧰 Công nghệ sử dụng

* **Core Runtime:** [Python 3.11+](https://www.python.org/)
* **Discord API Wrapper:** [discord.py v2.x](https://github.com/Rapptz/discord.py) (Slash Commands)
* **Trích xuất & phát audio:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) & [FFmpeg](https://ffmpeg.org/)

---

<a id="giay-phep-ban-quyen"></a>
### 📄 Giấy phép & Bản quyền

Dự án được cấp phép theo **MIT License**. Xem chi tiết tại file [LICENSE](LICENSE).

*Dự án được chia sẻ với mục đích học tập và sử dụng cá nhân phi thương mại. Vui lòng tôn trọng [Discord](https://discord.com/terms).*

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
6. [Troubleshooting](#troubleshooting)
7. [Tech Stack](#tech-stack)
8. [License & Disclaimer](#license)

---

<a id="overview"></a>
### 🌟 Overview

**Yui** is a self-hosted Discord bot inspired by **Yui Hirasawa** from the anime *K-ON!*, responding entirely in friendly, casual Vietnamese.

> ⚠️ **Control Mode:** The bot uses Discord's **Slash Commands (`/`)** exclusively — except for the word-chain game, which reads plain messages directly in the active channel.

---

<a id="key-features"></a>
### ✨ Key Features

* **🎵 YouTube & SoundCloud Music Playback:** Search by keyword or paste a link directly, streamed via `yt-dlp` + `FFmpeg`, with a queue, shuffle, and two loop modes (single track / entire queue).
* **🎨 Custom Role Management (`RoleSetupCog`):** Full custom role manager allowing boosted/donated members to edit role name, color (solid / 2-color Gradient), and custom icon via Modals.
* **🔤 Vietnamese Word-Chain Game:** A dictionary-checked word-chaining game played directly in chat, with anti-repeat protection over the last 50 turns.
* **💰 Yui Coin Economy:** Daily rewards (`/daily`), wallet lookup (`/cash`), leaderboards (`/top`), and peer-to-peer transfers (`/give`).
* **🎲 Betting Minigames:** Minesweeper (`/mine`) and Coinflip (`/coinflip`) — wager Yui Coin for a chance to multiply your winnings.
* **🛠️ Exclusive Utilities:** Automated Discord Quest completion (`/quest`) and HypeSquad house switcher (`/hypesquad`).
* **🖼️ Avatar & Banner Lookup:** `/avatar` and `/banner` show personal and per-server avatars/banners.
* **🤗 Fun Interactions:** Anime-style reaction commands (`/hug`, `/kiss`, `/pat`, `/slap`, `/dance`, ...) and fun joke scanners.
* **🔔 Voice Join/Leave Notifications:** `/thongbao` toggles server-wide voice activity announcements.
* **📖 In-Discord Command Menu:** `/help` opens an interactive category picker.

---

<a id="prerequisites"></a>
### 📦 Prerequisites

* **Python** `>= 3.11`.
* **FFmpeg** installed on the host.
* **Discord Bot Token** from [Discord Developer Portal](https://discord.com/developers/applications) *(**Message Content Intent** and **Server Members Intent** must be enabled)*.

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

#### 3. Run directly with Python
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
| `/play <query / link>` | Searches and streams from YouTube or SoundCloud. |
| `/skip` | Skips the current track. |
| `/pause` | Pauses playback. |
| `/resume` | Resumes a paused track. |
| `/stop` | Stops playback, clears the queue, and leaves voice. |
| `/queue` | Shows current queue. |
| `/nowplaying` | Shows details of the active track. |
| `/loop [track \| all \| off]` | Set loop mode. |
| `/shuffle` | Randomizes queue. |
| `/remove <index>` | Removes a track from queue by position. |

**🔤 Word Chain**

| Command | Description |
| :--- | :--- |
| `/noitu` | Starts a word-chain round. |
| `/noitu_stop` | Stops the word-chain round. |

**💰 Economy (Yui Coin)**

| Command | Description |
| :--- | :--- |
| `/daily` | Claim free daily Yui Coin reward. |
| `/cash [member]` | Shows wallet balance and win count. |
| `/top <coins \| wins>` | Shows economic leaderboards. |
| `/give <member> <amount>` | Transfers Yui Coin to another member. |

**🖼️ Profile**

| Command | Description |
| :--- | :--- |
| `/avatar [member]` | Shows global and server avatars. |
| `/banner [member]` | Shows global and server banners. |

**🎲 Minigames**

| Command | Description |
| :--- | :--- |
| `/mine <bet> <mine count>` | Minesweeper minigame. |
| `/coinflip <bet> <side>` | Coinflip minigame. |

**🛠️ Utilities**

| Command | Description |
| :--- | :--- |
| `/quest <token> <mode>` | Automated Discord Quest completion. |
| `/hypesquad <token> <house>` | Instantly updates HypeSquad house. |

**🤗 Fun Interactions**

| Command | Description |
| :--- | :--- |
| `/hug`, `/cuddle`, `/kiss`, `/pat`, `/slap`, `/kill`, `/poke`, `/highfive`, `/handhold`, `/tickle`, `/cry`, `/dance`, `/nom`, `/stare`, `/punch`, `/snuggle` | Anime interaction GIF. |
| `/soichieucao`, `/soidaden`, `/soideptrai`, `/soidodethuong`, `/soidowibu`, `/soiiq`, `/soimayman`, `/soicu` | Joke stat scanners. |
| `/hom-nay-an-gi` | Random food suggestions. |

**🔔 Voice Notifications & Help**

| Command | Description |
| :--- | :--- |
| `/thongbao <on \| off>` | Toggles voice join/leave announcements. |
| `/help` | Opens interactive command directory. |

---

<a id="troubleshooting"></a>
### 🛠️ Troubleshooting

<details>
<summary><b>1. Bot joins voice channel but plays no sound and leaves?</b></summary>

- Verify `FFmpeg` and `PyNaCl` are correctly installed.
- Ensure the bot has `Connect` and `Speak` permissions.
</details>

<details>
<summary><b>2. Slash commands (`/`) don't show up in Discord?</b></summary>

- Global slash command sync can take a few minutes after initial startup.
- Verify bot invite scope includes `applications.commands`.
</details>

---

<a id="tech-stack"></a>
### 🧰 Tech Stack

* **Core Runtime:** [Python 3.11+](https://www.python.org/)
* **Discord API Wrapper:** [discord.py v2.x](https://github.com/Rapptz/discord.py)
* **Audio Extraction & Streaming:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) & [FFmpeg](https://ffmpeg.org/)

---

<a id="license"></a>
### 📄 License & Disclaimer

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

*This project is shared for educational and personal, non-commercial use. Please respect [Discord's Terms of Service](https://discord.com/terms).*

---

<div align="center">
  <p>Made by <b>Keyl</b> • Join the <a href="https://discord.gg/ErGMVF77Pc"><b>Discord Support Server</b></a> 🎸</p>
</div>
