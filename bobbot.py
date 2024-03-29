import os

import discord
from discord.ext import commands

import settings

intents = discord.Intents(guilds=True, members=True, messages=True)

bot = commands.Bot(command_prefix=settings.COMMAND_PREFIX, intents=intents)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')


@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'Loaded extension {extension}.py')
    await ctx.message.delete()


@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    await ctx.send(f'Unloaded extension {extension}.py')
    await ctx.message.delete()


@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'Reloaded extension {extension}.py')
    await ctx.message.delete()

# Main
if __name__ == '__main__':
    bot.run(settings.DISCORD_TOKEN)
