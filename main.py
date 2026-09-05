import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import asyncio
import random
import os
import requests
import re
import time
import unicodedata
import yt_dlp
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import json
import base64
import uuid
import contextvars

# Import file Cog bên ngoài
from fun_cog import FunCog

load_dotenv()

# ==============================================================================
# ── YUI — lấy cảm hứng từ Yui Hirasawa (K-ON!) ────────────────────────────────
# ==============================================================================

HEART = "<a:klg23:1535400172199350332>"
EMBED_COLOR = 0xffb6c1
ERROR_COLOR = 0xff6961
FOOTER_TEXT = "Yui Hirasawa • Câu lạc bộ Nhạc Nhẹ"
current_footer_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("current_footer_ctx", default=FOOTER_TEXT)

def set_footer_guild(guild: Optional[discord.Guild]):
    current_footer_ctx.set(f"Yui Hirasawa • {guild.name}" if guild else FOOTER_TEXT)

COIN_EMOJI = "<:klcow:1544278502654873630>"
COINFLIP_MAX_BET = 250_000
COINFLIP_SPIN_EMOJI = "<a:giphy:1544584832129048606>"
COINFLIP_HEAD_EMOJI = "<:headkl:1544584406596063312>"
COINFLIP_TAIL_EMOJI = "<:tailkl:1544584549793534004>"
COINFLIP_SPIN_GIF_URL = "https://cdn.discordapp.com/emojis/1544584832129048606.gif?size=240&quality=lossless"
COINFLIP_HEAD_IMG_URL = "https://cdn.discordapp.com/emojis/1544584406596063312.png?size=240&quality=lossless"
COINFLIP_TAIL_IMG_URL = "https://cdn.discordapp.com/emojis/1544584549793534004.png?size=240&quality=lossless"
EMOJI_CORRECT = "<a:klquyt:1544282397040844850>"
EMOJI_INCORRECT = "<a:klwqquyt2:1544282445766066237>"
DB_FILE = "yui_db.json"
NOITU_WIN_REWARD = 10000
DAILY_REWARD_MIN, DAILY_REWARD_MAX = 1000, 2000
GIVE_DAILY_LIMIT = 5_000_000
MINES_TOTAL_CELLS = 9
MINES_MIN_MINES, MINES_MAX_MINES = 1, 8
MINES_MAX_BET = 250_000
MINES_HOUSE_EDGE = 0.94
GAME_COOLDOWN_SECONDS = 10.0
MUSIC_MAX_CONSECUTIVE_FAILURES = 3
MUSIC_MIN_PLAYBACK_SECONDS = 2.0

GIF_LIST = [
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExbTdibGIxbW82N2RleWpyYnk3aXRwaWY1NHRhamhmMHh6Y211bHZlcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/KTG2uX8CHJdIs/giphy.gif",
    "https://giffiles.alphacoders.com/215/215128.gif",
    "https://media.tenor.com/oQyiHReFBkAAAAAM/k-on-kon.gif",
    "https://i.kym-cdn.com/photos/images/original/002/161/679/2dd.gif",
    "https://media.tenor.com/TL2rTF5jqHoAAAAM/k-on-yui.gif",
]

def make_embed(description: str, *, title: str = None, color: int = EMBED_COLOR, gif: bool = False) -> discord.Embed:
    embed = discord.Embed(description=description, color=color)
    if title: embed.title = title
    embed.set_footer(text=current_footer_ctx.get())
    if gif: embed.set_thumbnail(url=random.choice(GIF_LIST))
    return embed

def fmt_time(ms: int) -> str:
    if not ms: return "??:??"
    total = ms // 1000
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def fmt_time_or_zero(ms: int) -> str:
    return "00:00" if not ms else fmt_time(ms)

def truncate_title(text: str, limit: int = 45) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"

class Colors:
    RESET  = "\033[0m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    DIM    = "\033[2m"

LOG_PROGRESS = True
DEBUG = True

class GlobalRateLimiter:
    def __init__(self, max_per_second: float = 35):
        self.max_per_second = max_per_second
        self._lock = asyncio.Lock()
        self._tokens = max_per_second
        self._last_refill = time.monotonic()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.max_per_second, self._tokens + elapsed * self.max_per_second)
            self._last_refill = now
            if self._tokens < 1:
                wait = (1 - self._tokens) / self.max_per_second
                await asyncio.sleep(wait)
                self._tokens = 0
                self._last_refill = time.monotonic()
            else:
                self._tokens -= 1

rate_limiter = GlobalRateLimiter()

async def safe_react(message: discord.Message, emoji: str):
    await rate_limiter.acquire()
    try: await message.add_reaction(emoji)
    except discord.HTTPException as e: log(f"Lỗi khi react tin nhắn: {e}", "warn")

async def safe_reply(message: discord.Message, content: str):
    await rate_limiter.acquire()
    try: await message.reply(content)
    except discord.HTTPException as e: log(f"Lỗi khi reply tin nhắn: {e}", "warn")

async def safe_send(channel, content: str = None, *, embed: discord.Embed = None):
    await rate_limiter.acquire()
    try: await channel.send(content=content, embed=embed)
    except discord.HTTPException as e: log(f"Lỗi khi gửi tin nhắn vào kênh: {e}", "warn")

def log(msg: str, level: str = "info"):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"info": f"{Colors.CYAN}[INFO]{Colors.RESET}", "ok": f"{Colors.GREEN}[  OK]{Colors.RESET}", "warn": f"{Colors.YELLOW}[WARN]{Colors.RESET}", "error": f"{Colors.RED}[ ERR]{Colors.RESET}", "debug": f"{Colors.DIM}[DBG ]{Colors.RESET}"}.get(level, f"[{level.upper()}]")
    if level == "debug" and not DEBUG: return
    print(f"{Colors.DIM}{ts}{Colors.RESET} {prefix} {msg}")

# ==============================================================================
# ── GAME NỐI TỪ ───────────────────────────────────────────────────────────────
# ==============================================================================

def norm(s: str) -> str: return unicodedata.normalize('NFC', s).strip().lower()

VIETNAMESE_WORDS, VIETNAMESE_WORDS_LIST, WORD_PREFIX_MAP = set(), [], {}
disabled_notify_channels, disabled_notify_guilds = set(), set()
games, game_locks = {}, {}

def get_game_lock(channel_id: int) -> asyncio.Lock:
    if channel_id not in game_locks: game_locks[channel_id] = asyncio.Lock()
    return game_locks[channel_id]

def get_vn_today() -> str:
    return datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")

def parse_bet_amount(text: str, balance: int, max_cap: Optional[int] = None) -> Optional[int]:
    text = text.strip().lower().replace(",", "").replace(".", "").replace(" ", "")
    if text in ("all", "allin", "tatca"):
        return balance if max_cap is None else min(balance, max_cap)
    mult = 1
    if text.endswith("k"): mult, text = 1_000, text[:-1]
    elif text.endswith("m"): mult, text = 1_000_000, text[:-1]
    try: value = float(text) * mult
    except ValueError: return None
    return int(value)

def _build_prefix_map(words_set: set) -> dict:
    pm = {}
    for w in words_set:
        w1, w2 = w.split(" ", 1)
        pm.setdefault(w1, set()).add(w2)
    return pm

def _use_fallback_words():
    global VIETNAMESE_WORDS, VIETNAMESE_WORDS_LIST, WORD_PREFIX_MAP
    VIETNAMESE_WORDS = {norm("bánh ngọt"), norm("trà chiều"), norm("âm nhạc")}
    VIETNAMESE_WORDS_LIST = list(VIETNAMESE_WORDS)
    WORD_PREFIX_MAP = _build_prefix_map(VIETNAMESE_WORDS)

def load_dictionary_sync():
    global VIETNAMESE_WORDS, VIETNAMESE_WORDS_LIST, WORD_PREFIX_MAP
    dict_file = "vietnamese_words.txt"
    if not os.path.exists(dict_file):
        headers = {"User-Agent": "Mozilla/5.0"}
        for url in ["https://raw.githubusercontent.com/duyet/vietnamese-wordlist/master/Viet74K.txt", "https://cdn.jsdelivr.net/gh/duyet/vietnamese-wordlist/Viet74K.txt"]:
            try:
                r = requests.get(url, headers=headers, timeout=20)
                if r.status_code == 200 and len(r.text) > 50000:
                    with open(dict_file, "w", encoding="utf-8") as f: f.write(r.text)
                    break
            except: continue
    try:
        ws = set()
        with open(dict_file, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower().replace("_", " ")
                parts = w.split()
                if len(parts) == 2 and parts[0].isalpha() and parts[1].isalpha(): ws.add(norm(w))
        if len(ws) > 1000:
            VIETNAMESE_WORDS, VIETNAMESE_WORDS_LIST = ws, list(ws)
            WORD_PREFIX_MAP = _build_prefix_map(ws)
        else: _use_fallback_words()
    except: _use_fallback_words()

def split_two_words(content: str):
    parts = re.sub(r'[^\w\s]', '', content).strip().split()
    if len(parts) != 2 or not (parts[0].isalpha() and parts[1].isalpha()): return None
    return norm(parts[0]), norm(parts[1])

def has_valid_next_word(end_word: str) -> bool: return bool(WORD_PREFIX_MAP.get(end_word))

def get_random_start_word() -> tuple:
    if not VIETNAMESE_WORDS_LIST: return ("âm", "nhạc")
    for _ in range(20):
        w1, w2 = random.choice(VIETNAMESE_WORDS_LIST).split()
        if has_valid_next_word(w2): return w1, w2
    return tuple(random.choice(VIETNAMESE_WORDS_LIST).split())

# ==============================================================================
# ── DÒ MÌN (MINES) ────────────────────────────────────────────────────────────
# ==============================================================================

active_mines_players = set()

def calc_mines_multiplier(total: int, mines: int, picks: int) -> float:
    safe = total - mines
    mult = MINES_HOUSE_EDGE
    for i in range(picks):
        mult *= (total - i) / (safe - i)
    return mult

class MineCellButton(discord.ui.Button):
    def __init__(self, index: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="❓", row=index // 3)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        await self.view.handle_pick(interaction, self.index)

class MineCashOutButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label="💰 Rút Tiền", row=3)

    async def callback(self, interaction: discord.Interaction):
        await self.view.handle_cashout(interaction)

class MinesView(discord.ui.View):
    def __init__(self, player: discord.abc.User, bet: int, mines: int):
        super().__init__(timeout=120)
        self.player, self.bet, self.mines_count = player, bet, mines
        self.total = MINES_TOTAL_CELLS
        self.safe_total = self.total - mines
        self.mine_positions = set(random.sample(range(self.total), mines))
        self.picks, self.finished, self.message = 0, False, None
        self.cell_buttons = []
        for i in range(self.total):
            btn = MineCellButton(i)
            self.cell_buttons.append(btn)
            self.add_item(btn)
        self.cashout_btn = MineCashOutButton()
        self.add_item(self.cashout_btn)

    def current_value(self) -> int:
        return 0 if self.picks == 0 else round(self.bet * calc_mines_multiplier(self.total, self.mines_count, self.picks))

    def current_mult(self) -> float:
        return 0.0 if self.picks == 0 else calc_mines_multiplier(self.total, self.mines_count, self.picks)

    def next_value(self) -> int:
        return round(self.bet * calc_mines_multiplier(self.total, self.mines_count, self.picks + 1))

    def next_mult(self) -> float:
        return calc_mines_multiplier(self.total, self.mines_count, self.picks + 1)

    def build_embed(self, *, status: str = "playing", win_amount: int = 0) -> discord.Embed:
        if status == "playing":
            desc, color = f"💣 {self.player.mention} đã bắt đầu ván Dò Mìn.", EMBED_COLOR
        elif status == "boom":
            desc, color = f"💥 {self.player.mention} đã đạp trúng mìn! Mất **{self.bet:,}** {COIN_EMOJI}", ERROR_COLOR
        elif status == "cashout":
            desc, color = f"{self.player.mention} đã rút tiền thành công! Nhận **{win_amount:,}** {COIN_EMOJI}", EMBED_COLOR
        elif status == "win":
            desc, color = f"🎉 {self.player.mention} đã dò sạch ô an toàn! Nhận **{win_amount:,}** {COIN_EMOJI}", EMBED_COLOR
        else:
            desc, color = f"⌛ Ván của {self.player.mention} đã hết giờ, Yui tự rút tiền giúp cậu rồi nha!", EMBED_COLOR

        embed = make_embed(desc, title=f"{HEART} Dò Mìn", color=color)
        embed.add_field(name="Bet", value=f"{self.bet:,} {COIN_EMOJI}", inline=True)
        embed.add_field(name="Mines", value=str(self.mines_count), inline=True)
        cash_val, cash_mult = self.current_value(), self.current_mult()
        embed.add_field(name="Cash Out", value=f"{cash_val:,} ({cash_mult:.2f}x)", inline=True)
        if status == "playing":
            nv, nm = self.next_value(), self.next_mult()
            embed.add_field(name="Next", value=f"{nv:,} ({nm:.2f}x)", inline=True)
        return embed

    def disable_all(self):
        for item in self.children: item.disabled = True

    async def finish(self, interaction: discord.Interaction, status: str, win_amount: int = 0):
        self.finished = True
        active_mines_players.discard(self.player.id)
        if win_amount > 0:
            uid = str(self.player.id)
            await bot.ensure_user(uid)
            async with bot.db_lock: bot.yui_db[uid]["coins"] += win_amount
            asyncio.create_task(bot.save_db())
        if status == "boom":
            for i in self.mine_positions:
                self.cell_buttons[i].style, self.cell_buttons[i].label = discord.ButtonStyle.danger, "💣"
        self.disable_all()
        self.stop()
        await interaction.response.edit_message(embed=self.build_embed(status=status, win_amount=win_amount), view=self)

    async def handle_pick(self, interaction: discord.Interaction, index: int):
        set_footer_guild(interaction.guild)
        if interaction.user.id != self.player.id:
            return await interaction.response.send_message(embed=make_embed("Đây hổng phải ván của cậu đâu! :3", color=ERROR_COLOR), ephemeral=True)
        if self.finished or self.cell_buttons[index].disabled:
            return await interaction.response.defer()

        if index in self.mine_positions:
            return await self.finish(interaction, "boom", 0)

        self.picks += 1
        btn = self.cell_buttons[index]
        btn.style, btn.label, btn.disabled = discord.ButtonStyle.success, "✅", True

        if self.picks >= self.safe_total:
            return await self.finish(interaction, "win", self.current_value())

        await interaction.response.edit_message(embed=self.build_embed(status="playing"), view=self)

    async def handle_cashout(self, interaction: discord.Interaction):
        set_footer_guild(interaction.guild)
        if interaction.user.id != self.player.id:
            return await interaction.response.send_message(embed=make_embed("Đây hổng phải ván của cậu đâu! :3", color=ERROR_COLOR), ephemeral=True)
        if self.finished:
            return await interaction.response.defer()
        await self.finish(interaction, "cashout", self.current_value())

    async def on_timeout(self):
        if self.finished: return
        self.finished = True
        active_mines_players.discard(self.player.id)
        set_footer_guild(self.message.guild if self.message else None)
        win = self.current_value()
        if win > 0:
            uid = str(self.player.id)
            await bot.ensure_user(uid)
            async with bot.db_lock: bot.yui_db[uid]["coins"] += win
            asyncio.create_task(bot.save_db())
        self.disable_all()
        if self.message:
            try: await self.message.edit(embed=self.build_embed(status="timeout"), view=self)
            except discord.HTTPException: pass

# ==============================================================================
# ── MUSIC SYSTEM (SoundCloud) ─────────────────────────────────────────────────
# ==============================================================================

SOUNDCLOUD_URL_RE = re.compile(r'^https?://([a-z0-9-]+\.)*(soundcloud\.com|snd\.sc)(/|$|\?)', re.I)

YDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": False,
    "default_search": "scsearch",
    "socket_timeout": 15,
    "source_address": "0.0.0.0",
    "extract_flat": "in_playlist",
}

