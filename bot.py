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

#when bot is ready send a message to terminal
#Functions 
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message, member):
    if message.author == client.user:
        return

    if message.content.upper.startswith('-HELP'):
        await message.channel.send('test123')

#Member joining welcoming message not working for some reason
@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to DayZero, consider checking out #start-here and #faq to get started!'
    )



#Execute
client.run(TOKEN)
