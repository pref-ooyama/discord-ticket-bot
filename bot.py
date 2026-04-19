import discord
import requests
import os
from discord.ext import commands

# GASのWebアプリURLをここに貼る
GAS_URL = "https://script.google.com/macros/s/AKfycbyxD6ID0sVYVJDCgWUnnAmSoeu6mly5GslZ5n0fhCs3lIM2Wy2RBu2tVOa8KBYDX3vR/exec"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} としてログインしました")

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        # ボタンが押されたらGASに通知
        data = {
            "type": 3,
            "user": {"username": interaction.user.name},
            "channel_id": interaction.channel_id,
            "guild_id": interaction.guild_id
        }
        requests.post(GAS_URL, json=data)
        await interaction.response.send_message("チケットを作成中...", ephemeral=True)

# 環境変数からトークンを読み込む
bot.run(os.environ["TOKEN"])