FFMPEG_BEFORE_OPTS = "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTS = "-vn"

async def extract_info(query: str) -> Optional[dict]:
    loop = asyncio.get_running_loop()
    def _extract():
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            return ydl.extract_info(query, download=False)
    return await loop.run_in_executor(None, _extract)

DEFAULT_SC_ARTWORK_MARKERS = ("default_avatar", "sndcdn.com/assets/images/default")

class Track:
    __slots__ = ("title", "webpage_url", "duration", "thumbnail", "requester_name", "requester_avatar", "cached_stream_url")
    def __init__(self, info: dict, requester: Optional[discord.abc.User] = None):
        self.title = info.get("title") or "Không rõ tên"
        self.webpage_url = info.get("webpage_url") or info.get("url")
        self.duration = int(info.get("duration") or 0)
        thumb = info.get("thumbnail")
        if not thumb and info.get("thumbnails"):
            thumb = info["thumbnails"][-1].get("url")
        if thumb and any(marker in thumb for marker in DEFAULT_SC_ARTWORK_MARKERS):
            thumb = None
        self.thumbnail = thumb
        self.requester_name = requester.display_name if requester else None
        self.requester_avatar = requester.display_avatar.url if requester else None
        self.cached_stream_url = info.get("url") if info.get("formats") else None

    def hydrate(self, info: dict):
        if info.get("title"):
            self.title = info["title"]
        if info.get("duration"):
            self.duration = int(info["duration"])
        thumb = info.get("thumbnail")
        if not thumb and info.get("thumbnails"):
            thumb = info["thumbnails"][-1].get("url")
        if thumb and not any(marker in thumb for marker in DEFAULT_SC_ARTWORK_MARKERS):
            self.thumbnail = thumb

