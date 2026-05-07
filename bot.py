import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- 1. Flaskの設定 (Render/Replit維持用) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    # ポート番号は環境変数から取得（デフォルト10000）
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. Discordボットの設定 ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # VC接続に必要
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# --- 3. !help コマンド ---
@bot.command()
async def help(ctx):
    help_msg = """
📜 **Bot コマンド一覧**

`!ticket` : チケット作成用のボタンパネルを表示します。
`!vc` : あなたが現在参加しているボイスチャンネルにBotを接続させます。
`!dc` : ボイスチャンネルからBotを退出させます。
    """
    await ctx.send(help_msg)

# --- 4. !vc コマンド ---
@bot.command()
async def vc(ctx):
    # 実行者がVCに入っているかチェック
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel
        try:
            await channel.connect()
            await ctx.send(f"✅ **{channel.name}** に接続しました！")
        except Exception as e:
            await ctx.send(f"❌ 接続中にエラーが発生しました: {e}")
    else:
        # VCに入っていない場合
        await ctx.send(f"❌ **{ctx.author.name}** さんがVCにいません。")

# 切断コマンドも念のため追加
@bot.command()
async def dc(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 切断しました。")
    else:
        await ctx.send("❌ BotはVCに参加していません。")

# --- 5. チケットパネル表示コマンド ---
@bot.command()
async def ticket(ctx):
    if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
        return

    view = discord.ui.View()
    button = discord.ui.Button(
        label="チケット作成", 
        style=discord.ButtonStyle.primary, 
        custom_id="create_ticket"
    )
    view.add_item(button)
    await ctx.send("以下のボタンを押してチケットを作成してください。", view=view)

# --- 6. ボタン処理（チケット作成） ---
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data.get("custom_id") == "create_ticket":
        try:
            guild = interaction.guild
            user = interaction.user
            
            # ロール名で検索
            kanbu_role = discord.utils.get(guild.roles, name="幹部自衛官")
            kansatu_role = discord.utils.get(guild.roles, name="監察課【ID】--Inspector Division")
            
            # 権限設定（本人のみ、および指定ロールのみ閲覧可能）
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            
            if kanbu_role:
                overwrites[kanbu_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            if kansatu_role:
                overwrites[kansatu_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            # チャンネル名の重複回避
            count = 1
            base_name = f"ticket-{user.name.lower()}"
            channel_name = base_name
            while any(c.name == channel_name for c in guild.text_channels):
                count += 1
                channel_name = f"{base_name}{count:02d}"
            
            # チャンネル作成
            new_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
            await interaction.response.send_message(f"チケットを作成しました: {new_channel.mention}", ephemeral=True)
            
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"エラー発生: {e}", ephemeral=True)

# --- 7. 起動 ---
if __name__ == "__main__":
    # Webサーバー（Flask）を別スレッドで開始
    Thread(target=run_web).start()
    # Botを起動
    bot.run(os.environ["TOKEN"])
