import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
import asyncio
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger("role_setup_cog")

# ==============================================================================
# ── CẤU HÌNH — SỬA Ở ĐÂY CHO TIỆN ─────────────────────────────────────────────
# ==============================================================================

# Các role được phép bấm nút tuỳ chỉnh (thêm/bớt ID thoải mái trong set này)
ALLOWED_ROLE_IDS = {
    1535283110739058728,
    1538778266406756402,
    1544305306580815922,
    1535278578613362714,
    1537789183219994706,
}

ROLE_SETUP_CHANNEL_ID = 1548639068399599636

# File lưu ánh xạ: guild_id -> user_id -> role_id (role riêng của từng người)
CUSTOM_ROLE_DB_FILE = "custom_roles.json"

# File lưu channel_id/message_id của embed cố định, để bot biết đã đăng
# chưa (tránh đăng trùng mỗi lần restart) và để tìm lại mà gắn View mới.
PANEL_STATE_FILE = "role_setup_panel.json"

# Thời gian (giây) chờ người dùng gửi ảnh/emoji khi bấm "Đổi icon"
ICON_WAIT_TIMEOUT = 60

# Gif/ảnh hiện BÊN DƯỚI embed cố định trong kênh setup (để trống "" nếu
# không muốn hiện gì). Dán link ảnh/gif trực tiếp (đuôi .gif/.png/.jpg).
PANEL_GIF_URL = "https://giffiles.alphacoders.com/349/34972.gif"

# ── Trang trí embed cho đồng bộ với phần còn lại của bot ─────────────────────
HEART = "<a:klg23:1535400172199350332>"
EMBED_COLOR = 0xFFB6C1
ERROR_COLOR = 0xFF6961
FOOTER_TEXT = "Yui Hirasawa • Câu lạc bộ Nhạc Nhẹ"

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")

# Một số bản discord.py/py-cord mới có class discord.RoleColours giúp set
# màu Gradient tiện lợi. Bản cũ hơn (như bản Yui đang chạy) thì KHÔNG có
# class này -> ta tự gọi thẳng REST API của Discord (PATCH role, field
# "colors") để không phụ thuộc vào việc thư viện có hỗ trợ hay chưa.
SUPPORTS_GRADIENT_COLOR = hasattr(discord, "RoleColours")

DISCORD_API_BASE = "https://discord.com/api/v10"


async def set_role_gradient_raw(
    bot: commands.Bot,
    guild_id: int,
    role_id: int,
    primary_color: int,
    secondary_color: int,
    tertiary_color: Optional[int] = None,
    reason: Optional[str] = None,
) -> None:
    """Gọi thẳng REST API của Discord để set màu Gradient cho role, không
    phụ thuộc vào việc thư viện discord.py/py-cord đang dùng có hỗ trợ
    sẵn hay chưa (Discord API đã hỗ trợ field "colors" từ lâu, chỉ là
    một số bản thư viện Python chưa cập nhật theo kịp).
    Ném discord.HTTPException nếu Discord từ chối request (VD server chưa
    đủ Boost Level cho gradient)."""
    headers = {
        "Authorization": f"Bot {bot.http.token}",
        "Content-Type": "application/json",
    }
    if reason:
        # Header audit-log reason cần được encode đúng chuẩn (Discord yêu
        # cầu URL-encode nếu có ký tự đặc biệt/dấu tiếng Việt).
        from urllib.parse import quote
        headers["X-Audit-Log-Reason"] = quote(reason)

    payload = {
        "colors": {
            "primary_color": primary_color,
            "secondary_color": secondary_color,
            "tertiary_color": tertiary_color,
        }
    }
    url = f"{DISCORD_API_BASE}/guilds/{guild_id}/roles/{role_id}"

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, json=payload, headers=headers) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                if resp.status == 403:
                    raise discord.Forbidden(resp, text)
                raise discord.HTTPException(resp, text)


def make_embed(
    description: str,
    *,
    title: Optional[str] = None,
    color: int = EMBED_COLOR,
    guild: Optional[discord.Guild] = None,
) -> discord.Embed:
    embed = discord.Embed(description=description, color=color)
    if title:
        embed.title = title
    embed.set_footer(text=f"Yui Hirasawa • {guild.name}" if guild else FOOTER_TEXT)
    return embed


def has_allowed_role(member: discord.Member) -> bool:
    return any(r.id in ALLOWED_ROLE_IDS for r in getattr(member, "roles", []))


