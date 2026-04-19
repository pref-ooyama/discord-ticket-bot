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
    # Renderは10000ポートを使用することが多いため指定
    app.run(host='0.0.0.0', port=10000)

# 2. Discordボットの設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージを読み込む権限
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# 3. !ticket コマンド（特定のロールのみ実行可能）
@bot.command()
@commands.has_any_role("監察課【ID】--Inspector Division", "幹部自衛官")
async def ticket(ctx):
    view = discord.ui.View()
    # custom_id はGAS側で識別する際に使います
    button = discord.ui.Button(label="チケット作成", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    view.add_item(button)
    await ctx.send("以下のボタンを押してチケットを作成してください。", view=view)

# 権限がない時のエラーハンドリング
@ticket.error
async def ticket_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("このコマンドを実行する権限がありません。（必要なロール：監察課【ID】--Inspector Division or 幹部自衛官）", ephemeral=True)

# 4. 起動処理
if __name__ == "__main__":
    # Webサーバーを別スレッドで起動
    Thread(target=run_web).start()
    # Discordボットを起動（Renderの環境変数TOKENを使用）
    bot.run(os.environ["TOKEN"])