class GuildMusicState:
    __slots__ = ("queue", "current", "loop_mode", "text_channel_id", "volume", "auto_stay", "started_at", "paused_at", "paused_total", "stopping", "consecutive_failures", "manual_skip")
    def __init__(self):
        self.queue: list[Track] = []
        self.current: Optional[Track] = None
        self.loop_mode = "off"
        self.text_channel_id: Optional[int] = None
        self.volume = 0.5
        self.auto_stay = True
        self.started_at: Optional[float] = None
        self.paused_at: Optional[float] = None
        self.paused_total = 0.0
        self.stopping = False
        self.consecutive_failures = 0
        self.manual_skip = False

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.states: dict[int, GuildMusicState] = {}

    def get_state(self, guild_id: int) -> GuildMusicState:
        if guild_id not in self.states:
            self.states[guild_id] = GuildMusicState()
        return self.states[guild_id]

    def _get_position_ms(self, state: GuildMusicState) -> int:
        if state.started_at is None:
            return 0
        now = time.monotonic()
        paused_extra = (now - state.paused_at) if state.paused_at else 0.0
        return max(0, int((now - state.started_at - state.paused_total - paused_extra) * 1000))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.id != self.bot.user.id or before.channel is None or after.channel is not None:
            return
        state = self.states.get(member.guild.id)
        if not state or not state.auto_stay:
            return
        try:
            await before.channel.connect(self_deaf=True, timeout=30)
        except Exception as e:
            log(f"Không thể tự vào lại kênh voice: {e}", "warn")
            return
        if state.current:
            state.queue.insert(0, state.current)
            state.current = None
        await self._play_next(member.guild)

    async def _reply(self, interaction: discord.Interaction, text: str, error: bool = False):
        embed = make_embed(text, color=ERROR_COLOR if error else EMBED_COLOR)
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=error)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=error)
        except discord.HTTPException: pass

    async def _ensure_voice(self, interaction: discord.Interaction) -> Optional[discord.VoiceClient]:
        user_voice = interaction.user.voice
        if not user_voice or not user_voice.channel:
            await asyncio.sleep(0.6)
            user_voice = interaction.user.voice
            if not user_voice or not user_voice.channel:
                await self._reply(interaction, f"{HEART} Cậu cần vào kênh voice trước nha!", error=True)
                return None
        vc = interaction.guild.voice_client
        if vc is None:
            try:
                vc = await user_voice.channel.connect(self_deaf=True, timeout=30)
            except Exception as e:
                await self._reply(interaction, f"{HEART} Lỗi kết nối: `{e}`", error=True)
                return None
            self.get_state(interaction.guild.id).text_channel_id = interaction.channel_id
        if user_voice.channel.id != vc.channel.id:
            await self._reply(interaction, f"{HEART} Cậu phải ở chung kênh voice với Yui nha!", error=True)
            return None
        return vc

    def _track_added_embed(self, track: Track, state: GuildMusicState) -> discord.Embed:
        position = len(state.queue)
        embed = make_embed(f"**[{truncate_title(track.title)}]({track.webpage_url})**", title=f"{HEART} Đã thêm vào hàng chờ")
        embed.add_field(name="⏱️ Thời lượng", value=fmt_time(track.duration * 1000), inline=True)
        embed.add_field(name="🔢 Vị trí", value=f"#{position}" if position > 0 else "*Phát ngay*", inline=True)
        if track.requester_name:
            embed.set_author(name=f"Yêu cầu bởi {track.requester_name}", icon_url=track.requester_avatar)
        if track.thumbnail: embed.set_thumbnail(url=track.thumbnail)
        return embed

    async def _announce(self, guild: discord.Guild, track: Track, state: GuildMusicState):
        if not state.text_channel_id: return
        channel = guild.get_channel(state.text_channel_id)
        if not channel: return
        set_footer_guild(guild)
        embed = make_embed(
            f"**[{truncate_title(track.title)}]({track.webpage_url})**",
            title=f"{HEART} Yui đang gảy đàn cho cậu nghe~",
        )
        embed.add_field(name="⏱️ Thời lượng", value=fmt_time(track.duration * 1000), inline=True)
        remaining = len(state.queue)
        embed.add_field(name="📃 Kế tiếp", value=f"{remaining} bài" if remaining else "*Hàng chờ trống*", inline=True)
        if track.requester_name:
            embed.set_author(name=f"Yêu cầu bởi {track.requester_name}", icon_url=track.requester_avatar)
        if track.thumbnail: embed.set_thumbnail(url=track.thumbnail)
        try: await channel.send(embed=embed)
        except discord.HTTPException: pass

    async def _announce_error(self, guild: discord.Guild, state: GuildMusicState, text: str):
        if not state.text_channel_id: return
        channel = guild.get_channel(state.text_channel_id)
        if not channel: return
        set_footer_guild(guild)
        try: await channel.send(embed=make_embed(f"{HEART} {text}", title=f"{HEART} Yui gặp trục trặc rồi", color=ERROR_COLOR))
        except discord.HTTPException: pass

    async def _resolve_stream_url(self, track: Track) -> Optional[str]:
        try:
            info = await extract_info(track.webpage_url)
        except Exception:
            return None
        if not info: return None
        if info.get("entries"):
            info = info["entries"][0] if info["entries"] else None
        if not info: return None
        track.hydrate(info)
        return info.get("url")

    async def _prefetch_next(self, track: Track):
        if track.cached_stream_url: return
        url = await self._resolve_stream_url(track)
        if url: track.cached_stream_url = url

    async def _hydrate_upcoming(self, tracks: list[Track]):
        for t in tracks:
            if t.duration and t.title != "Không rõ tên":
                continue
            try:
                info = await extract_info(t.webpage_url)
                if info: t.hydrate(info)
            except Exception:
                pass

    async def _play_next(self, guild: discord.Guild):
        vc = guild.voice_client
        if vc is None: return
        state = self.get_state(guild.id)

        if state.stopping:
            return

        if state.consecutive_failures >= MUSIC_MAX_CONSECUTIVE_FAILURES:
            state.consecutive_failures = 0
            state.queue.clear()
            state.current = None
            state.started_at = None
            await self._announce_error(
                guild, state,
                "Yui thử phát mấy bài liên tiếp mà bài nào cũng lỗi hết (chắc SoundCloud đang chặn server của Yui). "
                "Yui dừng hàng chờ lại đây, đợi lát rồi `/play` lại thử xem nha!"
            )
            return

        if state.loop_mode == "track" and state.current:
            next_track = state.current
        else:
            if state.loop_mode == "queue" and state.current:
                state.queue.append(state.current)
            if not state.queue:
                state.current = None
                state.started_at = None
                return
            next_track = state.queue.pop(0)

        stream_url = next_track.cached_stream_url or await self._resolve_stream_url(next_track)

        if not stream_url:
            state.consecutive_failures += 1
            return await self._play_next(guild)

        state.current = next_track
        state.started_at = time.monotonic()
        state.paused_at = None
        state.paused_total = 0.0

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(stream_url, before_options=FFMPEG_BEFORE_OPTS, options=FFMPEG_OPTS), volume=state.volume)
        def _after(error: Optional[Exception]):
            elapsed = (time.monotonic() - state.started_at) if state.started_at else 0.0
            if state.manual_skip:
                state.manual_skip = False
                state.consecutive_failures = 0
            elif error or elapsed < MUSIC_MIN_PLAYBACK_SECONDS:
                state.consecutive_failures += 1
            else:
                state.consecutive_failures = 0
            fut = asyncio.run_coroutine_threadsafe(self._play_next(guild), self.bot.loop)
            try: fut.result()
            except Exception: pass
        vc.play(source, after=_after)
        await self._announce(guild, next_track, state)

        if state.loop_mode != "track" and state.queue:
            asyncio.create_task(self._prefetch_next(state.queue[0]))

    @app_commands.command(name="play", description="Phát nhạc từ SoundCloud")
    @app_commands.describe(query="Link SoundCloud hoặc tên bài hát để Yui tìm trên SoundCloud")
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.guild_id)
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        vc = await self._ensure_voice(interaction)
        if vc is None: return

        state = self.get_state(interaction.guild.id)
        state.text_channel_id = interaction.channel_id
        state.stopping = False
        is_url = bool(re.match(r'^https?://', query, re.I))
        search_target = query if is_url else f"scsearch1:{query}"
        try: info = await extract_info(search_target)
        except Exception as e:
            return await interaction.followup.send(embed=make_embed(f"{HEART} Lỗi khi tìm bài: `{e}`", color=ERROR_COLOR))

        entries = info.get("entries") if info else None
        if entries is not None:
            entries = [e for e in entries if e]
            if not entries: return await interaction.followup.send(embed=make_embed(f"{HEART} Không tìm thấy bài nào hết á!", color=ERROR_COLOR))
            if is_url and info.get("_type") == "playlist" and len(entries) > 1:
                MAX_TRACKS = 200
                total_entries = len(entries)
                is_truncated = total_entries > MAX_TRACKS

                if is_truncated:
                    entries = entries[:MAX_TRACKS]

                tracks = [Track(e, requester=interaction.user) for e in entries]
                state.queue.extend(tracks)

                embed = make_embed(f"**[{info.get('title', 'Playlist SoundCloud')}]({query})**", title=f"{HEART} Đã thêm playlist vào hàng chờ")
                if is_truncated:
                    embed.add_field(name="🎵 Số bài", value=f"{len(tracks)} bài (đã cắt bớt từ {total_entries} bài để tránh nghẽn mạng)", inline=True)
                else:
                    embed.add_field(name="🎵 Số bài", value=f"{len(tracks)} bài", inline=True)
                    
                embed.set_author(name=f"Yêu cầu bởi {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
                asyncio.create_task(self._hydrate_upcoming(tracks[:3]))
            else:
                track = Track(entries[0], requester=interaction.user)
                state.queue.append(track)
                embed = self._track_added_embed(track, state)
        else:
            if not info: return await interaction.followup.send(embed=make_embed(f"{HEART} Không tìm thấy bài nào hết á!", color=ERROR_COLOR))
            track = Track(info, requester=interaction.user)
            state.queue.append(track)
            embed = self._track_added_embed(track, state)

        await interaction.followup.send(embed=embed)
        if not vc.is_playing() and not vc.is_paused():
            await self._play_next(interaction.guild)

    @app_commands.command(name="skip", description="Bỏ qua bài đang phát")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc is None or not (vc.is_playing() or vc.is_paused()):
            return await interaction.response.send_message(embed=make_embed(f"{HEART} Đâu có bài nào đang phát đâu!", color=ERROR_COLOR), ephemeral=True)
        self.get_state(interaction.guild.id).manual_skip = True
        vc.stop()
        await interaction.response.send_message(embed=make_embed(f"{HEART} Đã bỏ qua bài hiện tại!"))

    @app_commands.command(name="pause", description="Tạm dừng nhạc")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc is None or not vc.is_playing():
            return await interaction.response.send_message(embed=make_embed(f"{HEART} Đâu có bài nào đang phát đâu!", color=ERROR_COLOR), ephemeral=True)
        vc.pause()
        self.get_state(interaction.guild.id).paused_at = time.monotonic()
        await interaction.response.send_message(embed=make_embed(f"{HEART} Đã tạm dừng!"))

    @app_commands.command(name="resume", description="Phát tiếp nhạc")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc is None or not vc.is_paused():
            return await interaction.response.send_message(embed=make_embed(f"{HEART} Đâu có bài nào đang tạm dừng đâu!", color=ERROR_COLOR), ephemeral=True)
        vc.resume()
        state = self.get_state(interaction.guild.id)
        if state.paused_at:
            state.paused_total += time.monotonic() - state.paused_at
            state.paused_at = None
        await interaction.response.send_message(embed=make_embed(f"{HEART} Phát tiếp nè!"))

    @app_commands.command(name="queue", description="Xem hàng chờ nhạc")
    async def show_queue(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild.id)
        if not state.current and not state.queue:
            return await interaction.response.send_message(embed=make_embed(f"{HEART} Hàng chờ trống trơn!", color=ERROR_COLOR), ephemeral=True)

        upcoming = state.queue[:5]
        lines = []
        for i, t in enumerate(upcoming, start=1):
            req = f" — *{t.requester_name}*" if t.requester_name else ""
            lines.append(f"{i:02d}. [{truncate_title(t.title)}]({t.webpage_url}) {fmt_time(t.duration * 1000)}{req}")
        remaining = len(state.queue) - len(upcoming)
        if remaining > 0: lines.append(f"-# ... và {remaining} bài khác")

        embed = make_embed("\n".join(lines) if lines else "", title=f"{HEART} Hàng chờ nhạc của Yui")

        if state.current:
            c = state.current
            position_ms = self._get_position_ms(state)
            duration_ms = c.duration * 1000
            embed.add_field(
                name="▶️ Đang phát",
                value=f"[{truncate_title(c.title)}]({c.webpage_url}) — {fmt_time(position_ms)}/{fmt_time(duration_ms)}",
                inline=False,
            )
            if c.thumbnail: embed.set_thumbnail(url=c.thumbnail)

        total_ms = sum(t.duration for t in state.queue) * 1000
        embed.set_footer(text=f"{current_footer_ctx.get()} • {len(state.queue)} bài trong hàng chờ • Tổng {fmt_time_or_zero(total_ms)}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description="Xem bài đang phát")
    async def nowplaying(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild.id)
        if not state.current:
            return await interaction.response.send_message(embed=make_embed(f"{HEART} Đâu có bài nào đang phát đâu!", color=ERROR_COLOR), ephemeral=True)
        track = state.current
        position_ms = self._get_position_ms(state)
        duration_ms = track.duration * 1000
        pct = int(min(100, (position_ms / duration_ms * 100))) if duration_ms else 0
        status_icon = "⏸️" if state.paused_at else "🎸"

        embed = make_embed(f"**[{truncate_title(track.title)}]({track.webpage_url})**", title=f"{HEART} Yui đang gảy đàn~")
        embed.add_field(name=f"{status_icon} Vị trí", value=f"{fmt_time(position_ms)} / {fmt_time(duration_ms)} ({pct}%)", inline=True)
        embed.add_field(name="🔁 Chế độ lặp", value=state.loop_mode, inline=True)
        if track.requester_name:
            embed.set_author(name=f"Yêu cầu bởi {track.requester_name}", icon_url=track.requester_avatar)
        if track.thumbnail: embed.set_thumbnail(url=track.thumbnail)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="loop", description="/loop: lặp bài hiện tại • /loop all: lặp hàng chờ • /loop off: tắt lặp")
    @app_commands.choices(mode=[Choice(name="all — lặp cả hàng chờ", value="all"), Choice(name="off — tắt lặp", value="off")])
    async def loop(self, interaction: discord.Interaction, mode: Choice[str] = None):
        state = self.get_state(interaction.guild.id)
        if mode is None:
            state.loop_mode = "track"
            label = "Lặp bài hiện tại"
        elif mode.value == "all":
            state.loop_mode = "queue"
            label = "Lặp cả hàng chờ"
        else:
            state.loop_mode = "off"
            label = "Tắt lặp"
        await interaction.response.send_message(embed=make_embed(f"{HEART} Chế độ lặp: **{label}**"))

    @app_commands.command(name="shuffle", description="Xáo trộn hàng chờ")
    async def shuffle(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild.id)
        if not state.queue:
            return await interaction.response.send_message(embed=make_embed(f"{HEART} Hàng chờ trống, xáo gì bây giờ!", color=ERROR_COLOR), ephemeral=True)
        random.shuffle(state.queue)
        await interaction.response.send_message(embed=make_embed(f"{HEART} Đã xáo trộn hàng chờ!"))

    @app_commands.command(name="remove", description="Xoá 1 bài khỏi hàng chờ theo số thứ tự trong /queue")
    async def remove(self, interaction: discord.Interaction, index: app_commands.Range[int, 1, 500]):
        state = self.get_state(interaction.guild.id)
        if not state.queue or index > len(state.queue):
            return await interaction.response.send_message(embed=make_embed(f"{HEART} Số thứ tự không hợp lệ!", color=ERROR_COLOR), ephemeral=True)
        removed = state.queue.pop(index - 1)
        await interaction.response.send_message(embed=make_embed(f"{HEART} Đã xoá **{removed.title}** khỏi hàng chờ!"))

    @app_commands.command(name="stop", description="Dừng hẳn, xoá hàng chờ và rời voice")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        state = self.get_state(interaction.guild.id)
        state.auto_stay = False
        state.stopping = True
        state.consecutive_failures = 0
        if vc:
            state.queue.clear()
            state.current = None
            state.started_at = None
            if vc.is_playing() or vc.is_paused():
                vc.stop()
            await vc.disconnect(force=True)
            await interaction.response.send_message(embed=make_embed(f"{HEART} Yui ôm ghi ta về phòng câu lạc bộ đây, tạm biệt nha!", gif=True))
        else:
            await interaction.response.send_message(embed=make_embed(f"{HEART} Yui có ở trong kênh thoại nào đâu ngốc ạ!", color=ERROR_COLOR), ephemeral=True)

# ==============================================================================
# ── AUTOQUEST CORE ────────────────────────────────────────────────────────────
# ==============================================================================

API_BASE = "https://discord.com/api/v9"
POLL_INTERVAL = 60
HEARTBEAT_INTERVAL = 20
AUTO_ACCEPT = True

SUPPORTED_TASKS = [
    "WATCH_VIDEO",
    "PLAY_ON_DESKTOP",
    "STREAM_ON_DESKTOP",
    "PLAY_ACTIVITY",
    "WATCH_VIDEO_ON_MOBILE"
]

def fetch_latest_build_number() -> int:
    FALLBACK = 504649
    try:
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        r = requests.get("https://discord.com/app", headers={"User-Agent": ua}, timeout=15)
        if r.status_code != 200: return FALLBACK
        scripts = re.findall(r'/assets/([a-f0-9]+)\.js', r.text) or [s.split('/')[-1].replace('.js', '') for s in re.findall(r'src="(/assets/[^"]+\.js)"', r.text)]
        for h in scripts[-5:]:
            try:
                ar = requests.get(f"https://discord.com/assets/{h}.js", headers={"User-Agent": ua}, timeout=15)
                m = re.search(r'buildNumber["\s:]+["\s]*(\d{5,7})', ar.text)
                if m: return int(m.group(1))
            except Exception: continue
        return FALLBACK
    except Exception as e:
        log(f"Lỗi fetch build number: {e}", "warn")
        return FALLBACK

LATEST_BUILD = 504649

def make_super_properties(build_number: int) -> str:
    obj = {
        "os": "Windows",
        "browser": "Discord Client",
        "release_channel": "stable",
        "client_version": "1.0.9175",
        "os_version": "10.0.26100",
        "os_arch": "x64",
        "app_arch": "x64",
        "system_locale": "en-US",
        "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9175 Chrome/128.0.6613.186 Electron/32.2.7 Safari/537.36",
        "browser_version": "32.2.7",
        "client_build_number": build_number,
        "native_build_number": 59498,
        "client_event_source": None,
    }
    return base64.b64encode(json.dumps(obj).encode()).decode()

class DiscordAPI:
    def __init__(self, token: str, build_number: int):
        self.token = token
        self.session = requests.Session()
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9175 Chrome/128.0.6613.186 Electron/32.2.7 Safari/537.36"
        sp = make_super_properties(build_number)
        self.session.headers.update({
            "Authorization": token,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": ua,
            "X-Super-Properties": sp,
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "Asia/Ho_Chi_Minh",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/channels/@me",
        })

    def get(self, path: str, **kwargs): return self.session.get(f"{API_BASE}{path}", **kwargs)
    def post(self, path: str, payload: Optional[dict] = None, **kwargs): return self.session.post(f"{API_BASE}{path}", json=payload, **kwargs)
    def validate_token(self) -> bool:
        try: return self.get("/users/@me").status_code == 200
        except Exception as e:
            log(f"Lỗi validate token: {e}", "error")
            return False

def _get(d, *keys):
    if d is None: return None
    for k in keys:
        if k in d: return d[k]
    return None

def get_task_config(quest: dict): return _get(quest.get("config", {}), "taskConfig", "task_config", "taskConfigV2", "task_config_v2")

def get_quest_name(quest: dict) -> str:
    cfg = quest.get("config", {})
    msgs = cfg.get("messages", {})
    name = _get(msgs, "questName", "quest_name")
    if name: return name.strip()
    game = _get(msgs, "gameTitle", "game_title")
    if game: return game.strip()
    app_name = cfg.get("application", {}).get("name")
    if app_name: return app_name
    return f"Quest#{quest.get('id', '?')}"

def get_expires_at(quest: dict) -> Optional[str]:
    return _get(quest.get("config", {}), "expiresAt", "expires_at")

def get_user_status(quest: dict) -> dict:
    us = _get(quest, "userStatus", "user_status")
    return us if isinstance(us, dict) else {}

def is_completable(quest: dict) -> bool:
    expires = get_expires_at(quest)
    if expires:
        try:
            exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if exp_dt <= datetime.now(timezone.utc):
                return False
        except Exception: pass

    tc = get_task_config(quest)
    return any(tc["tasks"].get(t) is not None for t in SUPPORTED_TASKS) if tc and "tasks" in tc else False

def is_enrolled(quest: dict) -> bool: return bool(_get(get_user_status(quest), "enrolledAt", "enrolled_at"))
def is_completed(quest: dict) -> bool: return bool(_get(get_user_status(quest), "completedAt", "completed_at"))
def get_enrolled_at(quest: dict) -> Optional[str]: return _get(get_user_status(quest), "enrolledAt", "enrolled_at")

def get_task_type(quest: dict) -> Optional[str]:
    tc = get_task_config(quest)
    if not tc or "tasks" not in tc: return None
    for t in SUPPORTED_TASKS:
        if tc["tasks"].get(t) is not None: return t
    return None

def get_seconds_needed(quest: dict) -> int:
    tc = get_task_config(quest)
    t = get_task_type(quest)
    return tc["tasks"][t].get("target", 0) if tc and t else 0

def get_seconds_done(quest: dict) -> float:
    t = get_task_type(quest)
    return get_user_status(quest).get("progress", {}).get(t, {}).get("value", 0) if t else 0

class QuestAutocompleter:
    def __init__(self, api: DiscordAPI):
        self.api = api
        self.completed_ids = set()

    def fetch_quests(self) -> list:
        try:
            r = self.api.get("/quests/@me")
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict):
                    # Bỏ qua nếu đang bị block
                    blocked = data.get("quest_enrollment_blocked_until")
                    if blocked:
                        log(f"Account đang bị chặn enroll quest đến: {blocked}", "warn")
                        return []
                    return data.get("quests", [])
                elif isinstance(data, list):
                    return data
            elif r.status_code == 429:
                retry_after = r.json().get("retry_after", 10)
                time.sleep(retry_after)
                return self.fetch_quests()
            return []
        except Exception as e:
            log(f"Lỗi fetch quests: {e}", "error")
            return []

    def enroll_quest(self, quest: dict) -> bool:
        qid = quest["id"]
        payload = {
            "location": 11,
            "is_targeted": False,
            "metadata_raw": None,
            "metadata_sealed": None,
            "traffic_metadata_raw": quest.get("traffic_metadata_raw"),
            "traffic_metadata_sealed": quest.get("traffic_metadata_sealed"),
        }
        for attempt in range(1, 4):
            try:
                r = self.api.post(f"/quests/{qid}/enroll", payload)
                if r.status_code == 429:
                    wait = r.json().get("retry_after", 5) + 1
                    time.sleep(wait)
                    continue
                return r.status_code in (200, 201, 204)
            except Exception as e:
                log(f"Lỗi enroll quest {qid}: {e}", "warn")
                return False
        return False

    def auto_accept(self, quests: list) -> list:
        for q in [q for q in quests if not is_enrolled(q) and not is_completed(q) and is_completable(q)]:
            self.enroll_quest(q)
            time.sleep(2)
        return self.fetch_quests()

    def process_quest(self, quest: dict) -> bool:
        qid, task_type = quest.get("id"), get_task_type(quest)
        if not task_type or qid in self.completed_ids: return False

        name = get_quest_name(quest)
        sec_needed, sec_done = get_seconds_needed(quest), get_seconds_done(quest)
        log(f"Bắt đầu cày: {name} (Loại: {task_type})", "info")

        # ── 1. NHIỆM VỤ XEM VIDEO ──
        if task_type in ["WATCH_VIDEO", "WATCH_VIDEO_ON_MOBILE"]:
            enrolled_at_str = get_enrolled_at(quest)
            if enrolled_at_str:
                try: enrolled_ts = datetime.fromisoformat(enrolled_at_str.replace("Z", "+00:00")).timestamp()
                except Exception: enrolled_ts = time.time()
            else:
                enrolled_ts = time.time()

            max_future = 10
            speed = 7
            max_loops = (sec_needed // speed) + 30
            loops = 0

            while sec_done < sec_needed and loops < max_loops:
                loops += 1
                max_allowed = (time.time() - enrolled_ts) + max_future
                diff = max_allowed - sec_done
                timestamp = sec_done + speed

                if diff >= speed:
                    try:
                        r = self.api.post(f"/quests/{qid}/video-progress", {
                            "timestamp": min(sec_needed, timestamp + random.random())
                        })
                        if r.status_code == 200:
                            body = r.json()
                            if body.get("completed_at"):
                                self.completed_ids.add(qid)
                                return True
                            sec_done = min(sec_needed, timestamp)
                        elif r.status_code == 429:
                            time.sleep(r.json().get("retry_after", 5) + 1)
                            continue
                    except Exception as e:
                        log(f"Lỗi quest video {qid}: {e}", "warn")

                if timestamp >= sec_needed: break
                time.sleep(1)

            try: self.api.post(f"/quests/{qid}/video-progress", {"timestamp": sec_needed})
            except: pass
            if sec_done >= sec_needed:
                self.completed_ids.add(qid)
                return True

        # ── 2. NHIỆM VỤ CHƠI GAME / STREAM / ACTIVITY ──
        else:
            pid = random.randint(1000, 30000)
            stream_key = "call:0:1" if task_type == "PLAY_ACTIVITY" else f"call:0:{pid}"
            max_loops = (sec_needed // HEARTBEAT_INTERVAL) + 20
            loops = 0

            while sec_done < sec_needed and loops < max_loops:
                loops += 1
                try:
                    r = self.api.post(f"/quests/{qid}/heartbeat", {
                        "stream_key": stream_key,
                        "terminal": False
                    })
                    if r.status_code == 200:
                        body = r.json()
                        pdata = body.get("progress", {})
                        if pdata and task_type in pdata:
                            sec_done = pdata[task_type].get("value", sec_done)
                        if body.get("completed_at") or sec_done >= sec_needed:
                            self.completed_ids.add(qid)
                            return True
                    elif r.status_code == 429:
                        time.sleep(r.json().get("retry_after", 5) + 1)
                        continue
                except Exception as e:
                    log(f"Lỗi heartbeat quest {qid}: {e}", "warn")

                time.sleep(HEARTBEAT_INTERVAL)

            try: self.api.post(f"/quests/{qid}/heartbeat", {"stream_key": stream_key, "terminal": True})
            except: pass

        if sec_done >= sec_needed:
            self.completed_ids.add(qid)
            return True
        return False

def make_progress_bar_quest(percentage: float) -> str:
    return f"**{percentage:.1f}%**"

async def run_quests_with_progress(user_token: str, user: discord.User, is_keyl: bool, mode: str) -> dict:
    def setup_and_get():
        api = DiscordAPI(user_token, LATEST_BUILD)
        if not api.validate_token(): return None, {"status": "error", "msg": "Token không hợp lệ!"}
        completer = QuestAutocompleter(api)
        quests = completer.auto_accept(completer.fetch_quests())
        actionable = [q for q in quests if is_enrolled(q) and not is_completed(q) and is_completable(q)]
        return completer, {"total": len(quests), "completed_before": sum(1 for q in quests if is_completed(q)), "actionable": actionable}

    setup_result = await asyncio.to_thread(setup_and_get)
    if setup_result[0] is None: return setup_result[1]
    completer, data = setup_result

    success_count = 0
    for i, q in enumerate(data["actionable"]):
        if mode == "slow" and i > 0:
            delay = random.randint(3600, 10800)
            try:
                delay_msg = await user.send(embed=make_embed(f"Yui mỏi tay quá, nghỉ uống trà chiều **{delay // 60} phút** rồi mới làm quest tiếp theo nha! :3", title=f"{HEART} Giờ nghỉ giải lao...", gif=True))
            except discord.Forbidden:
                delay_msg = None
            
            await asyncio.sleep(delay)
            if delay_msg:
                try: await delay_msg.delete()
                except discord.HTTPException: pass

        q_name, q_type = get_quest_name(q), get_task_type(q) or "UNKNOWN"
        sec_needed, sec_done = get_seconds_needed(q), get_seconds_done(q)
        desc = f"**Loại:** {q_type}\n**Thời gian cần:** {sec_needed // 60} phút {sec_needed % 60} giây\n\n{make_progress_bar_quest(0.0)}"
        embed_prog = make_embed(desc, title=f"{HEART} Yui đang làm: {q_name}", gif=True)
        prog_msg = None
        try: prog_msg = await user.send(embed=embed_prog)
        except discord.Forbidden: pass

        task = asyncio.create_task(asyncio.to_thread(lambda: completer.process_quest(q)))
        start_time = time.time()
        
        if prog_msg:
            while not task.done():
                await asyncio.sleep(10)
                if task.done(): break
                current_done = min(sec_done + (time.time() - start_time), sec_needed)
                embed_prog.description = f"**Loại:** {q_type}\n**Thời gian cần:** {sec_needed // 60} phút {sec_needed % 60} giây\n\n{make_progress_bar_quest((current_done / sec_needed * 100) if sec_needed > 0 else 0)}"
                try: await prog_msg.edit(embed=embed_prog)
                except Exception as e: 
                    log(f"Lỗi update message quest progress: {e}", "debug")
                    
        is_success = await task
        if is_success:
            success_count += 1
            if prog_msg:
                try: await prog_msg.delete() 
                except Exception as e: log(f"Lỗi xoá msg progress: {e}", "debug")
            try: await user.send(embed=make_embed(f"**{q_name}**\nLoại: {q_type}\n\n{HEART} Nhiệm vụ đã được Yui hoàn thành!", title=f"{HEART} Quest hoàn thành!", gif=True))
            except Exception as e: 
                log(f"Lỗi báo cáo quest xong: {e}", "warn")
        else:
            log(f"Quest {q_name} chạy thất bại do API không ghi nhận.", "error")

    return {"status": "success", "total": data["total"], "completed_before": data["completed_before"], "to_do": len(data["actionable"]), "success": success_count, "failed": len(data["actionable"]) - success_count}

class ToSView(discord.ui.View):
    def __init__(self, user_token: str, is_keyl: bool, mode: str):
        super().__init__(timeout=120)
        self.user_token = user_token
        self.is_keyl = is_keyl
        self.mode = mode

    @discord.ui.button(label="Làm đi nè", style=discord.ButtonStyle.green, custom_id="accept_btn")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children: child.disabled = True
        
        if self.mode == "slow":
            await interaction.response.edit_message(embed=make_embed(f"Vì chọn An Toàn nên Yui sẽ túc tắc làm từng cái rồi báo kết quả qua Inbox nha! Thời gian có thể mất vài tiếng á! {HEART}", title=f"{HEART} Yui đang chạy ngầm...", gif=True), view=self)
            asyncio.create_task(self.run_background_quests(interaction.user))
        else:
            await interaction.response.edit_message(embed=make_embed(f"Cậu đợi Yui một chút nha, rẹt rẹt là xong liền! {HEART}", title=f"{HEART} Đang cặm cụi làm việc...", gif=True), view=self)
            await self.run_background_quests(interaction.user, interaction)

    async def run_background_quests(self, user: discord.User, interaction: Optional[discord.Interaction] = None):
        result = await run_quests_with_progress(self.user_token, user, self.is_keyl, self.mode)
        if result["status"] == "error":
            report_embed = make_embed(f"**Có lỗi kẹt lại nè:**\n{result['msg']}", title=f"{HEART} Ây da, có lỗi rồi", color=ERROR_COLOR)
        else:
            report_embed = make_embed(f"Tadaaa! Yui đã dọn dẹp sạch sẽ đống quest cho cậu rồi nè {HEART}", title=f"{HEART} BÁO CÁO HOÀN THÀNH {HEART}")
            report_embed.add_field(name="Tình hình tủ Quest", value=f"```\nTổng cộng: {result['total']}\nĐã xong trước đó: {result['completed_before']}\nCần quét dọn: {result['to_do']}\n```", inline=False)
            report_embed.add_field(name="Thành quả", value=f"```\nĐã xử lý: {result['to_do']}\nThành công: {result['success']}\nThất bại: {result['failed']}\n```", inline=False)
        
        if interaction:
            try: await interaction.edit_original_response(embed=make_embed(f"Xong hết rồi đó, cậu xem kết quả ở Inbox nha! {HEART}", title=f"{HEART} Yui làm xong rồi!", gif=True))
            except Exception: pass
        
        try: await user.send(embed=report_embed)
        except Exception as e: log(f"Lỗi gửi báo cáo DM cho {user.name}: {e}", "error")

    @discord.ui.button(label="Thôi hổng cần", style=discord.ButtonStyle.gray, custom_id="decline_btn")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(embed=make_embed("Vậy thôi cậu nghỉ ngơi đi nha! :3", title="Đã hủy dọn dẹp"), view=self)

# ==============================================================================
# ── NÂNG CẤP BADGE SPOOFER (Chuẩn Telemetry & X-Super-Properties 2026) ────────
# ==============================================================================

SPOOFER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) discord/1.0.9253 Chrome/148.0.7778.280 "
    "Electron/42.7.1 Safari/537.36"
)

