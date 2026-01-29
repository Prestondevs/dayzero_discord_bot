"""
Authored by: Preston Vardaman
Last edited 1/29/26

This is a discord bot for the DayZero Cybersecurity Club
"""
#Imports
import discord
import os
from dotenv import load_dotenv

#Setups
load_dotenv()
TOKEN = os.getenv('TOKEN')

if not TOKEN:
    raise RuntimeError("TOKEN environment variable is not set. Set TOKEN before running the bot.")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

#Functions 
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


#Execute
client.run(TOKEN)
