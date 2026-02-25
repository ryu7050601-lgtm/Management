import discord
from discord.ext import commands
import os
from flask import Flask
import threading

# --- [웹 서버 설정] Render/Uptime용 ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is online!"

def run():
    # Render는 'PORT' 환경 변수를 자동으로 부여합니다. 없으면 8080을 사용합니다.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True # 메인 프로세스 종료 시 함께 종료되도록 설정
    t.start()

# --- [디스코드 봇 설정] ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- [구매 기능] 1. 주문 정보 입력창 (Modal) ---
class OrderModal(discord.ui.Modal, title='상품 구매 정보 입력'):
    item_name = discord.ui.TextInput(
        label='구매 상품',
        placeholder='구매하실 상품 이름을 입력하세요.',
        required=True
    )
    quantity = discord.ui.TextInput(
        label='구매 수량',
        placeholder='숫자만 입력해주세요.',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"🛒-{user.name}-구매", overwrites=overwrites)

        msg_content = f"{user.mention}님, 주문이 접수되었습니다!\n토스뱅크 1908-9209-6452"
        embed = discord.Embed(title="📦 새로운 주문 상세", color=0x2f3136)
        embed.add_field(name="상품명", value=self.item_name.value, inline=False)
        embed.add_field(name="수량", value=self.quantity.value, inline=False)

        await channel.send(content=msg_content, embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"{channel.mention} 채널이 생성되었습니다.", ephemeral=True)

# --- [구매 기능] 2. 구매하기 버튼 뷰 ---
class PurchaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="구매하기", style=discord.ButtonStyle.success, emoji="💳", custom_id="btn_purchase_start")
    async def purchase_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OrderModal())

# --- [구매 기능] 3. 채널 닫기 버튼 뷰 ---
class CloseTicketView