def get_base_super_properties(build_number: int) -> dict:
    try:
        r = requests.post("https://cordapi.dolfi.es/api/v2/properties/windows", json={}, timeout=6)
        if r.status_code == 200:
            data = r.json()
            if "properties" in data and isinstance(data["properties"], dict):
                return data["properties"]
    except Exception:
        pass

    return {
        "os": "Windows",
        "browser": "Discord Client",
        "release_channel": "stable",
        "client_version": "1.0.9253",
        "os_version": "10.0.26200",
        "os_arch": "x64",
        "app_arch": "x64",
        "system_locale": "en-US",
        "has_client_mods": False,
        "browser_user_agent": SPOOFER_USER_AGENT,
        "browser_version": "42.7.1",
        "os_sdk_version": "26200",
        "client_build_number": build_number if build_number else 594031,
        "native_build_number": 88414,
        "client_event_source": None,
        "client_app_state": "focused",
    }

def encode_session_super_props(base_props: dict, launch_sig: str, hb_session: str) -> str:
    props = dict(base_props)
    props["client_launch_id"] = str(uuid.uuid4())
    props["launch_signature"] = launch_sig
    props["client_heartbeat_session_id"] = hb_session
    raw = json.dumps(props, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")

def get_real_games(limit=2000):
    try:
        r = requests.get("https://cdn.discordapp.com/detectables/games.json", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200:
            games_data = r.json()
            valid_games = []
            seen = set()
            for entry in games_data:
                gid = str(entry.get("id", ""))
                if not gid.isdigit() or gid in seen: continue
                exe_name = "game.exe"
                has_win32 = False
                for ex in entry.get("executables", []):
                    if ex.get("os") == "win32" and ex.get("name"):
                        exe_name = ex["name"]
                        has_win32 = True
                        break
                if not has_win32: continue
                seen.add(gid)
                valid_games.append({"id": gid, "name": entry.get("name", "Unknown"), "exe": exe_name})
                if len(valid_games) >= limit: break
            return valid_games
    except Exception as e: 
        log(f"Lỗi get detectables games: {e}", "error")
    return []

def build_spoofer_session_events(game: dict, duration_ms: int, heartbeat_session: str, launch_signature: str, seq_counter: list, fingerprint: str = "") -> list:
    def get_seq():
        seq_counter[0] += 1
        return seq_counter[0]

    now = int(time.time() * 1000)
    start = now - duration_ms if (now - duration_ms) > 0 else now
    session_id = str(uuid.uuid4())

    props_init = {
        "client_track_timestamp": start,
        "client_heartbeat_session_id": heartbeat_session,
        "event_sequence_number": get_seq(),
        "game_id": game["id"],
        "game_name": game["name"],
        "game_metadata": None,
        "game_executable": game["exe"],
        "game_detection_enabled": True,
        "initial_heartbeat": True,
        "final_heartbeat": False,
        "game_session_id": session_id,
        "duration_tracked_ms": 0,
        "rtc_connection_id": None,
        "media_session_id": None,
        "launch_signature": launch_signature,
        "client_app_state": "focused",
        "client_send_timestamp": start,
    }

    props_launch = {
        "client_track_timestamp": now,
        "client_heartbeat_session_id": heartbeat_session,
        "event_sequence_number": get_seq(),
        "game": game["name"],
        "game_id": game["id"],
        "verified": True,
        "elevated": False,
        "is_launcher": False,
        "game_platform": "desktop",
        "detection_method": "verified_game",
        "is_overlay_enabled": False,
        "is_overlay_game_enabled": True,
        "is_overlay_game_source": "OOP_DEFAULT_DATABASE",
        "fullscreen_type": "UNKNOWN",
        "hardware_display_count": 1,
        "overlay_method": "Disabled",
        "activity_status_enabled": True,
        "activity_status_shared_guilds": [],
        "current_user_status": "online",
        "game_detection_enabled": True,
        "executable_path": game["exe"],
        "voice_channel_id": None,
        "voice_channel_type": None,
        "voice_channel_bitrate": None,
        "voice_channel_guild_id": None,
        "hidden_by_distributor": False,
        "game_metadata": None,
        "client_performance_cpu": None,
        "client_performance_memory": None,
        "cpu_core_count": None,
        "accessibility_features": 0,
        "rendered_locale": "en-US",
        "launch_signature": launch_signature,
        "client_rtc_state": None,
        "client_app_state": "focused",
        "client_send_timestamp": now,
    }
    
    if fingerprint:
        props_launch["executable_fingerprint"] = fingerprint

    props_final = {
        "client_track_timestamp": now,
        "client_heartbeat_session_id": heartbeat_session,
        "event_sequence_number": get_seq(),
        "game_id": game["id"],
        "game_name": game["name"],
        "game_metadata": None,
        "game_executable": game["exe"],
        "game_detection_enabled": True,
        "initial_heartbeat": False,
        "final_heartbeat": True,
        "game_session_id": session_id,
        "duration_tracked_ms": duration_ms,
        "rtc_connection_id": None,
        "media_session_id": None,
        "launch_signature": launch_signature,
        "client_app_state": "focused",
        "client_send_timestamp": now,
    }

    return [
        {"type": "running_game_heartbeat", "properties": props_init},
        {"type": "launch_game", "properties": props_launch},
        {"type": "running_game_heartbeat", "properties": props_final}
    ]

def spoof_badge_sync(token: str, cookie: str, analytics_token: str, games: list, duration_ms: int, raw_fingerprint: str = ""):
    heartbeat_session = str(uuid.uuid4())
    launch_signature = str(uuid.uuid4())
    fingerprint = raw_fingerprint 

    base_props = get_base_super_properties(LATEST_BUILD)
    session_super_props = encode_session_super_props(base_props, launch_signature, heartbeat_session)

    post_headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": token,
        "content-type": "application/json",
        "cookie": cookie,
        "origin": "https://discord.com",
        "referer": "https://discord.com/channels/@me",
        "user-agent": SPOOFER_USER_AGENT,
        "x-debug-options": "bugReporterEnabled",
        "x-discord-locale": "en-US",
        "x-discord-timezone": "Asia/Ho_Chi_Minh",
        "x-super-properties": session_super_props,
    }

    seq_counter = [0]
    events = []
    for g in games:
        events.extend(build_spoofer_session_events(g, duration_ms, heartbeat_session, launch_signature, seq_counter, fingerprint))

    batch_size = 60 
    success_count = 0

    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        payload = {"token": analytics_token, "events": batch}
        try:
            r = requests.post(f"{API_BASE}/science", headers=post_headers, json=payload, timeout=15)
            if r.status_code == 204:
                success_count += len(batch) // 3
            elif r.status_code in (401, 403):
                return False, "Discord từ chối Cookie (cf_clearance) hoặc Token này rồi (Lỗi 401/403)! Hãy lấy Cookie mới nha."
            elif r.status_code == 429:
                wait_time = r.json().get("retry_after", 5) + 1
                time.sleep(wait_time)
                r = requests.post(f"{API_BASE}/science", headers=post_headers, json=payload, timeout=15)
                if r.status_code == 204:
                    success_count += len(batch) // 3
        except Exception as e:
            log(f"Lỗi gửi batch science events: {e}", "warn")
        time.sleep(0.3)

    total_hours_claimed = success_count * (duration_ms / (3600 * 1000.0))
    msg = (f"Vợ cày xong **{success_count}/{len(games)} game** rồi nè!\n"
           f"Tổng thời gian: **{total_hours_claimed:,.0f} giờ**.\n")
    if fingerprint:
        msg += "🛡️ Đã ép Fingerprint xịn xò, tha hồ nhặt huy hiệu Games Played nha!"
        
    return True, msg

class UltimateBadgeModal(discord.ui.Modal):
    token_input = discord.ui.TextInput(label='Token của chồng', style=discord.TextStyle.short, required=True)
    cookie_input = discord.ui.TextInput(label='Cookie cf_clearance', style=discord.TextStyle.paragraph, required=True)
    fingerprint_input = discord.ui.TextInput(label='Mã Fingerprint (Tùy chọn)', placeholder='Dán chuỗi executable_fingerprint thật vào đây...', style=discord.TextStyle.short, required=False)

    def __init__(self, games_count: int, hours_per_game: float):
        super().__init__(title='Buff Huy Hiệu Max Ping')
        self.games_count = games_count
        self.hours_per_game = hours_per_game

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=make_embed(f"Đang ép xung {self.games_count} game x {self.hours_per_game}h, chồng yêu đợi xíu nha! :3", title=f"{HEART} Bắt đầu cày cuốc..."), ephemeral=True)
        asyncio.create_task(self.run_badge_task(interaction.user, self.token_input.value.strip(), self.cookie_input.value.strip(), self.fingerprint_input.value.strip(), self.games_count, self.hours_per_game))
        
    async def run_badge_task(self, user: discord.User, token: str, cookie: str, raw_fingerprint: str, games_count: int, hours_per_game: float):
        uid = str(user.id)
        await bot.ensure_user(uid)
        
        now = time.time()
        cached_token = bot.yui_db[uid].get("analytics_token")
        token_time = bot.yui_db[uid].get("analytics_time", 0)
        
        if not cached_token or (now - token_time) > 43200: # Cache quá 12h thì lấy lại mới
            base_props = get_base_super_properties(LATEST_BUILD)
            session_super_props = encode_session_super_props(base_props, str(uuid.uuid4()), str(uuid.uuid4()))
            req_headers = {
                "authorization": token,
                "user-agent": SPOOFER_USER_AGENT,
                "x-super-properties": session_super_props,
            }
            try:
                r_analytics = await asyncio.to_thread(requests.get, f"{API_BASE}/users/@me?with_analytics_token=true", headers=req_headers, timeout=15)
                if r_analytics.status_code != 200: 
                    return await user.send(embed=make_embed("Lỗi lấy analytics_token! Có thể Token không hợp lệ.", title=f"{HEART} Gãy gánh rùi...", color=ERROR_COLOR, gif=True))
                analytics_token = r_analytics.json().get("analytics_token")
                if not analytics_token:
                    return await user.send(embed=make_embed("Discord trả về thành công nhưng không có analytics_token!", title=f"{HEART} Gãy gánh rùi...", color=ERROR_COLOR, gif=True))
                
                async with bot.db_lock:
                    bot.yui_db[uid]["analytics_token"] = analytics_token
                    bot.yui_db[uid]["analytics_time"] = now
                await bot.save_db()
            except Exception as e:
                log(f"Lỗi kết nối máy chủ Discord khi lấy analytics_token: {e}", "error")
                return await user.send(embed=make_embed("Lỗi kết nối máy chủ Discord khi lấy analytics_token!", title=f"{HEART} Gãy gánh rùi...", color=ERROR_COLOR, gif=True))
        else:
            analytics_token = cached_token
            
        all_games = await asyncio.to_thread(get_real_games, 2000)
        if not all_games:
            return await user.send(embed=make_embed("Lỗi không lấy được danh sách game!", title=f"{HEART} Gãy gánh rùi...", color=ERROR_COLOR, gif=True))
            
        used_games = bot.yui_db[uid].get("used_games", [])
        available_games = [g for g in all_games if g["id"] not in used_games]
        
        if len(available_games) < games_count:
            available_games.extend([g for g in all_games if g["id"] in used_games])
            
        selected_games = available_games[:games_count]
        
        async with bot.db_lock:
            new_used = [g["id"] for g in selected_games] + used_games
            bot.yui_db[uid]["used_games"] = list(dict.fromkeys(new_used))[:1000] # Giữ lại 1000 game gần nhất thôi để file DB nhẹ nè
        await bot.save_db()
        
        duration_ms = int(hours_per_game * 3600 * 1000)
        
        success, msg = await asyncio.to_thread(spoof_badge_sync, token, cookie, analytics_token, selected_games, duration_ms, raw_fingerprint)
        try:
            await user.send(embed=make_embed(msg, title=f"{HEART} Hoàn tất buff huy hiệu!" if success else f"{HEART} Gãy gánh rùi...", color=EMBED_COLOR if success else ERROR_COLOR, gif=True))
        except Exception as e:
            log(f"Lỗi gửi DM sau khi cày badge: {e}", "error")

