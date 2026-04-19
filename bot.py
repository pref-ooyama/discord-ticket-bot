import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# 1. Flaskの設定
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

# 3. ボタンが押された時の処理（ログ出力付き）
@bot.event
async def on_interaction(interaction: discord.Interaction):
    # 信号が来ているかログ確認
    print(f"DEBUG: Interaction received: {interaction.data.get('custom_id')}")
    
    if interaction.data.get("custom_id") == "create_ticket":
        try:
            guild = interaction.guild
            user = interaction.user
            
            # ロールID
            kanbu_id = 1311590141671899158
            kansatu_id = 1369118761352826890
            
            kanbu_role = guild.get_role(kanbu_id)
            kansatu_role = guild.get_role(kansatu_id)
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            if kanbu_role: overwrites[kanbu_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            if kansatu_role: overwrites[kansatu_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
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
            print(f"DEBUG: Channel {channel_name} created.")
            
        except Exception as e:
            # エラー内容をログに強制出力
            print(f"DEBUG ERROR: {e}")
            await interaction.response.send_message(f"エラー発生: {e}", ephemeral=True)

# 4. コマンド
@bot.command()
@commands.has_any_role("監察課【ID】--Inspector Division", "幹部自衛官")
async def ticket(ctx):
    view = discord.ui.View()
    button = discord.ui.Button(label="チケット作成", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    view.add_item(button)
    await ctx.send("以下のボタンを押してチケットを作成してください。", view=view)

# 5. 起動
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.environ["TOKEN"])
