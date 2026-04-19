import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# 1. Flaskの設定（Renderのポート対策）
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    # Renderが指定するポートを優先、なければ10000を使用
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Discordボットの設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# 3. ボタンが押された時の処理
@bot.event
async def on_interaction(interaction: discord.Interaction):
    # ボタンの custom_id が "create_ticket" の場合のみ処理
    if interaction.data.get("custom_id") == "create_ticket":
        guild = interaction.guild
        channel_name = f"ticket-{interaction.user.name}"
        
        # チャンネル作成（権限設定などは必要に応じて追加可能）
        new_channel = await guild.create_text_channel(channel_name)
        
        # 作成者への返信（Ephemeral＝本人にしか見えないメッセージ）
        await interaction.response.send_message(f"チケットを作成しました: {new_channel.mention}", ephemeral=True)

# 4. !ticket コマンド（特定のロールのみ実行可能）
@bot.command()
@commands.has_any_role("監察課【ID】--Inspector Division", "幹部自衛官")
async def ticket(ctx):
    view = discord.ui.View()
    button = discord.ui.Button(label="チケット作成", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    view.add_item(button)
    await ctx.send("以下のボタンを押してチケットを作成してください。", view=view)

@ticket.error
async def ticket_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("このコマンドを実行する権限がありません。（必要なロール：監察課【ID】--Inspector Division or 幹部自衛官）", ephemeral=True)

# 5. 起動処理
if __name__ == "__main__":
    # Webサーバーを別スレッドで起動
    Thread(target=run_web).start()
    # Discordボットを起動
    bot.run(os.environ["TOKEN"])