def set_hypesquad_house(user_token: str, house_name: str) -> tuple[bool, str]:
    houses = {"bravery": 1, "brilliance": 2, "balance": 3, "leave": 0}
    if house_name.lower() not in houses: return False, "Nhà HypeSquad không hợp lệ!"
    headers = {"Authorization": user_token, "Content-Type": "application/json"}
    try:
        if houses[house_name.lower()] == 0:
            r = requests.post(f"{API_BASE}/hypesquad/online", json={}, headers=headers, timeout=10)
            if r.status_code not in (200, 204): r = requests.delete(f"{API_BASE}/hypesquad/online", headers=headers, timeout=10)
        else:
            r = requests.post(f"{API_BASE}/hypesquad/online", json={"house_id": houses[house_name.lower()]}, headers=headers, timeout=10)
        if r.status_code in (200, 204): return True, f"Đã gán thành công huy hiệu **HypeSquad {house_name.capitalize()}** rồi nè :3"
        return False, "Token lỗi hoặc hết hạn rồi nha!"
    except Exception as e: return False, f"Lỗi kết nối: {str(e)}"

# ==============================================================================
# ── CORE & BOT EVENTS ─────────────────────────────────────────────────────────
# ==============================================================================

async def _cooldown_countdown_warning(interaction: discord.Interaction, seconds: int):
    def _text(n: int) -> str:
        return f"{interaction.user.mention} từ từ đã nào, đợi thêm **{n} giây** nữa rồi dùng lại lệnh này nha!"
    try:
        await interaction.response.send_message(_text(seconds))
    except discord.HTTPException:
        return
    remaining = seconds
    while remaining > 1:
        await asyncio.sleep(1)
        remaining -= 1
        try:
            await interaction.edit_original_response(content=_text(remaining))
        except discord.HTTPException:
            return
    await asyncio.sleep(1)
    try:
        await interaction.delete_original_response()
    except discord.HTTPException:
        pass

