import discord
from discord.ext import commands
from discord import app_commands
import random
import hashlib
import asyncio
import requests
from typing import Optional
from datetime import datetime, timedelta, timezone

def log(msg: str, level: str = "info"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{ts} [{level.upper()}] (fun_cog) {msg}")

HEART = "<a:klg23:1535400172199350332>"
EMBED_COLOR = 0xffb6c1
FOOTER_TEXT = "Yui Hirasawa • Câu lạc bộ Nhạc Nhẹ"

GIF_LIST = [
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExbTdibGIxbW82N2RleWpyYnk3aXRwaWY1NHRhamhmMHh6Y211bHZlcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/KTG2uX8CHJdIs/giphy.gif",
    "https://giffiles.alphacoders.com/215/215128.gif",
    "https://media.tenor.com/oQyiHReFBkAAAAAM/k-on-kon.gif",
    "https://i.kym-cdn.com/photos/images/original/002/161/679/2dd.gif",
    "https://media.tenor.com/TL2rTF5jqHoAAAAM/k-on-yui.gif",
]

def make_embed(description: str, *, title: str = None, color: int = EMBED_COLOR, gif: bool = False,
                guild: Optional[discord.Guild] = None) -> discord.Embed:
    embed = discord.Embed(description=description, color=color)
    if title:
        embed.title = title
    embed.set_footer(text=f"Yui Hirasawa • {guild.name}" if guild else FOOTER_TEXT)
    if gif:
        embed.set_thumbnail(url=random.choice(GIF_LIST))
    return embed

VN_TZ = timezone(timedelta(hours=7))

# key: f"{caller_id}-{target_id}-{cmd_name}" -> date_str
_daily_seen: dict[str, str] = {}

def get_vn_date_str() -> str:
    now_vn = datetime.now(VN_TZ)
    shifted_time = now_vn - timedelta(hours=6)
    return shifted_time.strftime("%Y-%m-%d")

def seeded_value(user_id: int, cmd_name: str, low: int, high: int) -> int:
    """Kết quả ổn định trong ngày, reset lúc 6:00 sáng giờ VN."""
    date_str = get_vn_date_str()
    seed_str = f"{user_id}-{cmd_name}-{date_str}"
    digest = hashlib.sha256(seed_str.encode()).hexdigest()
    span = high - low + 1
    return low + (int(digest, 16) % span)

def get_repeat_note(caller_id: int, target_id: int, cmd_name: str) -> str:
    date_str = get_vn_date_str()
    key = f"{caller_id}-{target_id}-{cmd_name}"
    is_repeat = _daily_seen.get(key) == date_str
    _daily_seen[key] = date_str
    if is_repeat:
        return "\n\n-# ⚠️ Kết quả này đã cố định cho hôm nay rồi, 6:00 sáng mai mới đổi được nha!"
    return ""

def pick_comment(value: int, tiers: list[tuple[int, str]]) -> str:
    result = tiers[0][1]
    for threshold, text in tiers:
        if value >= threshold:
            result = text
    return result

# ==============================================================================
# ── CẤU HÌNH API LẤY GIF ──────────────────────────────────────────────────────
# ==============================================================================

WAIFU_PICS_BASE = "https://api.waifu.pics/sfw"
NEKOS_BEST_BASE = "https://nekos.best/api/v2"

# Danh sách category hợp lệ của từng API để tránh gọi bậy ăn 404
WAIFU_CATEGORIES = {
    "bite", "blush", "bonk", "bully", "cringe", "cry", "cuddle", "dance", 
    "glomp", "handhold", "happy", "highfive", "hug", "kick", "kill", "kiss", 
    "lick", "nom", "pat", "poke", "slap", "smile", "smug", "wave", "wink", "yeet"
}
NEKOS_CATEGORIES = {
    "baka", "bite", "blush", "bored", "cry", "cuddle", "dance", "facepalm", 
    "feed", "handhold", "happy", "highfive", "hug", "kick", "kiss", "laugh", 
    "nod", "nom", "nope", "pat", "poke", "pout", "punch", "shoot", "shrug", 
    "slap", "sleep", "smile", "smug", "stare", "think", "thumbsup", "tickle", "wave", "wink", "yeet"
}

KILL_GIFS = ["https://media1.tenor.com/m/aZwNR4sZRvUAAAAd/anime-wasted.gif"]
BULLY_GIFS = ["https://media1.tenor.com/m/vBQRaCv6nhkAAAAd/anime-bully.gif"]

# ── CACHE GIF theo (source, category) để né gọi API thật khi bị rate-limit ──
GIF_CACHE_MAX = 30
_gif_cache: dict[str, list[str]] = {}

def _cache_key(source: str, category: str) -> str:
    return f"{source}-{category}"

def _cache_add(source: str, category: str, url: str) -> None:
    key = _cache_key(source, category)
    bucket = _gif_cache.setdefault(key, [])
    if url in bucket:
        bucket.remove(url)
    bucket.append(url)
    if len(bucket) > GIF_CACHE_MAX:
        del bucket[0]

def _cache_pick(source: str, category: str) -> Optional[str]:
    bucket = _gif_cache.get(_cache_key(source, category))
    return random.choice(bucket) if bucket else None

def _fetch_gif_sync(source: str, category: str) -> Optional[str]:
    base = WAIFU_PICS_BASE if source == "waifu" else NEKOS_BEST_BASE
    try:
        r = requests.get(f"{base}/{category}", timeout=6)
        if r.status_code == 429:
            log(f"RATE LIMITED [{source}/{category}] status=429", level="warn")
            return None
        if r.status_code != 200:
            log(f"Fetch fail [{source}/{category}] status={r.status_code}", level="warn")
            return None
        if source == "waifu":
            url = r.json().get("url")
        else:
            res = r.json().get("results")
            url = res[0].get("url") if res else None
        if url:
            _cache_add(source, category, url)
        return url
    except Exception as e:
        log(f"Fetch error [{source}/{category}]: {e}", level="error")
        return None

async def fetch_action_gif(source: str, category: str) -> Optional[str]:
    url = await asyncio.to_thread(_fetch_gif_sync, source, category)
    if url:
        return url

    # Chỉ gọi API kia nếu API đó thực sự hỗ trợ danh mục này
    other = "nekos" if source == "waifu" else "waifu"
    valid_set = NEKOS_CATEGORIES if other == "nekos" else WAIFU_CATEGORIES
    if category in valid_set:
        url = await asyncio.to_thread(_fetch_gif_sync, other, category)
        if url:
            return url

    # Cả 2 nguồn đều fail (thường là do rate limit) → lấy tạm từ cache
    # thay vì gọi lại API, né spam thêm request khi đang bị limit
    cached = _cache_pick(source, category) or _cache_pick(other, category)
    if cached:
        log(f"Using cached gif [{source}/{category}] (API unavailable)", level="warn")
        return cached
    return None

ACTIONS: dict[str, dict] = {
    "hug": {"source": "waifu", "category": "hug", "lines": ["{a} lao vào ôm chầm lấy {b}", "{a} đè {b} ra ôm cứng ngắc, đéo cho thoát!"]},
    "cuddle": {"source": "waifu", "category": "cuddle", "lines": ["{a} rúc vào người {b} cọ cọ như con cờ hó!", "{a} dụi dụi vào người {b} tởm vãi lều!"]},
    "kiss": {"source": "waifu", "category": "kiss", "lines": ["{a} đè {b} ra bú mỏ chùn chụt!", "{a} cưỡng hôn {b} ướt nhẹp cmn hết cái mặt!"]},
    "pat": {"source": "waifu", "category": "pat", "lines": ["{a} xoa đầu {b} như xoa đầu cún!", "{a} vuốt ve cái đầu ngu ngốc của {b}!"]},
    "slap": {"source": "waifu", "category": "slap", "lines": ["{a} vả vỡ mẹ mõm {b}!", "{a} tát lật cmn mặt {b}, chừa cái thói láo cá chó đi!"]},
    "kill": {"source": "nekos", "category": "kick", "lines": ["{a} xiên chết cụ {b}!", "{a} tiễn {b} về chầu ông bà cmnl!"], "static_fallback": KILL_GIFS},
    "bully": {"source": "waifu", "category": "bully", "lines": ["{a} đè cổ {b} ra bắt nạt!", "{a} hành {b} ra bã, khóc cmn đi!"], "fallback": ("nekos", "smug"), "static_fallback": BULLY_GIFS},
    "bonk": {"source": "waifu", "category": "bonk", "lines": ["{a} táng vỡ cmn sọ {b}!", "{a} gõ u đầu {b}!"]},
    "poke": {"source": "waifu", "category": "poke", "lines": ["{a} chọc lủng cmn má {b}!", "{a} lấy ngón tay chọt chọt trêu chó {b}!"]},
    "highfive": {"source": "waifu", "category": "highfive", "lines": ["{a} đập tay {b} cái chát đau điếng cmn tay!", "{a} đập tay với {b} bung cmn móng!"]},
    "handhold": {"source": "waifu", "category": "handhold", "lines": ["{a} nắm chặt tay {b} đéo buông, ớn lạnh vãi!", "{a} đan tay {b} sến súa vãi cớt!"]},
    "tickle": {"source": "nekos", "category": "tickle", "lines": ["{a} thò tay móc nách cù léc {b} cười sặc cmn cứt!", "{a} cù léc {b} giãy đành đạch như chó dại!"]},
    "cry": {"source": "waifu", "category": "cry", "lines": ["{a} khóc rống lên bám áo {b} ăn vạ!", "{a} rớt nước mắt cá sấu ướt cmn áo {b}!"]},
    "dance": {"source": "waifu", "category": "dance", "lines": ["{a} kéo {b} lên nhảy múa quạt như thằng ngáo đá!", "{a} và {b} quẩy tung cmn nóc, sập mẹ sàn rồi!"]},
    "lick": {"source": "waifu", "category": "lick", "lines": ["{a} liếm cmn một phát vào mặt {b}, dơ vãi lều!", "{a} thè lưỡi liếm {b} cái chóc, hư thấy mẹ!"]},
    "nom": {"source": "waifu", "category": "nom", "lines": ["{a} ngoạm cmn một miếng {b}, ngon vãi cả cứt!", "{a} cắn nghiến {b} như cẩu đói ba ngày!"]},
    "stare": {"source": "nekos", "category": "stare", "lines": ["{a} trợn mắt nhìn {b} như nhìn thứ ba đầu sáu tay!", "{a} nhìn {b} chằm chằm, dòm cái gì mà dòm lắm thế?!"]},
    "greet": {"source": "waifu", "category": "wave", "lines": ["{a} vẫy tay chào {b} như thằng dở hơi!", "{a} cúi đầu chào {b}, giả trân vừa thôi!"]},
    "punch": {"source": "nekos", "category": "punch", "lines": ["{a} đấm vỡ mẹ mồm {b}!", "{a} nện {b} một cú trời giáng, gãy cmn răng luôn!"]},
    "pats": {"source": "waifu", "category": "pat", "lines": ["{a} vỗ vỗ liên tục lên đầu {b} như đập muỗi!", "{a} xoa đầu {b} không ngừng nghỉ, ngứa tay vãi!"]},
    "snuggle": {"source": "waifu", "category": "cuddle", "lines": ["{a} rúc sát vào {b} như con đỉa bám!", "{a} chui tọt vào lòng {b}, đéo chịu ra!"]},
}

class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _soi_embed(self, title: str, user: discord.abc.User, percentage: int,
                    comment: str, emoji: str = "📊", note: str = "", guild: Optional[discord.Guild] = None) -> discord.Embed:
        desc = (
            f"Tới công chuyện với {user.mention} 🤡\n\n"
            f"{emoji} **Kết quả**\n{percentage}%\n\n"
            f"💬 **Phán**\n{comment}"
            f"{note}"
        )
        embed = make_embed(desc, title=f"{HEART} {title}", guild=guild)
        embed.set_thumbnail(url=user.display_avatar.url)
        return embed

    async def _interact(self, interaction: discord.Interaction, action_key: str, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message("Bắt buộc phải tag người khác cơ mà, tự tag mình chi vậy trời :3", ephemeral=True)
            return

        await interaction.response.defer()
        cfg = ACTIONS.get(action_key)
        if not cfg: return
        actor, target = interaction.user, member

        gif_url = await fetch_action_gif(cfg["source"], cfg["category"])
        if not gif_url and cfg.get("fallback"): 
            gif_url = await fetch_action_gif(*cfg["fallback"])
        if not gif_url and cfg.get("static_fallback"): 
            gif_url = random.choice(cfg["static_fallback"])

        desc = random.choice(cfg["lines"]).format(a=actor.mention, b=target.mention)
        embed = make_embed(desc, guild=interaction.guild)
        embed.set_image(url=gif_url or random.choice(GIF_LIST))
        await interaction.followup.send(embed=embed)

    # ── TƯƠNG TÁC (ACTIONS) ───────────────────────────────────────────
    
    @app_commands.command(name="hug", description="Ôm 1 đứa thật chặt 🤗")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def hug(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "hug", member)

    @app_commands.command(name="cuddle", description="Cọ cọ vào người 1 đứa 🥰")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def cuddle(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "cuddle", member)

    @app_commands.command(name="kiss", description="Bú mỏ 1 đứa 💋")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def kiss(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "kiss", member)

    @app_commands.command(name="pat", description="Xoa đầu 1 đứa ngốc 🖐️")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def pat(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "pat", member)

    @app_commands.command(name="slap", description="Tát 1 đứa lật mặt 👋")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slap(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "slap", member)

    @app_commands.command(name="kill", description="Tiễn 1 đứa lên bảng đếm số")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def kill(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "kill", member)
        
    @app_commands.command(name="bully", description="Hành xác 1 đứa 🤡")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def bully(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "bully", member)
        
    @app_commands.command(name="bonk", description="Gõ đầu 1 đứa cho chừa 🔨")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def bonk(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "bonk", member)
        
    @app_commands.command(name="poke", description="Chọc ngoáy 1 đứa 👉")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def poke(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "poke", member)
        
    @app_commands.command(name="highfive", description="Đập tay mẻ xương 🙌")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def highfive(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "highfive", member)
        
    @app_commands.command(name="handhold", description="Nắm chặt tay 1 đứa 🤝")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def handhold(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "handhold", member)
        
    @app_commands.command(name="tickle", description="Cù léc 1 đứa sặc luôn 🤣")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def tickle(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "tickle", member)
        
    @app_commands.command(name="cry", description="Ăn vạ 1 đứa 😭")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def cry(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "cry", member)
        
    @app_commands.command(name="dance", description="Kéo 1 đứa lên múa quạt 💃")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def dance(self, interaction: discord.Interaction, member: discord.Member): 
        await self._interact(interaction, "dance", member)

    @app_commands.command(name="lick", description="Liếm 1 đứa cho dơ luôn 👅")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def lick(self, interaction: discord.Interaction, member: discord.Member):
        await self._interact(interaction, "lick", member)

    @app_commands.command(name="nom", description="Cắn ngấu nghiến 1 đứa 😋")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def nom(self, interaction: discord.Interaction, member: discord.Member):
        await self._interact(interaction, "nom", member)

    @app_commands.command(name="stare", description="Trợn mắt nhìn 1 đứa 👀")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def stare(self, interaction: discord.Interaction, member: discord.Member):
        await self._interact(interaction, "stare", member)

    @app_commands.command(name="greet", description="Vẫy tay chào 1 đứa 👋")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def greet(self, interaction: discord.Interaction, member: discord.Member):
        await self._interact(interaction, "greet", member)

    @app_commands.command(name="punch", description="Đấm 1 đứa cho tỉnh 🥊")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def punch(self, interaction: discord.Interaction, member: discord.Member):
        await self._interact(interaction, "punch", member)

    @app_commands.command(name="pats", description="Vỗ về 1 đứa liên tục 🖐️✨")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def pats(self, interaction: discord.Interaction, member: discord.Member):
        await self._interact(interaction, "pats", member)

    @app_commands.command(name="snuggle", description="Rúc sát vào 1 đứa 🐣")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def snuggle(self, interaction: discord.Interaction, member: discord.Member):
        await self._interact(interaction, "snuggle", member)

    # ── /soichieucao ──────────────────────────────────────────────────
    @app_commands.command(name="soichieucao", description="Đo chiều cao xem lùn cỡ nào 📏")
    @app_commands.describe(member="Mục tiêu bị soi")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def soichieucao(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        cm = seeded_value(target.id, "soichieucao", 140, 195)
        note = get_repeat_note(interaction.user.id, target.id, "soichieucao")
        tiers = [
            (140, "Lùn tịt như cây nấm, ra đường cẩn thận kẻo bị đạp trúng! 🍄"),
            (155, "Chiều cao này thì với đồ trên cao không được mà chui gầm giường cũng bị kẹt. 🗿"),
            (165, "Bình thường vãi chưởng, ném vào đám đông là tàng hình luôn không ai thèm ngó. 🥱"),
            (180, "Cái sào chọc cứt à? Cao quá cẩn thận đi đập đầu vào cửa sổ đấy! 🦒"),
        ]
        comment = pick_comment(cm, tiers)
        desc = (
            f"Soi thử {target.mention} coi\n\n"
            f"📏 **Chiều cao**\n{cm} cm\n\n"
            f"💬 **Phán**\n{comment}"
            f"{note}"
        )
        embed = make_embed(desc, title=f"{HEART} Máy soi chiều cao", guild=interaction.guild)
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ── /soidaden ─────────────────────────────────────────────────────
    @app_commands.command(name="soidaden", description="Máy soi Có Quyền Công Dân không")
    @app_commands.describe(member="Mục tiêu bị soi")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def soidaden(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        roll = seeded_value(target.id, "soidaden", 0, 1)
        note = get_repeat_note(interaction.user.id, target.id, "soidaden")
        if roll == 1:
            result = "CÓ ✅"
            comment_pool = [
                "Trắng trẻo sạch sẽ phết, qua vòng gửi xe, tạm chấp nhận cho hít chung bầu không khí. 🐔",
                "Quyền công dân full HD, nói chung là nhân phẩm hôm nay độ còng lưng! 📄",
            ]
        else:
            result = "KHÔNG ❌"
            comment_pool = [
                "Đen như tiền đồ của chị Dậu, cúp điện phát là tàng hình mẹ luôn! 🌚",
                "Hồ sơ trống trơn, chắc đang ở chế độ ẩn danh trong hệ thống. 👻",
                "Quét ba lần vẫn không ra kết quả, chịu thua luôn. 🌚",
            ]
        comment = comment_pool[seeded_value(target.id, "soidaden_c", 0, len(comment_pool) - 1)]
        desc = (
            f"Hồ sơ của {target.mention}\n\n"
            f"🪪 **Quyền công dân**\n{result}\n\n"
            f"💬 **Phán**\n{comment}"
            f"{note}"
        )
        embed = make_embed(desc, title=f"{HEART} Check Công Dân", guild=interaction.guild)
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ── /soideptrai ───────────────────────────────────────────────────
    @app_commands.command(name="soideptrai", description="Đo nhan sắc xem có xúc phạm người nhìn không 😎")
    @app_commands.describe(member="Mục tiêu bị soi")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def soideptrai(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        pct = seeded_value(target.id, "soideptrai", 0, 100)
        note = get_repeat_note(interaction.user.id, target.id, "soideptrai")
        tiers = [
            (0, "Nhan sắc xúc phạm thị giác, ra đường nhớ đội bao bố. 🤢"),
            (30, "Mặt tiền phèn chua, nhan sắc cỡ này chắc ế mốc meo cmnr. 📉"),
            (60, "Tạm được, nhìn không đến nỗi khó chịu. 🙄"),
            (85, "Nhan sắc hơi bị ảo ma đấy, chắc chắn là trap boy. ✨"),
        ]
        comment = pick_comment(pct, tiers)
        embed = self._soi_embed("Máy soi NHAN SẮC", target, pct, comment, "😎", note, guild=interaction.guild)
        await interaction.response.send_message(embed=embed)

    # ── /soidodethuong ────────────────────────────────────────────────
    @app_commands.command(name="soidodethuong", description="Đo độ thảo mai dễ thương 🐹")
    @app_commands.describe(member="Mục tiêu bị soi")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def soidodethuong(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        pct = seeded_value(target.id, "soidodethuong", 0, 100)
        note = get_repeat_note(interaction.user.id, target.id, "soidodethuong")
        tiers = [
            (0, "Mặt lạnh như đá, nhìn là thấy ghét, lượn ra chỗ khác chơi! 🐍"),
            (30, "Dễ thương cái nỗi gì, cố làm nũng nhìn chỉ muốn đấm cho nhát! 👊"),
            (60, "Cũng có tí đáng yêu đấy, nhưng che cái nết hãm lại thì tốt hơn. 🤡"),
            (85, "Dễ thương max lv, dạo này xài bùa ngải gì mà nhìn cuốn thế hả? 🍰"),
        ]
        comment = pick_comment(pct, tiers)
        embed = self._soi_embed("Máy soi ĐỘ CUTE", target, pct, comment, "🐹", note, guild=interaction.guild)
        await interaction.response.send_message(embed=embed)

    # ── /soidowibu ────────────────────────────────────────────────────
    @app_commands.command(name="soidowibu", description="Máy đo nồng độ chúa tể bóng tối 🎌")
    @app_commands.describe(member="Mục tiêu bị soi")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def soidowibu(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        pct = seeded_value(target.id, "soidowibu", 0, 100)
        note = get_repeat_note(interaction.user.id, target.id, "soidowibu")
        tiers = [
            (0, "Tấm chiếu mới, mầm non đất nước chưa bị văn hóa 2D tẩy não. 🌤️"),
            (30, "Mới tập đú anime theo phong trào thôi chứ biết cái vẹo gì! 📺"),
            (60, "Wibu rách, mở miệng ra là onii-chan nghe ung thư lỗ tai! 🤢"),
            (85, "Chúa tể bóng tối thức tỉnh, wibu chúa hết cứu! ☠️"),
        ]
        comment = pick_comment(pct, tiers)
        embed = self._soi_embed("Máy soi WIBU", target, pct, comment, "🎌", note, guild=interaction.guild)
        await interaction.response.send_message(embed=embed)

    # ── /soiiq ────────────────────────────────────────────────────────
    @app_commands.command(name="soiiq", description="Máy soi não 🧠")
    @app_commands.describe(member="Mục tiêu bị soi")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def soiiq(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        iq = seeded_value(target.id, "soiiq", 40, 160)
        note = get_repeat_note(interaction.user.id, target.id, "soiiq")
        tiers = [
            (40, "Não phẳng nếp nhăn tỉ lệ nghịch với tuổi tác, khỉ nó còn khôn hơn! 🐒"),
            (80, "IQ mức tạm ổn, đủ sống qua ngày không sao cả. 📉"),
            (110, "Não cũng chịu nhảy số đấy, đủ xài để không bị lừa bán qua biên giới. 🤔"),
            (140, "IQ đột biến mẹ rồi, thông minh thế này coi chừng người ngoài hành tinh tới bắt. 👽"),
        ]
        comment = pick_comment(iq, tiers)
        desc = (
            f"Kết quả scan não của {target.mention}\n\n"
            f"🧠 **Chỉ số IQ**\n{iq}\n\n"
            f"💬 **Phán**\n{comment}"
            f"{note}"
        )
        embed = make_embed(desc, title=f"{HEART} Trung Tâm Kiểm Tra Trí Tuệ", guild=interaction.guild)
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ── /soimayman ────────────────────────────────────────────────────
    @app_commands.command(name="soimayman", description="Xem hôm nay có bị giẫm cứt chó không 🍀")
    @app_commands.describe(member="Mục tiêu bị soi")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def soimayman(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        pct = seeded_value(target.id, "soimayman", 0, 100)
        note = get_repeat_note(interaction.user.id, target.id, "soimayman")
        tiers = [
            (0, "Tới thở cũng xui, nghiệp quật cmnr, hôm nay ra đường cẩn thận cứt chó! 💩"),
            (30, "Nhân phẩm tồi tàn, làm gì cũng hỏng, tốt nhất trùm mền đi ngủ đi. 🛌"),
            (60, "Vía tàm tạm, không xui nhưng cũng chả có gì đặc sắc. 😐"),
            (85, "Nhân phẩm bùng nổ, đi đánh con đề ngay còn kịp, trúng nhớ chia tao! 💸"),
        ]
        comment = pick_comment(pct, tiers)
        embed = self._soi_embed("Máy đo NHÂN PHẨM", target, pct, comment, "🍀", note, guild=interaction.guild)
        await interaction.response.send_message(embed=embed)

    # ── /soicu ────────────────────────────────────────────────────────
    @app_commands.command(name="soicu", description="Máy đo độ dài ciu (troll thôi, đừng nghiêm túc) 📏")
    @app_commands.describe(member="Mục tiêu bị soi")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def soicu(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        cm = seeded_value(target.id, "soicu", 3, 25)
        note = get_repeat_note(interaction.user.id, target.id, "soicu")
        tiers = [
            (3, "Bé tí xíu cỡ quả ớt hiểm, soi kính lúp lòi cả pha mới thấy. 🤣"),
            (10, "Cỡ cái xúc xích xông khói cắn dở, thôi thì ráng cày kỹ năng để bù đắp nha con gà! 😐"),
            (16, "Ngon nghẻ phết nhờ! Hàng họ xịn xò đấy, tự tin vác đi khè thiên hạ được rồi! 🍌🔥"),
            (21, "Ảo ma Canada! Khai thật đi m độn thêm cái gì vào đúng không? 😱"),
        ]
        comment = pick_comment(cm, tiers)
        desc = (
            f"Kết quả đo của {target.mention}\n\n"
            f"📏 **Số đo**\n{cm} cm\n\n"
            f"💬 **Phán**\n{comment}\n\n"
            f"-# Máy đo nhân phẩm thôi, thằng nào cay thằng đó nhột! 🤡"
            f"{note}"
        )
        # Đã bổ sung title còn thiếu
        embed = make_embed(desc, title=f"{HEART} Máy Đo Kích Thước", guild=interaction.guild)
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ── /hom-nay-an-gi ────────────────────────────────────────────────
    FOOD_MENU = {
        "Buổi sáng": {
            "main": ["Cháo sườn", "Bánh mì trứng", "Xôi gà", "Phở bò", "Bún riêu", "Bánh cuốn"],
            "side": ["Dưa lưới", "Sữa chua", "Chuối", "Táo", "Xoài"],
            "drink": ["Sữa đậu nành", "Cà phê sữa đá", "Trà đào", "Sinh tố bơ"],
        },
        "Buổi trưa": {
            "main": ["Cơm sườn", "Bún bò Huế", "Cơm gà xối mỡ", "Mì Quảng", "Bánh xèo", "Cơm tấm"],
            "side": ["Dưa hấu", "Chè đậu xanh", "Trái cây thập cẩm", "Sữa chua nếp cẩm"],
            "drink": ["Trà tắc", "Nước mía", "Trà sữa trân châu", "Nước cam"],
        },
        "Buổi tối": {
            "main": ["Lẩu thái", "Cơm chiên dương châu", "Bún chả", "Cháo lòng", "Hủ tiếu", "Bò kho bánh mì"],
            "side": ["Kem", "Bánh flan", "Chè khúc bạch", "Trái cây dầm"],
            "drink": ["Trà chanh", "Nước ép ổi", "Cacao nóng", "Nước lọc"],
        },
    }

    FLAVOR_LINES = [
        "Ăn lẹ đi rồi còn xách đít lên làm việc!",
        "Nuốt cho trôi, cấm chê dở nha!",
        "Ăn xong rửa chén, đừng có lười!",
        "Bày đặt chê ỏng chê eo tao nhét nguyên cái bát vào mồm giờ!",
        "Ngon thế này mà chê nữa thì mài cạo rỉ sắt ra mà ăn nhé con lợn!",
        "Cơm bưng nước rót tận miệng rồi, hốc nhanh đi khóc lóc cái gì?",
        "Dạo này cái nọng cằm mài sắp rớt xuống gối rồi đấy, táp vừa vừa thôi!",
        "Ế mốc meo ra thì lo mà ăn cho có sức chống chọi với cô đơn đi cưng!",
        "Thực đơn vip pro, không ăn thì nhịn đói ráng chịu nha cái đồ kén cá chọn canh!",
    ]
  
    OUTRO_LINES = [
        "Uống từ từ thôi kẻo sặc nước đéo ai rảnh gọi cấp cứu đâu!",
        "Tu nhanh lên rồi cút đi rửa bát, lười như hủi!",
        "Ăn xong cái mồm thối um cả server rồi, nhớ đi đánh răng giùm!",
        "Nhai cho kỹ vào kẻo nghẹn, tao không chịu trách nhiệm đâu!",
        "Ăn xong thì đứng lên đi lại cho tiêu cơm, ngồi trương thây ra đấy à?",
        "Táp ít thôi coi chừng mập!",
    ]

    @app_commands.command(name="hom-nay-an-gi", description="Nấu mâm cơm cho những đứa lười suy nghĩ 🍽️")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def hom_nay_an_gi(self, interaction: discord.Interaction):
        now_vn = datetime.now(VN_TZ)
        hour = now_vn.hour
        if hour < 10:
            buoi = "Buổi sáng"
        elif hour < 16:
            buoi = "Buổi trưa"
        else:
            buoi = "Buổi tối"

        menu = self.FOOD_MENU[buoi]
        main = random.choice(menu["main"])
        side = random.choice(menu["side"])
        drink = random.choice(menu["drink"])
        flavor = random.choice(self.FLAVOR_LINES)
        outro = random.choice(self.OUTRO_LINES)

        desc = (
            f"🍚 **Hốc cái này**: {main}\n"
            f"🍇 **Tráng miệng**: {side}\n"
            f"🥛 **Tu nốt**: {drink}\n\n"
            f"💬 {flavor}\n"
            f"💧 {outro}\n\n"
            f"-# Giờ VN: {now_vn.strftime('%H:%M')}"
        )
        embed = make_embed(desc, title=f"{HEART} Hôm nay nạp gì? ({buoi})", gif=True, guild=interaction.guild)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))