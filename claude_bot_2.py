# discord modules
from discord.ext import commands
import discord
import os
from claude2 import ask, voice, image
from dotenv import load_dotenv

load_dotenv()

# discord bot
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

# changing the headline in the help command
help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)

bot = commands.Bot(intents = intents, command_prefix = "!", help_command=help_command)


@bot.command(name="c", help = "!c [prompt] - Pick a choice or ask Claude")
async def ask_claude(ctx, *, args):
    message = await ctx.send("Fetching answer. Please wait a moment!")
    answer = ask(args)

    chunk_length = 2000
    chunks = [answer["response"][i:i + chunk_length] for i in range(0, len(answer["response"]), chunk_length)]
    for count, chunk in enumerate(chunks):
        if count == 0:
            await message.edit(content=chunk)
        else:
            await ctx.send(content=chunk)
        await ctx.send(image(chunk))
        filename = "narrator"
        voice(chunk, filename)
        await ctx.send(file=discord.File('./data/narrator.mp3'))
        for file in os.scandir("data/"):
            os.remove(file.path)

    # await ctx.send(content=answer["token"])

@bot.command(name="quit", help = "!quit - Closes the bot")
async def quit(ctx):
    await ctx.send("Chirp! Goodbye!")
    await bot.close()

@bot.command(name="about", help = "!about - Learn how to get started.")
async def about(ctx):
    await ctx.send(
"""**I'm Claude, the game narrator!**
__About Me:__
Use `!c start` to start the adventure!""")



@bot.event
async def on_command_error(ctx, error, **kwargs):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.reply("Command not found! Do !help to see a list of commands")
    elif isinstance(error, commands.errors.UserInputError):
        await ctx.reply("Invalid arguments: Please check !help to see the available arguments")
    else:
        await ctx.reply(error)

@bot.event
async def on_connect():
    print("ready")


bot.run(TOKEN)