class YuiCommandTree(app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        set_footer_guild(interaction.guild)
        return True

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            seconds = max(1, round(error.retry_after))
            asyncio.create_task(_cooldown_countdown_warning(interaction, seconds))
            return
        await super().on_error(interaction, error)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix='/', intents=intents, tree_cls=YuiCommandTree)
        self.yui_db = {}
        self.db_lock = asyncio.Lock()

    async def load_db(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f: self.yui_db = json.load(f)
            except: pass

    async def save_db(self):
        async with self.db_lock:
            def _write():
                with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(self.yui_db, f, indent=4)
            await asyncio.to_thread(_write)

    async def ensure_user(self, uid_str: str):
        async with self.db_lock:
            if uid_str not in self.yui_db:
                self.yui_db[uid_str] = {"coins": 0, "wins": 0, "last_daily": "", "fun_daily": {}, "give_today": 0, "give_date": "", "used_games": []}
            elif "used_games" not in self.yui_db[uid_str]:
                self.yui_db[uid_str]["used_games"] = []

    async def setup_hook(self):
        global LATEST_BUILD
        LATEST_BUILD = await asyncio.to_thread(fetch_latest_build_number)
        await asyncio.to_thread(load_dictionary_sync)
        await self.load_db()
        await self.add_cog(MusicCog(self))
        await self.add_cog(FunCog(self))
        await self.tree.sync()
        log("Đã đồng bộ bot thành công!", "ok")

bot = MyBot()

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name="/help 🎸")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    log(f"Yui lên sàn! Bot {bot.user} sẵn sàng phục vụ!", "ok")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot: return
    channel_id = message.channel.id
    content = message.content.strip()

    if channel_id in games and not content.startswith('/'):
        async with get_game_lock(channel_id):
            game = games.get(channel_id)
            if not game: return await bot.process_commands(message)

            parts = split_two_words(content)
            if parts:
                w1, w2 = parts
                if game.get('current') and w1 != game['current'][1]:
                    return await bot.process_commands(message)

                phrase_key = f"{w1} {w2}"
                if game.get('last_author_id') == message.author.id:
                    await safe_react(message, EMOJI_INCORRECT)
                    await safe_reply(message, "Cậu vừa nối rồi, nhường người khác nha! :3")
                    return await bot.process_commands(message)

                if phrase_key in game['history'][-50:]:
                    await safe_react(message, EMOJI_INCORRECT)
                    await safe_reply(message, "Từ này vừa dùng rùi, chờ tý nha!")
                    return await bot.process_commands(message)

                if phrase_key not in VIETNAMESE_WORDS:
                    await safe_react(message, EMOJI_INCORRECT)
                    await safe_reply(message, "Từ này hổng có trong từ điển tiếng Việt của Yui! :3")
                    return await bot.process_commands(message)

                game['current'], game['last_author_id'] = (w1, w2), message.author.id
                game['history'].append(phrase_key)
                await safe_react(message, EMOJI_CORRECT)

                if not has_valid_next_word(w2):
                    new_w1, new_w2 = get_random_start_word()
                    game['current'], game['history'], game['last_author_id'] = (new_w1, new_w2), [f"{new_w1} {new_w2}"], None
                    
                    reward = NOITU_WIN_REWARD
                    uid = str(message.author.id)
                    await bot.ensure_user(uid)
                    bot.yui_db[uid]["wins"] += 1
                    bot.yui_db[uid]["coins"] += reward
                    asyncio.create_task(bot.save_db())

                    await safe_send(message.channel, f"Hết từ nối rồi! **{message.author.display_name}** thắng nha!\n**Thưởng:** {reward} {COIN_EMOJI}\nLượt mới: **{new_w1} {new_w2}**")
    await bot.process_commands(message)

# ==============================================================================
# ── THÔNG BÁO RA/VÀO PHÒNG VOICE ──────────────────────────────────────────────
# ==============================================================================

LEAVE_MESSAGES = [
    "{HEART} Bai bai **{name}** nha! Hẹn cậu ở buổi trà chiều sau! 🍰",
    "{HEART} **{name}** về rồi hả... Yui sẽ nhớ cậu lắm đó nha! :3",
    "{HEART} Tạm biệt **{name}**! Nhớ quay lại chơi nối từ với Yui nha!",
    "🚪 **{name}** rời phòng rồi, hẹn gặp lại cậu sau nha!",
    "{HEART} **{name}** đi ngủ hay đi đâu vậy ta... Ngủ ngon nha cậu!",
    "🍵 Buổi trà chiều với **{name}** tạm dừng ở đây thôi. Hẹn lần sau nha!",
]
JOIN_MESSAGES = [
    "✈️ **{name}** vừa đáp chuyến bay từ **{channel}** tới đây!",
    "{HEART} **{name}** vừa ghé qua **{channel}**, chào mừng cậu nha :3",
    "🎸 **{name}** đã vào **{channel}**, Yui ôm ghi ta ra chào nè!",
    "🌸 Ơ, **{name}** ghé chơi hả! Vào **{channel}** ngồi chơi nha :3",
    "{HEART} **{name}** tới rồi nè, **{channel}** vui hẳn lên luôn!",
    "🍰 Yui vừa pha xong trà thì **{name}** ghé **{channel}** đúng lúc ghê!",
]

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot or before.channel == after.channel:
        return
    guild = member.guild
    if guild.id in disabled_notify_guilds:
        return

    if after.channel is not None and before.channel != after.channel:
        if after.channel.id in disabled_notify_channels:
            return
        perms = after.channel.permissions_for(guild.me)
        if perms.view_channel and perms.send_messages:
            text = random.choice(JOIN_MESSAGES).format(HEART=HEART, name=member.display_name, channel=after.channel.name)
            await safe_send(after.channel, text)
    elif before.channel is not None and after.channel is None:
        if before.channel.id in disabled_notify_channels:
            return
        perms = before.channel.permissions_for(guild.me)
        if perms.view_channel and perms.send_messages:
            text = random.choice(LEAVE_MESSAGES).format(HEART=HEART, name=member.display_name, channel=before.channel.name)
            await safe_send(before.channel, text)