async def report_ui_error(interaction: discord.Interaction, error: Exception, *, where: str):
    """Log lỗi đầy đủ ra console VÀ cố gắng báo cho người dùng biết, thay vì
    để Discord tự hiện "Ứng dụng đã không phản hồi kịp thời" một cách im lặng.
    Dùng chung cho on_error của mọi View/Modal trong file này."""
    logger.exception("Lỗi không mong muốn trong %s", where, exc_info=error)
    embed = make_embed(
        f"Yui gặp lỗi bất ngờ khi xử lý yêu cầu này, thử lại giúp Yui nha!\n"
        f"(Nếu lặp lại nhiều lần, báo cho admin kèm log console)",
        title=f"{HEART} Có lỗi xảy ra", color=ERROR_COLOR, guild=interaction.guild,
    )
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.HTTPException:
        pass  # interaction đã hết hạn hoặc đã có phản hồi khác, đành chịu


# ==============================================================================
# ── LƯU TRỮ ROLE RIÊNG CỦA TỪNG NGƯỜI ─────────────────────────────────────────
# ==============================================================================

class RoleStore:
    """Lưu role riêng (custom role) của từng user theo từng server vào JSON."""

    def __init__(self, path: str = CUSTOM_ROLE_DB_FILE):
        self.path = path
        self.data: dict[str, dict[str, int]] = {}
        self._lock = asyncio.Lock()
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    async def save(self):
        async with self._lock:
            def _write():
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=4)
            await asyncio.to_thread(_write)

    def get_role_id(self, guild_id: int, user_id: int) -> Optional[int]:
        return self.data.get(str(guild_id), {}).get(str(user_id))

    async def set_role_id(self, guild_id: int, user_id: int, role_id: int):
        self.data.setdefault(str(guild_id), {})[str(user_id)] = role_id
        await self.save()

    async def remove(self, guild_id: int, user_id: int):
        bucket = self.data.get(str(guild_id))
        if bucket and str(user_id) in bucket:
            del bucket[str(user_id)]
            await self.save()


# ==============================================================================
# ── LƯU TRỮ TRẠNG THÁI EMBED CỐ ĐỊNH (channel_id / message_id) ───────────────
# ==============================================================================

class PanelStore:
    """Nhớ embed cố định đã đăng ở đâu, để không đăng trùng mỗi lần bot khởi động lại."""

    def __init__(self, path: str = PANEL_STATE_FILE):
        self.path = path
        self.data: dict = {}
        self._lock = asyncio.Lock()
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def get(self) -> Optional[dict]:
        return self.data or None

    async def set(self, channel_id: int, message_id: int):
        self.data = {"channel_id": channel_id, "message_id": message_id}
        async with self._lock:
            def _write():
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=4)
            await asyncio.to_thread(_write)


# ==============================================================================
# ── MODAL: ĐỔI TÊN ─────────────────────────────────────────────────────────
# ==============================================================================

