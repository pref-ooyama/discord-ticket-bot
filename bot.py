import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# 1. Flaskの設定 (Render用)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Discordボットの設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# 3. ボタンが押された時の処理（全サーバー対応版）
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data.get("custom_id") == "create_ticket":
        print(f"DEBUG: 受信 - {interaction.user.name} がチケット作成ボタンを押しました")
        
        try:
            guild = interaction.guild
            user = interaction.user
            
            # 【重要】ロール名で検索（どのサーバーでも名前さえあればOK）
            # ロール名がサーバーの表記と完全に一致している必要があります
            kanbu_role = discord.utils.get(guild.roles, name="幹部自衛官")
            kansatu_role = discord.utils.get(guild.roles, name="監察課【ID】--Inspector Division")
            
            print(f"DEBUG: 検索結果 - 幹部: {kanbu_role}, 監察課: {kansatu_role}")
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            
            if kanbu_role:
                overwrites[kanbu_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            if kansatu_role:
                overwrites[kansatu_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            # チャンネル名決定
            count = 1
            base_name = f"ticket-{user.name.lower()}"
            channel_name = base_name
            while any(c.name == channel_name for c in guild.text_channels):
                count += 1
                channel_name = f"{base_name}{count:02d}"
            
            # チャンネル作成
            new_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
            
            await interaction.response.send_message(f"チケットを作成しました: {new_channel.mention}", ephemeral=True)
            print(f"DEBUG: 成功 - {channel_name} を作成しました")
            
        except Exception as e:
            error_msg = f"エラー発生: {e}"
            print(f"DEBUG ERROR: {error_msg}")
            # エラーを直接Discordに通知
            if not interaction.response.is_done():
                await interaction.response.send_message(error_msg, ephemeral=True)

# 4. コマンド (!ticket)
@bot.command()
async def ticket(ctx):
    # メッセージの送受信チェック
    if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
        print("DEBUG: このチャンネルで発言権限がありません")
        return

    view = discord.ui.View()
    button = discord.ui.Button(label="チケット作成", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    view.add_item(button)
    await ctx.send("以下のボタンを押してチケットを作成してください。", view=view)

# 5. 起動
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.environ["TOKEN"])