# ==============================================================================
# ── LỆNH TIỀN TỆ & NỐI TỪ & EXTRA ─────────────────────────────────────────────
# ==============================================================================

@bot.tree.command(name="daily", description="Nhận quà điểm danh mỗi ngày :3")
async def daily(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    await bot.ensure_user(uid)
    today = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")
    
    if bot.yui_db[uid].get("last_daily") == today:
        return await interaction.response.send_message(embed=make_embed(f"Hôm nay cậu nhận quà rồi! Mai nha {HEART}", color=ERROR_COLOR), ephemeral=True)
    
    reward = random.randint(DAILY_REWARD_MIN, DAILY_REWARD_MAX)
    bot.yui_db[uid]["coins"] += reward
    bot.yui_db[uid]["last_daily"] = today
    asyncio.create_task(bot.save_db())
    
    await interaction.response.send_message(embed=make_embed(f"Tada! Cậu nhận được **{reward}** {COIN_EMOJI}!\nVí: **{bot.yui_db[uid]['coins']}** {COIN_EMOJI}", title="Quà Hàng Ngày"))

@bot.tree.command(name="cash", description="Xem ví tiền và thành tích nối từ")
async def cash(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    target = member or interaction.user
    uid = str(target.id)
    coins = bot.yui_db.get(uid, {}).get("coins", 0)
    wins = bot.yui_db.get(uid, {}).get("wins", 0)
    embed = make_embed(f"**Tài sản:** {coins} {COIN_EMOJI}\n**Thắng nối từ:** {wins} trận", title=f"Hồ sơ của {target.display_name}")
    embed.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="Xem avatar cá nhân và avatar riêng theo server của một người")
@app_commands.describe(member="Người muốn xem avatar (mặc định là chính bạn)")
async def avatar_cmd(interaction: discord.Interaction, member: Optional[discord.User] = None):
    target = member or interaction.user
    await interaction.response.defer()

    try:
        user = await bot.fetch_user(target.id)
    except discord.NotFound:
        return await interaction.followup.send(embed=make_embed(f"Yui hổng tìm thấy người này đâu! {HEART}", color=ERROR_COLOR))
    global_url = user.display_avatar.url

    guild_url = None
    if interaction.guild:
        try:
            gm = await interaction.guild.fetch_member(target.id)
            if gm.guild_avatar:
                guild_url = gm.guild_avatar.url
        except discord.NotFound:
            pass

    lines = [f"**Avatar cá nhân:** [Xem ảnh]({global_url})"]
    lines.append(f"**Avatar server:** [Xem ảnh]({guild_url})" if guild_url else "**Avatar server:** Không đặt riêng, đang dùng avatar cá nhân")

    embed = make_embed("\n".join(lines), title=f"🖼️ Avatar của {target.display_name}")
    embed.set_image(url=guild_url or global_url)
    if guild_url:
        embed.set_thumbnail(url=global_url)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="banner", description="Xem banner cá nhân và banner riêng theo server của một người")
@app_commands.describe(member="Người muốn xem banner (mặc định là chính bạn)")
async def banner_cmd(interaction: discord.Interaction, member: Optional[discord.User] = None):
    target = member or interaction.user
    await interaction.response.defer()

    try:
        user = await bot.fetch_user(target.id)
    except discord.NotFound:
        return await interaction.followup.send(embed=make_embed(f"Yui hổng tìm thấy người này đâu! {HEART}", color=ERROR_COLOR))
    global_url = user.banner.url if user.banner else None

    guild_url = None
    if interaction.guild:
        try:
            gm = await interaction.guild.fetch_member(target.id)
            if getattr(gm, "guild_banner", None):
                guild_url = gm.guild_banner.url
        except discord.NotFound:
            pass

    if not global_url and not guild_url:
        return await interaction.followup.send(embed=make_embed(f"{target.mention} chưa đặt banner nào cả! :3", color=ERROR_COLOR))

    lines = [f"**Banner cá nhân:** [Xem ảnh]({global_url})" if global_url else "**Banner cá nhân:** Chưa đặt"]
    lines.append(f"**Banner server:** [Xem ảnh]({guild_url})" if guild_url else "**Banner server:** Chưa đặt riêng")

    embed = make_embed("\n".join(lines), title=f"🎴 Banner của {target.display_name}")
    embed.set_image(url=guild_url or global_url)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="top", description="Xem bảng xếp hạng Yui Coin hoặc Nối từ")
@app_commands.choices(loai=[Choice(name="Đại Gia (Coin)", value="coins"), Choice(name="Nối Từ (Wins)", value="wins")])
async def top(interaction: discord.Interaction, loai: Choice[str]):
    k = loai.value
    sorted_u = sorted([i for i in bot.yui_db.items() if i[1].get(k, 0) > 0], key=lambda x: x[1].get(k, 0), reverse=True)[:10]
    if not sorted_u: return await interaction.response.send_message(embed=make_embed("Chưa có ai lọt top cả", color=ERROR_COLOR))
    medals = {1: "Top 1", 2: "Top 2", 3: "Top 3"}
    unit = "trận thắng" if k == "wins" else COIN_EMOJI
    lines = [f"{medals.get(i, f'**#{i}**')} <@{u}> — **{d.get(k)}** {unit}" for i, (u, d) in enumerate(sorted_u, 1)]
    title = f"{HEART} Top Đại Gia Yui Coin" if k == "coins" else f"{HEART} Top Cao Thủ Nối Từ"
    await interaction.response.send_message(embed=make_embed("\n".join(lines), title=title))

@bot.tree.command(name="give", description="Chuyển Yui Coin cho người khác (giới hạn 5,000,000/ngày)")
@app_commands.describe(member="Người nhận tiền", amount="Số tiền muốn chuyển (có thể gõ all để chuyển hết ví)")
async def give(interaction: discord.Interaction, member: discord.Member, amount: str):
    giver, receiver = interaction.user, member
    if receiver.id == giver.id:
        return await interaction.response.send_message(embed=make_embed(f"Cậu hổng thể tự chuyển tiền cho chính mình đâu! {HEART}", color=ERROR_COLOR), ephemeral=True)
    if receiver.bot:
        return await interaction.response.send_message(embed=make_embed("Hổng thể chuyển tiền cho bot được đâu nha! :3", color=ERROR_COLOR), ephemeral=True)

    uid, rid = str(giver.id), str(receiver.id)
    await bot.ensure_user(uid)
    await bot.ensure_user(rid)

    balance = bot.yui_db[uid]["coins"]
    send_amount = parse_bet_amount(amount, balance)
    if send_amount is None or send_amount <= 0:
        return await interaction.response.send_message(embed=make_embed("Số tiền không hợp lệ, thử lại nha! :3", color=ERROR_COLOR), ephemeral=True)
    if send_amount > balance:
        return await interaction.response.send_message(embed=make_embed(f"Cậu hổng đủ tiền đâu! Ví hiện có **{balance:,}** {COIN_EMOJI}", color=ERROR_COLOR), ephemeral=True)

    today = get_vn_today()
    if bot.yui_db[uid].get("give_date") != today:
        bot.yui_db[uid]["give_date"], bot.yui_db[uid]["give_today"] = today, 0
    given_today = bot.yui_db[uid].get("give_today", 0)

    if given_today + send_amount > GIVE_DAILY_LIMIT:
        remain = max(GIVE_DAILY_LIMIT - given_today, 0)
        return await interaction.response.send_message(embed=make_embed(f"Cậu chỉ được chuyển tối đa **{GIVE_DAILY_LIMIT:,}** {COIN_EMOJI} mỗi ngày thôi!\nHôm nay cậu còn chuyển được: **{remain:,}** {COIN_EMOJI}", color=ERROR_COLOR), ephemeral=True)

    async with bot.db_lock:
        bot.yui_db[uid]["coins"] -= send_amount
        bot.yui_db[uid]["give_today"] = given_today + send_amount
        bot.yui_db[rid]["coins"] += send_amount
    asyncio.create_task(bot.save_db())

    await interaction.response.send_message(embed=make_embed(f"{giver.mention} đã chuyển **{send_amount:,}** {COIN_EMOJI} cho {receiver.mention}! {HEART}", title=f"{HEART} Chuyển Khoản Thành Công"))

@bot.tree.command(name="mine", description="Chơi Dò Mìn - dò ô an toàn để nhân thưởng, cẩn thận trúng mìn nha!")
@app_commands.describe(bet="Số tiền cược (tối đa 250,000 - gõ all để cược mức tối đa)", mines=f"Số lượng mìn ({MINES_MIN_MINES}-{MINES_MAX_MINES})")
@app_commands.checks.cooldown(1, GAME_COOLDOWN_SECONDS, key=lambda i: i.user.id)
async def mine_game(interaction: discord.Interaction, bet: str, mines: app_commands.Range[int, MINES_MIN_MINES, MINES_MAX_MINES]):
    uid = str(interaction.user.id)
    await bot.ensure_user(uid)

    if interaction.user.id in active_mines_players:
        return await interaction.response.send_message(embed=make_embed("Cậu đang có một ván Dò Mìn khác chưa xong nè! :3", color=ERROR_COLOR), ephemeral=True)

    balance = bot.yui_db[uid]["coins"]
    bet_amount = parse_bet_amount(bet, balance, max_cap=MINES_MAX_BET)

    if bet_amount is None or bet_amount <= 0:
        return await interaction.response.send_message(embed=make_embed("Số tiền cược không hợp lệ, thử lại nha! :3", color=ERROR_COLOR), ephemeral=True)
    if bet_amount > balance:
        return await interaction.response.send_message(embed=make_embed(f"Cậu hổng đủ tiền cược đâu! Ví hiện có **{balance:,}** {COIN_EMOJI}", color=ERROR_COLOR), ephemeral=True)
    if bet_amount > MINES_MAX_BET:
        return await interaction.response.send_message(embed=make_embed(f"Cậu chỉ được cược tối đa **{MINES_MAX_BET:,}** {COIN_EMOJI} thôi nha!", color=ERROR_COLOR), ephemeral=True)

    async with bot.db_lock: bot.yui_db[uid]["coins"] -= bet_amount
    asyncio.create_task(bot.save_db())

    active_mines_players.add(interaction.user.id)
    view = MinesView(interaction.user, bet_amount, mines)
    try:
        await interaction.response.send_message(embed=view.build_embed(status="playing"), view=view)
        view.message = await interaction.original_response()
    except Exception as e:
        active_mines_players.discard(interaction.user.id)
        async with bot.db_lock: bot.yui_db[uid]["coins"] += bet_amount
        asyncio.create_task(bot.save_db())
        log(f"Lỗi khi mở ván mine: {e}", "warn")

