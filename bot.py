import disnake
from disnake.ext import commands
import json
import os
from config import TOKEN
from disnake import OptionChoice, OptionType
def load_reactions_data():
    try:
        with open('reactions.json', 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


reactions_data = load_reactions_data()
intents = disnake.Intents.all()

bot = commands.Bot(command_prefix='/', intents=intents, activity=disnake.Game(name="Powered by Fristikon"))

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')

@bot.slash_command(description='Автореакции')
@commands.has_permissions(manage_messages = True, manage_channels = True)
async def реакции(
    ctx,
    канал: disnake.TextChannel, 
    действие: str = commands.Param(
        choices=[
            OptionChoice(name="Добавить", value="Добавить"),
            OptionChoice(name="Удалить", value="Удалить")
        ]
    ),
    emoji: str = commands.Param()
):
    if действие == "Добавить":
        if emoji not in reactions_data.get(str(канал.id), {}).get('emojis', []):
            reactions_data.setdefault(str(канал.id), {}).setdefault('emojis', {})[emoji] = True
            await ctx.send(f"Реакция '{emoji}' будет добавлена в канал {канал.mention} для новых сообщений.", ephemeral=True)
        else:
            # Если реакция уже существует, вы можете явно установить ее значение на True
            reactions_data[str(канал.id)]['emojis'][emoji] = True
            await ctx.send(f"Реакция '{emoji}' будет добавлена в канал {канал.mention} для новых сообщений.",ephemeral=True)
    elif действие == "Удалить":
        if emoji in reactions_data.get(str(канал.id), {}).get('emojis', []):
            reactions_data[str(канал.id)]['emojis'][emoji] = False
            await ctx.send(f"Реакция '{emoji}' будет удалена из канала {канал.mention} для новых сообщений.", ephemeral=True)
        else:
            await ctx.send(f"Реакции '{emoji}' нет в канале {канал.mention}.", ephemeral=True)

    with open('reactions.json', 'w') as file:
        json.dump(reactions_data, file, indent=4)

@bot.slash_command(description='Автоветки')
@commands.has_permissions(manage_messages = True, manage_channels = True)
async def ветки(
    ctx,
    канал: disnake.TextChannel, 
    действие: str = commands.Param(
        choices=[
            OptionChoice(name="Добавить", value="Добавить"),
            OptionChoice(name="Удалить", value="Удалить")
        ],
    ),
    name: str = commands.Param()
):



    thread_data = load_thread_data()

    if действие == "Добавить":
        thread_data.setdefault(str(канал.id), {}).setdefault('threads', {})[name] = True
        save_thread_data(thread_data)

        await ctx.send(f"Автоветка успешно добавлена для канала {канал}!", ephemeral=True)
    elif действие == "Удалить":
        thread_data.setdefault(str(канал.id), {}).setdefault('threads', {})[name] = False
        save_thread_data(thread_data)

        await ctx.send(f"Автоветка успешно удалена для канала {канал}!", ephemeral=True)




@bot.event
async def on_message(message):
    # Загрузка данных о реакциях
    reactions_data = load_reactions_data()
    thread_data = load_thread_data()

    # Проверка, существует ли запись для канала в reactions_data
    channel_id = str(message.channel.id)
    if channel_id not in reactions_data:
        return

    for emoji, should_react in reactions_data[channel_id].get('emojis', {}).items():
        if should_react and not (message.author.bot or message.is_system()):
            await message.add_reaction(emoji)


    for thread_name, should_create in thread_data[str(message.channel.id)].get('threads', {}).items():
        if should_create:
            thread = await message.create_thread(name=thread_name)

            welcome_message = await thread.send(f".")

            await welcome_message.delete()





def load_thread_data():
    try:
        with open('thread.json', 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_thread_data(thread_data):
    with open('thread.json', 'w') as file:
        json.dump(thread_data, file, indent=4)


bot.run(TOKEN)