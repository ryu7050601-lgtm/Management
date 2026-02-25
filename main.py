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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# --- [디스코드 봇 설정] ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------------------------------------------
# [공용 기능] 채널 닫기 버튼 뷰
# ---------------------------------------------------------
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="닫기", style=discord.ButtonStyle.red, emoji="🔒", custom_id="btn_close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("채널을 삭제합니다...", ephemeral=True)
        await interaction.channel.delete()

# ---------------------------------------------------------
# [문의 기능] 모달 및 뷰
# ---------------------------------------------------------
class InquiryModal(discord.ui.Modal, title='📬 문의하기'):
    subject = discord.ui.TextInput(
        label='문의 사항',
        placeholder='문의하실 주제를 입력해주세요.',
        style=discord.TextStyle.short,
        required=True
    )
    content = discord.ui.TextInput(
        label='문의 내용',
        placeholder='문의하실 내용을 상세히 적어주세요.',
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        # 채널 생성 권한 설정
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"{user.name}-문의", overwrites=overwrites)

        embed = discord.Embed(title="📬 새로운 문의 내용", color=0x3CA45C)
        embed.add_field(name="문의 사항", value=self.subject.value, inline=False)
        embed.add_field(name="문의 내용", value=self.content.value, inline=False)
        embed.set_footer(text=f"작성자: {user.name} ({user.id})")

        await channel.send(content=f"{user.mention}님, 문의가 접수되었습니다.", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"{channel.mention} 채널이 생성되었습니다.", ephemeral=True)

class InquiryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="문의하기", style=discord.ButtonStyle.success, emoji="📨", custom_id="btn_inquiry_start")
    async def inquiry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InquiryModal())

# ---------------------------------------------------------
# [구매 기능] 모달 및 뷰
# ---------------------------------------------------------
class OrderModal(discord.ui.Modal, title='상품 구매 정보 입력'):
    item_name = discord.ui.TextInput(label='구매 상품', placeholder='구매하실 상품 이름을 입력하세요.', required=True)
    quantity = discord.ui.TextInput(label='구매 수량', placeholder='숫자만 입력해주세요.', required=True)

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

        channel = await guild.create_text_channel(name=f"{user.name}-구매", overwrites=overwrites)
        msg_content = f"{user.mention}님, 주문이 접수되었습니다!\n토스뱅크 1908-9209-6452
        <@&1475315894464024606>"
        embed = discord.Embed(title="📦 새로운 주문 상세", color=0x2f3136)
        embed.add_field(name="상품명", value=self.item_name.value, inline=False)
        embed.add_field(name="수량", value=self.quantity.value, inline=False)

        await channel.send(content=msg_content, embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"{channel.mention} 채널이 생성되었습니다.", ephemeral=True)

class PurchaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="구매하기", style=discord.ButtonStyle.success, emoji="💳", custom_id="btn_purchase_start")
    async def purchase_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OrderModal())

# ---------------------------------------------------------
# [후기 기능] 모달 및 뷰
# ---------------------------------------------------------
class ReviewModal(discord.ui.Modal, title='후기 작성하기'):
    satisfaction = discord.ui.TextInput(label='만족도 (1~5)', placeholder='5', min_length=1, max_length=1)
    content = discord.ui.TextInput(label='구매 후기', style=discord.TextStyle.paragraph, placeholder='내용을 입력하세요.', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            score = int(self.satisfaction.value)
            stars = "⭐" * min(max(score, 1), 5)
        except:
            stars = "⭐"
            score = self.satisfaction.value

        embed = discord.Embed(
            description=f"**새 리뷰 도착 ✨**\n\n**작성자**\n{interaction.user.mention}\n\n**만족도**\n{stars} ({score}/5)\n\n**구매 후기**\n{self.content.value}",
            color=0x2f3136
        )
        embed.set_footer(text=f"작성자: {interaction.user.name} ({interaction.user.id})")
        await interaction.response.send_message(f"{interaction.user.mention}님, 소중한 후기 감사합니다!", embed=embed)

class ReviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='후기 작성하기', style=discord.ButtonStyle.green, emoji='📩', custom_id="btn_review_write")
    async def write_review(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReviewModal())

# ---------------------------------------------------------
# 이벤트 및 명령어 (클래스 정의보다 아래에 위치)
# ---------------------------------------------------------
@bot.event
async def on_ready():
    # 영구적인 버튼 등록
    bot.add_view(PurchaseView())
    bot.add_view(CloseTicketView())
    bot.add_view(ReviewView())
    bot.add_view(InquiryView())
    print(f'봇 온라인: {bot.user.name}')

@bot.command(name="구매생성")
async def create_purchase(ctx):
    try:
        embed = discord.Embed(title="🛒 구매상품", description="구매하시려면 아래 버튼을 눌러주세요.", color=0x3CA45C)
        await ctx.send(embed=embed, view=PurchaseView())
    except Exception as e:
        await ctx.send(f"오류 발생: {e}")

@bot.command(name="문의생성")
async def create_inquiry(ctx):
    try:
        embed = discord.Embed(title="📬 문의사항", description="문의하시려면 아래 버튼을 클릭해주세요.", color=0x3CA45C)
        await ctx.send(embed=embed, view=InquiryView())
    except Exception as e:
        # 명령어가 반응이 없을 경우를 대비해 채팅창에 에러 출력
        await ctx.send(f"오류 발생: {e}")

@bot.command(name="후기생성")
async def create_review(ctx):
    try:
        await ctx.send("아래 버튼을 눌러 후기를 남겨주세요!", view=ReviewView())
    except Exception as e:
        await ctx.send(f"오류 발생: {e}")

# --- [실행] ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get('TOKEN')
    if token:
        bot.run(token)
    else:
        print("에러: TOKEN 환경 변수가 설정되지 않았습니다.")