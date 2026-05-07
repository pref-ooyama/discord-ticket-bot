import os
import discord
import gspread
import json
from discord.ext import commands
from flask import Flask
from threading import Thread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. Flaskの設定 ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. スプレッドシート設定 ---
try:
    creds_dict = json.loads(os.environ["GOOGLE_SHEETS_JSON"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("勤務記録シート").sheet1 
except Exception as e:
    print(f"スプレッドシート連携エラー: {e}")

# --- 3. Discordボットの設定 ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True 
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# --- 4. VC自動切断ロジック ---
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id: return
    vc = discord.utils.get(bot.voice_clients, guild=member.guild)
    if vc and before.channel and before.channel.id == vc.channel.id:
        if len([m for m in vc.channel.members if not m.bot]) == 0:
            await vc.disconnect()

# --- 5. コマンド実装 ---

@bot.command()
async def help(ctx):
    msg = """
📜 **チケット・VC Bot コマンド一覧**
`!ticket` : チケット作成パネルを表示
`!vc` : あなたがいるVCに接続（無人になると自動切断）
`!dc` : VCから手動切断
`!total [名前]` : 勤務記録を確認（重複修正済）
    """
    await ctx.send(msg)

@bot.command()
async def vc(ctx):
    if ctx.author.voice and ctx.author.voice.channel:
        try:
            await ctx.author.voice.channel.connect()
            await ctx.send(f"✅ **{ctx.author.voice.channel.name}** に接続しました。")
        except Exception as e:
            await ctx.send(f"❌ エラー: {e}\n※サーバー側で `pip install PyNaCl` が必要です。")
    else:
        await ctx.send(f"❌ {ctx.author.name}さんがVCにいません。")

@bot.command()
async def dc(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 切断しました。")

@bot.command()
async def total(ctx, name: str = None):
    target = name if name else ctx.author.display_name
    try:
        data = sheet.get_all_values()
        records = [r for r in data if len(r) >= 1 and r[0] == target]
        if not records: return await ctx.send(f"❌ {target} さんの記録なし")
        
        msg = f"📊 **{target} さんの記録**\n"
        seen_depts = set() # 重複表示を防ぐ
        for r in records:
            d_name = r[4] if len(r) >= 5 and r[4] else "個人・未指定"
            if d_name in seen_depts: continue
            seen_depts.add(d_name)
            msg += f"・{d_name}: 今月 {r[1]}分 / 累計 {r[2]}分\n"
        await ctx.send(msg)
    except Exception as e: await ctx.send(f"❌ エラー: {e}")

@bot.command()
async def ticket(ctx):
    view = discord.ui.View()
    button = discord.ui.Button(label="チケット作成", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    view.add_item(button)
    await ctx.send("以下のボタンを押してチケットを作成してください。", view=view)

# --- 6. インタラクション（チケット作成） ---
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data.get("custom_id") == "create_ticket":
        try:
            guild = interaction.guild
            user = interaction.user
            kanbu_role = discord.utils.get(guild.roles, name="幹部自衛官")
            kansatu_role = discord.utils.get(guild.roles, name="監察課【ID】--Inspector Division")
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            if kanbu_role: overwrites[kanbu_role] = discord.PermissionOverwrite(read_messages=True)
            if kansatu_role: overwrites[kansatu_role] = discord.PermissionOverwrite(read_messages=True)
            
            new_channel = await guild.create_text_channel(f"ticket-{user.name.lower()}", overwrites=overwrites)
            await interaction.response.send_message(f"チケットを作成しました: {new_channel.mention}", ephemeral=True)
        except Exception as e:
            if not interaction.response.is_done(): await interaction.response.send_message(f"エラー: {e}", ephemeral=True)

# --- 7. 起動 ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.environ["TOKEN"])