@bot.tree.command(name="coinflip", description="Tung đồng xu, đoán mặt Ngửa/Sấp để x2 tiền cược!")
@app_commands.describe(bet="Số tiền cược (gõ all để cược hết ví)", mat="Đoán đồng xu sẽ rơi mặt nào")
@app_commands.choices(mat=[Choice(name="Ngửa (Heads)", value="heads"), Choice(name="Sấp (Tails)", value="tails")])
@app_commands.checks.cooldown(1, GAME_COOLDOWN_SECONDS, key=lambda i: i.user.id)
async def coinflip(interaction: discord.Interaction, bet: str, mat: Choice[str]):
    uid = str(interaction.user.id)
    await bot.ensure_user(uid)

    balance = bot.yui_db[uid]["coins"]
    bet_amount = parse_bet_amount(bet, balance, max_cap=COINFLIP_MAX_BET)
    if bet_amount is None or bet_amount <= 0:
        return await interaction.response.send_message(embed=make_embed("Số tiền cược không hợp lệ, thử lại nha! :3", color=ERROR_COLOR), ephemeral=True)
    if bet_amount > balance:
        return await interaction.response.send_message(embed=make_embed(f"Cậu hổng đủ tiền cược đâu! Ví hiện có **{balance:,}** {COIN_EMOJI}", color=ERROR_COLOR), ephemeral=True)
    if bet_amount > COINFLIP_MAX_BET:
        return await interaction.response.send_message(embed=make_embed(f"Cậu chỉ được cược tối đa **{COINFLIP_MAX_BET:,}** {COIN_EMOJI} thôi nha!", color=ERROR_COLOR), ephemeral=True)

    async with bot.db_lock: bot.yui_db[uid]["coins"] -= bet_amount
    asyncio.create_task(bot.save_db())

    pick_label = "Ngửa" if mat.value == "heads" else "Sấp"
    spin_embed = make_embed(
        f"{interaction.user.mention} cược **{bet_amount:,}** {COIN_EMOJI} và chọn **{pick_label}**\nĐồng xu đang tung... {COINFLIP_SPIN_EMOJI}",
        title=f"{HEART} Tung Đồng Xu",
    )
    spin_embed.set_thumbnail(url=COINFLIP_SPIN_GIF_URL)
    await interaction.response.send_message(embed=spin_embed)

    await asyncio.sleep(5)

    result = random.choice(["heads", "tails"])
    result_label = "Ngửa" if result == "heads" else "Sấp"
    result_emoji = COINFLIP_HEAD_EMOJI if result == "heads" else COINFLIP_TAIL_EMOJI
    won = result == mat.value

    if won:
        payout = bet_amount * 2
        async with bot.db_lock: bot.yui_db[uid]["coins"] += payout
        asyncio.create_task(bot.save_db())
        text = f"Đồng xu rơi trúng mặt **{result_label}** {result_emoji}! Cậu **THẮNG {payout:,}** {COIN_EMOJI} rồi! {HEART}"
        color = EMBED_COLOR
    else:
        text = f"Đồng xu rơi trúng mặt **{result_label}** {result_emoji}... Cậu mất hết **{bet_amount:,}** {COIN_EMOJI} rồi :c"
        color = ERROR_COLOR

    result_img = COINFLIP_HEAD_IMG_URL if result == "heads" else COINFLIP_TAIL_IMG_URL
    result_embed = make_embed(text, title=f"{HEART} Kết Quả Tung Đồng Xu", color=color)
    result_embed.set_thumbnail(url=result_img)
    await interaction.edit_original_response(embed=result_embed)

@bot.tree.command(name="noitu", description="Bắt đầu ván game nối từ cùng Yui nè :3")
async def start_noitu(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    async with get_game_lock(channel_id):
        existing = games.get(channel_id)
        if existing:
            w1, w2 = existing['current']
            await interaction.response.send_message(
                f"Đang có ván nối từ chưa xong nè! Tiếp chữ `{w2}` đi, hoặc `/noitu_stop` nếu muốn dừng lại nha :3",
                ephemeral=True,
            )
            return
        w1, w2 = get_random_start_word()
        games[channel_id] = {'history': [f"{w1} {w2}"], 'current': (w1, w2), 'last_author_id': None}
    await interaction.response.send_message(f"Yui mở màn: **{w1} {w2}** :3\nTiếp chữ `{w2}` đi!")

@bot.tree.command(name="noitu_stop", description="Dừng chơi nối từ :3")
async def stop_noitu(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    async with get_game_lock(channel_id):
        if channel_id in games:
            del games[channel_id]
            await interaction.response.send_message("Yui dẹp bàn nối từ rồi nha! :3")
        else: await interaction.response.send_message("Ơ có chơi đâu mà dừng!")

@bot.tree.command(name="thongbao", description="Bật/tắt thông báo Yui chào khi có người ra vào phòng voice (cần quyền Manage Server)")
@app_commands.describe(trang_thai="Bật hay tắt thông báo cho cả server")
@app_commands.choices(trang_thai=[Choice(name="Bật", value="on"), Choice(name="Tắt", value="off")])
@app_commands.checks.has_permissions(manage_guild=True)
async def toggle_notify(interaction: discord.Interaction, trang_thai: Choice[str]):
    guild_id = interaction.guild_id
    if trang_thai.value == "off":
        disabled_notify_guilds.add(guild_id)
        msg = "Yui im re, hổng chào ai ra vào phòng voice nữa nha! :3"
    else:
        disabled_notify_guilds.discard(guild_id)
        msg = "Yui lại chào hỏi mọi người ra vào phòng voice rồi nha! :3"
    await interaction.response.send_message(embed=make_embed(msg))

@toggle_notify.error
async def toggle_notify_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(embed=make_embed("Cậu cần quyền Manage Server mới đổi được cái này nha!", color=ERROR_COLOR), ephemeral=True)
    else:
        raise error

# ==============================================================================
# ── /HELP ─────────────────────────────────────────────────────────────────────
# ==============================================================================

HELP_CATEGORIES = {
    "essential": ("🎸 Nhạc (Essential)", "Phát nhạc, hàng chờ, tua bài...", ["play", "skip", "pause", "resume", "queue", "nowplaying", "loop", "shuffle", "remove", "stop"]),
    "economy":   ("💰 Kinh Tế (Economy)", "Ví Yui Coin, điểm danh, bxh...", ["daily", "cash", "top", "give"]),
    "profile":   ("🖼️ Hồ Sơ (Profile)", "Xem avatar, banner cá nhân & server", ["avatar", "banner"]),
    "game":      ("🔤 Trò Chơi (Game)", "Nối từ, cá cược cùng Yui...", ["mine", "coinflip", "noitu", "noitu_stop"]),
    "setup":     ("⚙️ Cài Đặt (Setup)", "Cấu hình Yui trong Server", ["thongbao"]),
}

def _help_category_embed(key: str) -> discord.Embed:
    label, _desc, cmd_names = HELP_CATEGORIES[key]
    lines = []
    for name in cmd_names:
        cmd = bot.tree.get_command(name)
        desc = cmd.description if cmd else "?"
        lines.append(f"**/{name}**\nMô tả: {desc}")
    return make_embed("\n\n".join(lines), title=f"{HEART} {label}")

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, description=desc, value=key)
            for key, (label, desc, _cmds) in HELP_CATEGORIES.items()
        ]
        super().__init__(placeholder="Chọn danh mục lệnh muốn xem...", options=options)

    async def callback(self, interaction: discord.Interaction):
        set_footer_guild(interaction.guild)
        await interaction.response.edit_message(embed=_help_category_embed(self.values[0]), view=self.view)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpSelect())

@bot.tree.command(name="help", description="Xem danh sách lệnh của Yui theo từng danh mục")
async def help_cmd(interaction: discord.Interaction):
    embed = make_embed(
        "Chọn 1 danh mục ở menu bên dưới để xem các lệnh trong đó nha :3",
        title=f"{HEART} Danh sách các lệnh của Yui",
    )
    await interaction.response.send_message(embed=embed, view=HelpView())

@bot.tree.command(name="quest", description="Gọi Yui ra cày Auto Quest nè 🥰")
@app_commands.describe(token="Đưa Token đây nè (Tuyệt đối bảo mật nha)", mode="Chọn tốc độ chạy nhiệm vụ")
@app_commands.choices(mode=[
    Choice(name="Siêu tốc (Làm liên tục)", value="fast"),
    Choice(name="An toàn (Nghỉ 1-3 tiếng)", value="slow")
])
async def quest_command(interaction: discord.Interaction, token: str, mode: Choice[str]):
    if interaction.guild_id != 1535278578155921420: 
        return await interaction.response.send_message(embed=make_embed(f"Yui chỉ được phép làm việc ở trong phòng câu lạc bộ của Keyl thôi! {HEART}", title=f"{HEART} Hổng được đâu ạ! {HEART}", color=ERROR_COLOR, gif=True), ephemeral=True)
    is_keyl = (interaction.user.id == 1147592525696204822)
    desc = f"Trước khi Yui xắn tay áo lên cày quest, Keyl nhớ đọc nha:\n\n{HEART} Yui chỉ mượn Token để chạy nhiệm vụ thôi.\n{HEART} Làm xong là Yui vứt Token đi liền, an tâm tuyệt đối nha!\n\nBấm nút xanh bên dưới để Yui làm việc nha :3" if is_keyl else f"Chào đằng ấy!\n\n{HEART} Yui chỉ mượn Token để chạy nhiệm vụ thôi.\n{HEART} Làm xong là Yui vứt Token đi liền, an tâm tuyệt đối nha!\n\nBấm nút xanh bên dưới nhé :3"
    await interaction.response.send_message(embed=make_embed(desc, title=f"{HEART} Lời Dặn Dò Của Yui Hirasawa {HEART}", gif=True), view=ToSView(user_token=token, is_keyl=is_keyl, mode=mode.value), ephemeral=True)

@bot.tree.command(name="badge", description="Nâng cấp huy hiệu max ping: tuỳ chỉnh số game, số giờ + Fingerprint Bypass :3")
@app_commands.describe(games_count="Số game muốn cày (Mặc định 102)", hours_per_game="Số giờ mỗi game (Mặc định 50.0)")
async def badge_command(interaction: discord.Interaction, games_count: Optional[int] = 102, hours_per_game: Optional[float] = 50.0):
    if interaction.guild_id != 1535278578155921420: 
        return await interaction.response.send_message(embed=make_embed(f"Tính năng này vợ chỉ để phục vụ ở phòng câu lạc bộ thôi nha! :3", title=f"{HEART} Lạc đường rồi! {HEART}", color=ERROR_COLOR, gif=True), ephemeral=True)
    
    games_count = max(1, min(150, games_count))
    hours_per_game = max(0.1, hours_per_game)
    
    await interaction.response.send_modal(UltimateBadgeModal(games_count, hours_per_game))

@bot.tree.command(name="hypesquad", description="Gán hoặc đổi huy hiệu HypeSquad cho tài khoản :3")
@app_commands.describe(token="Đưa chìa khóa (Token)", house="Chọn nhà HypeSquad bạn muốn nhận")
@app_commands.choices(house=[Choice(name="Bravery (Dũng Cảm)", value="bravery"), Choice(name="Brilliance (Kiệt Xuất)", value="brilliance"), Choice(name="Balance (Cân Bằng)", value="balance"), Choice(name="Gỡ HypeSquad", value="leave")])
async def hypesquad_command(interaction: discord.Interaction, token: str, house: Choice[str]):
    if interaction.guild_id != 1535278578155921420: 
        return await interaction.response.send_message(embed=make_embed("Yui chỉ hỗ trợ trong Câu lạc bộ thôi nha :3", title=f"{HEART} Hổng được đâu ạ! {HEART}", color=ERROR_COLOR), ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    success, msg = await asyncio.to_thread(set_hypesquad_house, token, house.value)
    await interaction.followup.send(embed=make_embed(msg, title=f"{HEART} Nhận Huy Hiệu Thành Công! {HEART}" if success else f"{HEART} Thao tác thất bại {HEART}", color=EMBED_COLOR if success else ERROR_COLOR, gif=success), ephemeral=True)

# ==============================================================================
# ── KEEPALIVE ─────────────────────────────────────────────────────────────────
# ==============================================================================

app = Flask('')
@app.route('/')
def home(): return "Yui is running!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive():
    if os.environ.get("ENABLE_KEEPALIVE", "0") == "1": Thread(target=run, daemon=True).start()

async def run_bot_with_backoff():
    token = os.getenv('BOT_TOKEN')
    if not token: return log("BOT_TOKEN is missing", "error")
    try: await bot.start(token)
    except Exception as e: log(f"Discord error: {e}", "error")

if __name__ == "__main__":
    keep_alive()
    asyncio.run(run_bot_with_backoff())