class RoleNameModal(discord.ui.Modal, title="Đổi tên role"):
    def __init__(self, role: discord.Role):
        super().__init__()
        self.role = role
        self.name_input = discord.ui.TextInput(
            label="Tên role mới",
            default=role.name,
            max_length=100,
            required=True,
        )
        self.add_item(self.name_input)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await report_ui_error(interaction, error, where="RoleNameModal")

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.name_input.value.strip()
        if not new_name:
            return await interaction.response.send_message(
                embed=make_embed("Tên role không được để trống nha!", title=f"{HEART} Sai định dạng",
                                  color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )
        try:
            await self.role.edit(name=new_name, reason=f"Đổi tên role riêng bởi {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=make_embed(
                    "Yui hổng đủ quyền để sửa role này (kiểm tra vị trí role của Yui trong server nha)!",
                    title=f"{HEART} Thất bại", color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=make_embed(f"Có lỗi xảy ra: {e}", title=f"{HEART} Thất bại",
                                  color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )
        await interaction.response.send_message(
            embed=make_embed(f"Đã đổi tên role thành **{new_name}** rồi nè :3",
                              title=f"{HEART} Thành công", guild=interaction.guild),
            ephemeral=True,
        )


# ==============================================================================
# ── MODAL: ĐỔI MÀU ─────────────────────────────────────────────────────────
# ==============================================================================

class RoleColorModal(discord.ui.Modal, title="Đổi màu role"):
    def __init__(self, role: discord.Role):
        super().__init__()
        self.role = role
        self.color_input = discord.ui.TextInput(
            label="Mã màu HEX (VD: ff66aa hoặc #ff66aa)",
            placeholder="ff66aa",
            max_length=7,
            required=True,
        )
        self.add_item(self.color_input)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await report_ui_error(interaction, error, where="RoleColorModal")

    async def on_submit(self, interaction: discord.Interaction):
        match = HEX_RE.match(self.color_input.value.strip())
        if not match:
            return await interaction.response.send_message(
                embed=make_embed("Mã màu không hợp lệ nha! Nhập dạng HEX như `ff66aa` hoặc `#ff66aa` nè.",
                                  title=f"{HEART} Sai định dạng", color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )
        color_value = int(match.group(1), 16)
        try:
            await self.role.edit(colour=discord.Colour(color_value),
                                  reason=f"Đổi màu role riêng bởi {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=make_embed("Yui hổng đủ quyền để sửa role này!", title=f"{HEART} Thất bại",
                                  color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=make_embed(f"Có lỗi xảy ra: {e}", title=f"{HEART} Thất bại",
                                  color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )
        await interaction.response.send_message(
            embed=make_embed(f"Đã đổi màu role thành `#{match.group(1)}` rồi nè :3",
                              title=f"{HEART} Thành công", color=color_value, guild=interaction.guild),
            ephemeral=True,
        )


# ==============================================================================
# ── MODAL: ĐỔI MÀU GRADIENT (2 MÀU) ──────────────────────────────────────────
# ==============================================================================

class RoleGradientColorModal(discord.ui.Modal, title="Đổi màu Gradient (2 màu)"):
    def __init__(self, role: discord.Role, bot: commands.Bot):
        super().__init__()
        self.role = role
        self.bot = bot
        self.color1_input = discord.ui.TextInput(
            label="Mã màu 1 (HEX, VD: ff66aa)",
            placeholder="ff66aa",
            max_length=7,
            required=True,
        )
        self.color2_input = discord.ui.TextInput(
            label="Mã màu 2 (HEX, VD: 66aaff)",
            placeholder="66aaff",
            max_length=7,
            required=True,
        )
        self.add_item(self.color1_input)
        self.add_item(self.color2_input)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await report_ui_error(interaction, error, where="RoleGradientColorModal")

    async def on_submit(self, interaction: discord.Interaction):
        match1 = HEX_RE.match(self.color1_input.value.strip())
        match2 = HEX_RE.match(self.color2_input.value.strip())
        if not match1 or not match2:
            return await interaction.response.send_message(
                embed=make_embed("Mã màu không hợp lệ nha! Nhập cả 2 mã dạng HEX như `ff66aa` nè.",
                                  title=f"{HEART} Sai định dạng", color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )

        color1_value = int(match1.group(1), 16)
        color2_value = int(match2.group(1), 16)
        reason = f"Đổi màu gradient role riêng bởi {interaction.user}"

        try:
            if SUPPORTS_GRADIENT_COLOR:
                # Thư viện có hỗ trợ sẵn -> dùng API chính thức của thư viện.
                colours = discord.RoleColours(
                    primary=discord.Colour(color1_value),
                    secondary=discord.Colour(color2_value),
                )
                await self.role.edit(colours=colours, reason=reason)
            else:
                # Thư viện chưa cập nhật -> gọi thẳng REST API của Discord,
                # không phụ thuộc vào việc thư viện có hỗ trợ hay chưa.
                await set_role_gradient_raw(
                    self.bot, self.role.guild.id, self.role.id,
                    primary_color=color1_value, secondary_color=color2_value,
                    reason=reason,
                )
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=make_embed("Yui hổng đủ quyền để sửa role này!", title=f"{HEART} Thất bại",
                                  color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )
        except discord.HTTPException as e:
            # Server chưa đủ Boost Level cho tính năng Gradient thường trả lỗi ở đây
            return await interaction.response.send_message(
                embed=make_embed(
                    f"Có lỗi xảy ra: {e}\n\n{HEART} Lưu ý: màu Gradient cần server đạt "
                    f"Boost Level đủ điều kiện (tính năng `ENHANCED_ROLE_COLORS`).",
                    title=f"{HEART} Thất bại", color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )

        await interaction.response.send_message(
            embed=make_embed(
                f"Đã đổi màu role thành Gradient `#{match1.group(1)}` → `#{match2.group(1)}` rồi nè :3",
                title=f"{HEART} Thành công", color=color1_value, guild=interaction.guild),
            ephemeral=True,
        )


# ==============================================================================
# ── VIEW: CHỌN 1 MÀU HAY 2 MÀU (GRADIENT) TRƯỚC KHI MỞ MODAL ────────────────
# ==============================================================================

class ColorModeView(discord.ui.View):
    def __init__(self, role: discord.Role, owner_id: int, bot: commands.Bot):
        super().__init__(timeout=60)
        self.role = role
        self.owner_id = owner_id
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                embed=make_embed("Đây không phải bảng tuỳ chỉnh của bạn nha!",
                                  title=f"{HEART} Hổng được đâu", color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        await report_ui_error(interaction, error, where="ColorModeView")

    @discord.ui.button(label="1 Màu", style=discord.ButtonStyle.blurple, emoji="🎨")
    async def btn_solid(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RoleColorModal(self.role))

    @discord.ui.button(label="2 Màu (Gradient)", style=discord.ButtonStyle.blurple, emoji="🌈")
    async def btn_gradient(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RoleGradientColorModal(self.role, self.bot))


# ==============================================================================
# ── VIEW: XÁC NHẬN XOÁ ROLE ──────────────────────────────────────────────────
# ==============================================================================

class DeleteRoleConfirmView(discord.ui.View):
    def __init__(self, cog: "RoleSetupCog", role: discord.Role, owner_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.role = role
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                embed=make_embed("Đây không phải bảng tuỳ chỉnh của bạn nha!",
                                  title=f"{HEART} Hổng được đâu", color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        await report_ui_error(interaction, error, where="DeleteRoleConfirmView")

    @discord.ui.button(label="Xác nhận xoá", style=discord.ButtonStyle.red, emoji="🗑️")
    async def btn_confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await self.cog.handle_role_delete(interaction, self.role)

    @discord.ui.button(label="Huỷ", style=discord.ButtonStyle.grey, emoji="↩️")
    async def btn_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=make_embed("Đã huỷ, role của bạn vẫn còn nguyên nha!",
                              title=f"{HEART} Đã huỷ", guild=interaction.guild),
            view=self,
        )


# ==============================================================================
# ── VIEW: BẢNG TUỲ CHỈNH (4 NÚT: TÊN / MÀU / ICON / XOÁ) ─────────────────────
# Đây là bảng riêng, chỉ người bấm nút ở embed cố định mới thấy (ephemeral).
# ==============================================================================

class RoleSetupView(discord.ui.View):
    def __init__(self, cog: "RoleSetupCog", role: discord.Role, owner_id: int):
        super().__init__(timeout=180)
        self.cog = cog
        self.role = role
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Chỉ chủ nhân của bảng (người đã bấm nút mở bảng) mới được thao tác
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                embed=make_embed("Đây không phải bảng tuỳ chỉnh của bạn nha!",
                                  title=f"{HEART} Hổng được đâu", color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        await report_ui_error(interaction, error, where="RoleSetupView")

    @discord.ui.button(label="Đổi tên", style=discord.ButtonStyle.blurple, emoji="📝")
    async def btn_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RoleNameModal(self.role))

    @discord.ui.button(label="Đổi màu", style=discord.ButtonStyle.grey, emoji="🎨")
    async def btn_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=make_embed("Bạn muốn đổi role sang **1 màu** hay **2 màu (Gradient)**?",
                              title=f"{HEART} Chọn kiểu màu", guild=interaction.guild),
            view=ColorModeView(self.role, owner_id=self.owner_id, bot=self.cog.bot),
            ephemeral=True,
        )

    @discord.ui.button(label="Đổi icon", style=discord.ButtonStyle.green, emoji="🖼️")
    async def btn_icon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_icon_change(interaction, self.role)

    @discord.ui.button(label="Xoá role", style=discord.ButtonStyle.red, emoji="🗑️")
    async def btn_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=make_embed(
                f"Bạn có chắc muốn **xoá hẳn** role {self.role.mention} của mình không? "
                f"Hành động này không thể hoàn tác đâu nha!",
                title=f"{HEART} Xác nhận xoá role", color=ERROR_COLOR, guild=interaction.guild),
            view=DeleteRoleConfirmView(self.cog, self.role, owner_id=self.owner_id),
            ephemeral=True,
        )


# ==============================================================================
# ── VIEW CỐ ĐỊNH (PERSISTENT): gắn vào embed duy nhất trong kênh setup ───────
# Dùng custom_id cố định + timeout=None để nút vẫn hoạt động kể cả sau khi
# bot restart, không cần đăng lại embed.
# ==============================================================================

class RoleSetupEntryView(discord.ui.View):
    def __init__(self, cog: "RoleSetupCog"):
        super().__init__(timeout=None)
        self.cog = cog

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        await report_ui_error(interaction, error, where="RoleSetupEntryView")

    @discord.ui.button(
        label="Tuỳ chỉnh role của tôi",
        style=discord.ButtonStyle.blurple,
        emoji=HEART,
        custom_id="role_setup:open_panel",
    )
    async def btn_open(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.open_personal_panel(interaction)


# ==============================================================================
# ── COG CHÍNH ─────────────────────────────────────────────────────────────
# ==============================================================================

class RoleSetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.store = RoleStore()
        self.panel_store = PanelStore()
        self._panel_checked = False

    async def cog_load(self):
        # Đăng ký View cố định ngay khi cog được nạp, để nút bấm vẫn hoạt
        # động kể cả trước khi on_ready chạy xong (VD ngay sau khi bot restart).
        self.bot.add_view(RoleSetupEntryView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        # on_ready có thể được gọi lại nhiều lần khi reconnect, chỉ cần
        # kiểm tra/đăng embed 1 lần duy nhất cho mỗi lần bot khởi động.
        if self._panel_checked:
            return
        self._panel_checked = True
        await self.ensure_panel_message()

    # ── Đảm bảo embed cố định đã tồn tại trong kênh cấu hình, nếu chưa thì đăng ──
    async def ensure_panel_message(self):
        if not ROLE_SETUP_CHANNEL_ID:
            print("[role_setup_cog] Chưa cấu hình ROLE_SETUP_CHANNEL_ID, bỏ qua đăng bảng.")
            return

        channel = self.bot.get_channel(ROLE_SETUP_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(ROLE_SETUP_CHANNEL_ID)
            except discord.HTTPException:
                print(f"[role_setup_cog] Không tìm thấy kênh ID {ROLE_SETUP_CHANNEL_ID}.")
                return

        embed = make_embed(
            "Bấm nút bên dưới để mở bảng tuỳ chỉnh role riêng của bạn (tên, màu, icon) nha :3\n\n"
            f"{HEART} Chỉ dành cho ai *boost* hoặc *donate server* thôi nha!",
            title=f"{HEART} Tuỳ Chỉnh Role Riêng",
            guild=channel.guild,
        )
        if PANEL_GIF_URL:
            embed.set_image(url=PANEL_GIF_URL)

        stored = self.panel_store.get()
        if stored and stored.get("channel_id") == channel.id:
            try:
                old_msg = await channel.fetch_message(stored["message_id"])
                # Message vẫn còn -> chỉ cập nhật lại nội dung/gif cho khớp
                # cấu hình mới nhất, khỏi cần đăng embed mới.
                await old_msg.edit(embed=embed, view=RoleSetupEntryView(self))
                return
            except discord.HTTPException:
                pass  # message đã bị xoá hoặc lỗi -> đăng mới bên dưới

        try:
            msg = await channel.send(embed=embed, view=RoleSetupEntryView(self))
        except discord.HTTPException as e:
            print(f"[role_setup_cog] Đăng embed thất bại: {e}")
            return
        await self.panel_store.set(channel.id, msg.id)

    # ── Đẩy role lên vị trí cao nhất có thể (ngay dưới role cao nhất của Yui) ─
    # Làm vậy để MÀU và ICON của role riêng luôn được ưu tiên hiển thị hơn
    # các role khác mà thành viên đang có (Discord chỉ hiện màu/icon của role
    # có vị trí CAO NHẤT trong số các role của thành viên).
    async def _promote_role_position(self, guild: discord.Guild, role: discord.Role):
        me = guild.me
        desired_position = max(1, me.top_role.position - 1)
        if role.position == desired_position:
            return  # đã ở đúng vị trí ưu tiên rồi, khỏi gọi API cho tốn quota
        try:
            await role.edit(position=desired_position, reason="Ưu tiên hiển thị màu/icon role riêng")
        except discord.Forbidden:
            logger.warning(
                "Không đủ quyền đẩy vị trí role %s (id=%s) lên %s — top_role của bot là %s (pos=%s)",
                role.name, role.id, desired_position, me.top_role.name, me.top_role.position,
            )
        except discord.HTTPException as e:
            # Edit vị trí đơn lẻ qua PATCH /roles/{id} đôi khi bị Discord từ
            # chối âm thầm nếu vị trí đích đang trùng/xung đột với role khác.
            # Fallback: dùng bulk position edit (PATCH /roles, list đầy đủ),
            # cách này đáng tin cậy hơn vì Discord tự resolve toàn bộ thứ tự.
            logger.warning("role.edit(position=...) thất bại (%s), thử fallback bulk edit_role_positions", e)
            try:
                await guild.edit_role_positions(
                    positions={role: desired_position},
                    reason="Ưu tiên hiển thị màu/icon role riêng (fallback bulk)",
                )
            except discord.HTTPException as e2:
                logger.warning("Fallback bulk edit_role_positions cũng thất bại: %s", e2)

    # ── Lấy role riêng của user, tự tạo nếu chưa có ──────────────────────────
    async def get_or_create_role(self, interaction: discord.Interaction) -> Optional[discord.Role]:
        guild = interaction.guild
        member = interaction.user

        role_id = self.store.get_role_id(guild.id, member.id)
        role = guild.get_role(role_id) if role_id else None

        if role is not None and role not in member.roles:
            # Role cũ vẫn tồn tại nhưng người dùng không còn giữ (bị gỡ thủ công) -> gán lại
            try:
                await member.add_roles(role, reason="Gán lại role riêng qua bảng tuỳ chỉnh")
            except discord.Forbidden:
                role = None  # sẽ tạo role mới bên dưới nếu gán lại thất bại

        if role is None:
            me = guild.me
            if not me.guild_permissions.manage_roles:
                await interaction.followup.send(
                    embed=make_embed("Yui không có quyền `Manage Roles` để tạo role riêng cho bạn!",
                                      title=f"{HEART} Thiếu quyền", color=ERROR_COLOR, guild=guild),
                    ephemeral=True,
                )
                return None
            try:
                role = await guild.create_role(
                    name=member.display_name[:100],
                    hoist=True,
                    reason=f"Tạo role riêng cho {member} qua bảng tuỳ chỉnh",
                )
                await member.add_roles(role, reason="Gán role riêng vừa tạo")
            except discord.Forbidden:
                await interaction.followup.send(
                    embed=make_embed("Yui không đủ quyền để tạo/gán role mới!",
                                      title=f"{HEART} Thiếu quyền", color=ERROR_COLOR, guild=guild),
                    ephemeral=True,
                )
                return None
            except discord.HTTPException as e:
                await interaction.followup.send(
                    embed=make_embed(f"Có lỗi xảy ra khi tạo role: {e}",
                                      title=f"{HEART} Thất bại", color=ERROR_COLOR, guild=guild),
                    ephemeral=True,
                )
                return None

            await self.store.set_role_id(guild.id, member.id, role.id)

        # Luôn đẩy role lên vị trí ưu tiên cao nhất có thể, dù là role vừa tạo
        # hay role cũ đã có từ trước (phòng trường hợp có role khác chen lên trên).
        await self._promote_role_position(guild, role)

        return role

    # ── Xử lý đổi icon (ảnh ưu tiên, fallback emoji) ─────────────────────────
    async def handle_icon_change(self, interaction: discord.Interaction, role: discord.Role):
        guild = interaction.guild

        if "ROLE_ICONS" not in guild.features:
            return await interaction.response.send_message(
                embed=make_embed(
                    "Server chưa đủ điều kiện để dùng Icon Role (cần đạt Boost Level 2) nha!",
                    title=f"{HEART} Không khả dụng", color=ERROR_COLOR, guild=guild),
                ephemeral=True,
            )

        await interaction.response.send_message(
            embed=make_embed(
                f"Gửi **1 ảnh đính kèm** (ưu tiên) hoặc **1 emoji** ngay trong kênh này trong vòng "
                f"{ICON_WAIT_TIMEOUT} giây để làm icon cho role nha!\n\n"
                f"{HEART} Ảnh nên vuông để hiển thị đẹp nhất.",
                title=f"{HEART} Đổi Icon Role", guild=guild),
            ephemeral=True,
        )

        def check(m: discord.Message) -> bool:
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=ICON_WAIT_TIMEOUT)
        except asyncio.TimeoutError:
            return await interaction.followup.send(
                embed=make_embed("Hết giờ rồi, bấm lại nút Đổi Icon để thử lại nha!",
                                  title=f"{HEART} Hết thời gian", color=ERROR_COLOR, guild=guild),
                ephemeral=True,
            )

        icon_bytes: Optional[bytes] = None
        unicode_emoji: Optional[str] = None

        # Ưu tiên 1: ảnh đính kèm
        if msg.attachments:
            attachment = msg.attachments[0]
            if attachment.content_type and attachment.content_type.startswith("image/"):
                try:
                    icon_bytes = await attachment.read()
                except discord.HTTPException:
                    icon_bytes = None

        # Fallback: emoji (custom emoji của server hoặc emoji unicode thường)
        if icon_bytes is None:
            content = msg.content.strip()
            partial: Optional[discord.PartialEmoji] = None
            try:
                partial = discord.PartialEmoji.from_str(content)
            except Exception:
                partial = None

            if partial is not None and partial.is_custom_emoji():
                # QUAN TRỌNG: PartialEmoji.from_str() KHÔNG gắn kèm _state, nên
                # gọi thẳng partial.read() sẽ luôn lỗi (không có state để gọi
                # HTTP), lỗi đó bị nuốt bởi except bên dưới -> icon_bytes luôn
                # None dù emoji hợp lệ. Ta lấy emoji thật từ cache guild (đã có
                # state hợp lệ) trước, rồi mới fallback tải thủ công qua URL CDN.
                cached_emoji = guild.get_emoji(partial.id)
                if cached_emoji is not None:
                    try:
                        icon_bytes = await cached_emoji.read()
                    except Exception:
                        icon_bytes = None

                if icon_bytes is None:
                    # Fallback cuối: tự tải bytes từ URL CDN của emoji (không
                    # cần _state), phòng khi emoji không nằm trong cache guild
                    # (VD emoji từ server khác nhưng bot cũng ở server đó).
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(partial.url) as resp:
                                if resp.status == 200:
                                    icon_bytes = await resp.read()
                    except Exception:
                        icon_bytes = None
            elif content:
                unicode_emoji = content

        try:
            await msg.delete()
        except discord.HTTPException:
            pass

        if icon_bytes is None and unicode_emoji is None:
            return await interaction.followup.send(
                embed=make_embed("Yui không nhận ra ảnh hay emoji nào hết, bấm nút Đổi Icon để thử lại nha!",
                                  title=f"{HEART} Không hợp lệ", color=ERROR_COLOR, guild=guild),
                ephemeral=True,
            )

        try:
            # discord.py dùng chung tham số display_icon: truyền bytes ảnh
            # hoặc chuỗi emoji unicode đều được.
            new_icon = icon_bytes if icon_bytes is not None else unicode_emoji
            await role.edit(display_icon=new_icon, reason=f"Đổi icon role riêng bởi {interaction.user}")
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed("Yui hổng đủ quyền để sửa role này!", title=f"{HEART} Thất bại",
                                  color=ERROR_COLOR, guild=guild),
                ephemeral=True,
            )
        except discord.HTTPException as e:
            return await interaction.followup.send(
                embed=make_embed(f"Có lỗi xảy ra: {e}", title=f"{HEART} Thất bại",
                                  color=ERROR_COLOR, guild=guild),
                ephemeral=True,
            )

        await interaction.followup.send(
            embed=make_embed("Đã đổi icon role thành công rồi nè :3", title=f"{HEART} Thành công", guild=guild),
            ephemeral=True,
        )

    # ── Xử lý xoá hẳn role riêng của người dùng ──────────────────────────────
    async def handle_role_delete(self, interaction: discord.Interaction, role: discord.Role):
        guild = interaction.guild
        member = interaction.user

        try:
            await role.delete(reason=f"Xoá role riêng theo yêu cầu của {interaction.user}")
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed("Yui hổng đủ quyền để xoá role này!", title=f"{HEART} Thất bại",
                                  color=ERROR_COLOR, guild=guild),
                ephemeral=True,
            )
        except discord.HTTPException as e:
            return await interaction.followup.send(
                embed=make_embed(f"Có lỗi xảy ra: {e}", title=f"{HEART} Thất bại",
                                  color=ERROR_COLOR, guild=guild),
                ephemeral=True,
            )

        await self.store.remove(guild.id, member.id)

        await interaction.followup.send(
            embed=make_embed(
                "Đã xoá role riêng của bạn rồi nè. Bấm lại nút \"Tuỳ chỉnh role của tôi\" "
                "nếu muốn tạo role mới nha :3",
                title=f"{HEART} Đã xoá", guild=guild),
            ephemeral=True,
        )

    # ── Được gọi khi ai đó bấm nút "Tuỳ chỉnh role của tôi" trên embed cố định ──
    async def open_personal_panel(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message(
                embed=make_embed("Cái này chỉ dùng được trong server thôi nha!",
                                  title=f"{HEART} Hổng được đâu", color=ERROR_COLOR),
                ephemeral=True,
            )

        if not has_allowed_role(interaction.user):
            return await interaction.response.send_message(
                embed=make_embed("Bạn cần *boost* hoặc *donate server* mới bấm được nút này nha!",
                                  title=f"{HEART} Hổng có quyền", color=ERROR_COLOR, guild=interaction.guild),
                ephemeral=True,
            )

        # Tạo role (nếu cần) có thể tốn hơn 3s -> defer trước
        await interaction.response.defer(ephemeral=True, thinking=True)

        role = await self.get_or_create_role(interaction)
        if role is None:
            return  # thông báo lỗi đã được gửi trong get_or_create_role

        view = RoleSetupView(self, role, owner_id=interaction.user.id)
        await interaction.followup.send(
            embed=make_embed(
                f"Đây là bảng tuỳ chỉnh cho role {role.mention} của bạn, bấm nút bên dưới để chỉnh sửa nha :3",
                title=f"{HEART} Bảng Tuỳ Chỉnh Role Riêng", guild=interaction.guild),
            view=view,
            ephemeral=True,
        )

    # ── Lệnh admin để đăng/đăng lại embed cố định thủ công, phòng khi cần dời
    # kênh hoặc embed bị xoá mà không muốn restart cả bot. KHÔNG dành cho
    # người dùng thường (đã giới hạn quyền Manage Server).
    @app_commands.command(name="role-setup-panel", description="[Admin] Đăng/refresh embed tuỳ chỉnh role cố định")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def role_setup_panel_refresh(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.ensure_panel_message()
        await interaction.followup.send(
            embed=make_embed("Đã kiểm tra/đăng lại embed tuỳ chỉnh role rồi nha :3",
                              title=f"{HEART} Xong", guild=interaction.guild),
            ephemeral=True,
        )

    # ── Lệnh admin để hoist lại hàng loạt các role riêng đã tạo TRƯỚC KHI
    # code có hoist=True (role cũ sẽ không tự động hoist, phải chạy tay 1
    # lần). Cũng tiện dùng lại nếu ai đó lỡ tay bỏ hoist của role riêng.
    @app_commands.command(name="role-hoist-fix", description="[Admin] Bật hoist cho toàn bộ role riêng đã tạo trong server")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def role_hoist_fix(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild

        role_ids = list(self.store.data.get(str(guild.id), {}).values())
        if not role_ids:
            return await interaction.followup.send(
                embed=make_embed("Server này chưa có role riêng nào được lưu trong dữ liệu của Yui hết nha!",
                                  title=f"{HEART} Không có gì để sửa", guild=guild),
                ephemeral=True,
            )

        fixed, already_ok, not_found, failed = 0, 0, 0, 0
        for role_id in role_ids:
            role = guild.get_role(role_id)
            if role is None:
                not_found += 1
                continue
            if role.hoist:
                already_ok += 1
                continue
            try:
                await role.edit(hoist=True, reason=f"Bật hoist hàng loạt bởi {interaction.user}")
                fixed += 1
            except discord.HTTPException as e:
                logger.warning("Không hoist được role %s (id=%s): %s", role.name, role.id, e)
                failed += 1

        desc = (
            f"**Đã bật hoist**: {fixed}\n"
            f"**Đã hoist sẵn từ trước**: {already_ok}\n"
            f"**Role không còn tồn tại**: {not_found}\n"
            f"**Lỗi (không đủ quyền/vị trí)**: {failed}"
        )
        await interaction.followup.send(
            embed=make_embed(desc, title=f"{HEART} Đã xử lý xong", guild=guild),
            ephemeral=True,
        )

    # ── Lệnh admin xoá role riêng của MỘT thành viên bất kỳ (VD họ rời
    # server nhưng role rác còn sót lại, hoặc bị report/vi phạm nên cần
    # thu hồi role riêng). Khác với handle_role_delete (chỉ chủ role tự
    # xoá được), lệnh này admin xoá thay cho ai cũng được.
    @app_commands.command(name="role-delete", description="[Admin] Xoá role riêng của một thành viên")
    @app_commands.describe(member="Thành viên cần xoá role riêng (dùng ID nếu họ đã rời server)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def role_delete_admin(self, interaction: discord.Interaction, member: discord.User):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild

        role_id = self.store.get_role_id(guild.id, member.id)
        if role_id is None:
            return await interaction.followup.send(
                embed=make_embed(f"{member.mention} không có role riêng nào được lưu trong dữ liệu của Yui hết nha!",
                                  title=f"{HEART} Không tìm thấy", color=ERROR_COLOR, guild=guild),
                ephemeral=True,
            )

        role = guild.get_role(role_id)
        if role is not None:
            try:
                await role.delete(reason=f"Admin {interaction.user} xoá role riêng của {member}")
            except discord.Forbidden:
                return await interaction.followup.send(
                    embed=make_embed("Yui hổng đủ quyền để xoá role này (kiểm tra vị trí role của Yui nha)!",
                                      title=f"{HEART} Thất bại", color=ERROR_COLOR, guild=guild),
                    ephemeral=True,
                )
            except discord.HTTPException as e:
                return await interaction.followup.send(
                    embed=make_embed(f"Có lỗi xảy ra: {e}", title=f"{HEART} Thất bại",
                                      color=ERROR_COLOR, guild=guild),
                    ephemeral=True,
                )

        await self.store.remove(guild.id, member.id)

        note = "" if role is not None else "\n\n-# (Role đã không còn tồn tại trong server, chỉ dọn lại dữ liệu thôi)"
        await interaction.followup.send(
            embed=make_embed(f"Đã xoá role riêng của {member.mention} rồi nha!{note}",
                              title=f"{HEART} Đã xoá", guild=guild),
            ephemeral=True,
        )

    # ── Lệnh admin liệt kê toàn bộ role riêng đang được bot quản lý trong
    # server, kèm chủ sở hữu, để tiện đối soát/dọn dẹp thủ công.
    @app_commands.command(name="role-list", description="[Admin] Liệt kê toàn bộ role riêng trong server")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def role_list_admin(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild

        bucket = self.store.data.get(str(guild.id), {})
        if not bucket:
            return await interaction.followup.send(
                embed=make_embed("Server này chưa có role riêng nào được lưu trong dữ liệu của Yui hết nha!",
                                  title=f"{HEART} Trống trơn", guild=guild),
                ephemeral=True,
            )

        lines: list[str] = []
        for user_id_str, role_id in bucket.items():
            member = guild.get_member(int(user_id_str))
            owner_text = member.mention if member is not None else f"<@{user_id_str}> *(đã rời server)*"
            role = guild.get_role(role_id)
            role_text = role.mention if role is not None else "*(role đã bị xoá)*"
            lines.append(f"{owner_text} — {role_text}")

        desc = "\n".join(lines)
        truncated_note = ""
        if len(desc) > 3900:
            # Embed description giới hạn 4096 ký tự, cắt bớt cho an toàn và
            # báo rõ để admin biết còn sót, tránh tưởng nhầm là danh sách đủ.
            shown = 0
            acc = ""
            for line in lines:
                if len(acc) + len(line) + 1 > 3900:
                    break
                acc += line + "\n"
                shown += 1
            desc = acc
            truncated_note = f"\n\n-# Danh sách dài quá, chỉ hiện {shown}/{len(lines)} role đầu tiên thôi nha!"

        embed = make_embed(desc + truncated_note,
                            title=f"{HEART} Danh Sách Role Riêng ({len(lines)} role)", guild=guild)
        await interaction.followup.send(embed=embed, ephemeral=True)
