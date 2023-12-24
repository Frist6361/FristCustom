import disnake
from disnake.ext import commands
import json

class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_deleted_message(self, guild_id, channel_id, author_id, author_name, content, channel_name):
        guild = self.bot.get_guild(guild_id)
        if guild:
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    author = await self.bot.fetch_user(author_id)
                    embed = disnake.Embed(
                        title="Удалённое сообщение",
                        description=f"**Автор:** {author.mention}\n**Канал:** #{channel_name}\n**Сообщение:** {content}\n",
                        color=disnake.Color.red()
                    )
                    avatar_url = author.avatar
                    embed.set_thumbnail(url=f'{avatar_url}')
                    await channel.send(embed=embed)
                except disnake.errors.HTTPException as e:
                    print(f"Failed to fetch user: {e}")

    @commands.slash_command(name='логи', description='Настройка канала для логов')
    @commands.has_permissions(manage_messages = True, manage_channels = True)
    async def set_log_channel(
        self,
        inter,
        канал: disnake.TextChannel = commands.Param(description='Укажите канал для логов')
    ):
        guild_id = str(inter.guild.id)
        log_settings = {}

        try:
            with open('log_settings.json', 'r') as file:
                log_settings = json.load(file)
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            print("Error decoding JSON. File may be empty.")
            log_settings = {}

        log_settings[guild_id] = {'log_channel_id': str(канал.id)}

        with open('log_settings.json', 'w') as file:
            json.dump(log_settings, file, indent=4)

        await inter.send(f'Канал для логов успешно установлен: {канал.mention}', ephemeral=True)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot and message.guild:
            guild_id = str(message.guild.id)
            try:
                with open('log_settings.json', 'r') as file:
                    log_settings = json.load(file)
            except FileNotFoundError:
                print("Log settings file not found.")
                return
            except json.decoder.JSONDecodeError:
                print("Error decoding JSON. File may be empty.")
                log_settings = {}

            if guild_id in log_settings:
                channel_id = log_settings[guild_id]['log_channel_id']
                author = f"{message.author.name}#{message.author.discriminator}"
                content = message.content
                channel_name = message.channel.name
                await self.log_deleted_message(int(guild_id), int(channel_id), message.author.id, author, content, channel_name)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        guild_id = str(member.guild.id)
        try:
            with open('log_settings.json', 'r') as file:
                log_settings = json.load(file)
        except FileNotFoundError:
            return
        except json.decoder.JSONDecodeError:
            log_settings = {}

        if guild_id in log_settings:
            channel_id = log_settings[guild_id]['log_channel_id']
            channel = member.guild.get_channel(int(channel_id))

            if channel:
                if before.channel != after.channel:
                    action = "Вошел в" if after.channel else "Вышел из"
                    voice_channel_name = after.channel.name if after.channel else before.channel.name
                    author = f"{member.name}#{member.discriminator}"

                    embed = disnake.Embed(
                        title=f"{action} голосовой канал",
                        description=f"**Пользователь:** {member.mention}\n**Канал:** #{voice_channel_name}",
                        color=disnake.Color.green() if after.channel else disnake.Color.red()
                    )

                    avatar_url = member.avatar.url if member.avatar else None
                    embed.set_thumbnail(url=f'{avatar_url}')
                    await channel.send(embed=embed)
            else:
                print("Log channel not found.")
        else:
            print("Guild ID not found in log settings.")



    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            guild_id = str(before.guild.id)
            try:
                with open('log_settings.json', 'r') as file:
                    log_settings = json.load(file)
            except FileNotFoundError:
                return
            except json.decoder.JSONDecodeError:
                log_settings = {}

            if guild_id in log_settings:
                channel_id = log_settings[guild_id]['log_channel_id']
                log_channel = before.guild.get_channel(int(channel_id))

                if log_channel:
                    member = after
                    changed_roles = set(after.roles) - set(before.roles)
                    removed_roles = set(before.roles) - set(after.roles)

                    if changed_roles or removed_roles:
                        embed = disnake.Embed(
                            title="Обновление ролей",
                            description=f"**Пользователь:** {member.mention}\n"
                                        f"**Добавлены роли:** {', '.join(role.mention for role in changed_roles)}\n"
                                        f"**Удалены роли:** {', '.join(role.mention for role in removed_roles)}",
                            color=disnake.Color.orange()
                        )

                        avatar_url = member.avatar
                        if avatar_url == None:
                            avatar_url = 'https://media.discordapp.net/attachments/982269337727549530/982275492096901130/123123.png' 
                        embed.set_thumbnail(url=f'{avatar_url}')
                        await log_channel.send(embed=embed)
                else:
                    print("Log channel not found.")
            else:
                print("Guild ID not found in log settings.")
        if before.nick != after.nick:
            guild_id = str(before.guild.id)
            try:
                with open('log_settings.json', 'r') as file:
                    log_settings = json.load(file)
            except FileNotFoundError:
                return
            except json.decoder.JSONDecodeError:
                log_settings = {}

            if guild_id in log_settings:
                channel_id = log_settings[guild_id]['log_channel_id']
                log_channel = before.guild.get_channel(int(channel_id))

                if log_channel:
                    member = after
                    old_nick = before.nick if before.nick else "None"
                    new_nick = after.nick if after.nick else "None"

                    embed = disnake.Embed(
                        title="Изменение ника",
                        description=f"**Пользователь:** {member.mention}\n"
                                    f"**Старый ник:** {old_nick}\n"
                                    f"**Новый ник:** {new_nick}",
                        color=disnake.Color.blue()
                    )

                    avatar_url = member.avatar.url if member.avatar else None
                    embed.set_thumbnail(url=avatar_url)

                    await log_channel.send(embed=embed)
                else:
                    print("Log channel not found.")
            else:
                print("Guild ID not found in log settings.")
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            guild_id = str(before.guild.id)
            try:
                with open('log_settings.json', 'r') as file:
                    log_settings = json.load(file)
            except FileNotFoundError:
                return
            except json.decoder.JSONDecodeError:
                log_settings = {}

            if guild_id in log_settings:
                channel_id = log_settings[guild_id]['log_channel_id']
                log_channel = before.guild.get_channel(int(channel_id))

                if log_channel:
                    author = before.author

                    embed = disnake.Embed(
                        title="Изменение сообщения",
                        description=f"**Автор:** {author.mention}\n"
                                    f"**Канал:** #{before.channel.name}\n"
                                    f"**Старое сообщение:** {before.content}\n"
                                    f"**Новое сообщение:** {after.content}",
                        color=disnake.Color.gold()
                    )

                    avatar_url = author.avatar.url if author.avatar else None
                    embed.set_thumbnail(url=avatar_url)

                    await log_channel.send(embed=embed)
                else:
                    print("Log channel not found.")
            else:
                print("Guild ID not found in log settings.")

def setup(bot):
    bot.add_cog(LogsCog(bot))
