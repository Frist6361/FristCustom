import disnake
from disnake.ext import commands
import json
import asyncio

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mute_role_settings = self.load_mute_role_settings()
        self.muted_users = self.load_muted_users()
        self.log_settings = self.load_log_settings()

    def load_mute_role_settings(self):
        try:
            with open('mute_role_settings.json', 'r') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_mute_role_settings(self):
        with open('mute_role_settings.json', 'w') as file:
            json.dump(self.mute_role_settings, file, indent=4)

    def load_muted_users(self):
        try:
            with open('muted_users.json', 'r') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_muted_users(self):
        with open('muted_users.json', 'w') as file:
            json.dump(self.muted_users, file, indent=4)

    def load_log_settings(self):
        try:
            with open('log_settings.json', 'r') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    async def send_punishment_dm(self, user, punishment_type, duration, reason):
        avatar_url = user.avatar.url if hasattr(user.avatar, "url") else None
        embed = disnake.Embed(
            title=f'Вы получили {punishment_type.lower()}',
            description=f'**Длительность:** {duration} минут\n**Причина:** {reason}',
            color=disnake.Color.red()
        )
        embed.set_thumbnail(url=avatar_url)
        await user.send(embed=embed)

    async def log_punishment(self, ctx, target, punishment_type, reason, duration=None):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.log_settings:
            return

        log_channel_id = self.log_settings[guild_id]['log_channel_id']
        log_channel = ctx.guild.get_channel(int(log_channel_id))
        if not log_channel:
            print("Log channel not found.")
            return

        moderator = ctx.author
        avatar_url = target.avatar.url if hasattr(target.avatar, "url") else None

        description = f'**Модератор:** {moderator.mention}\n**Получил наказание** {target.mention}\n'
        if duration:
            description += f'**Длительность:** {duration} минут\n'
        if reason:
            description += f'**Причина:** {reason}\n'

        embed = disnake.Embed(
            title=f'{punishment_type} для {target.name}',
            description=description,
            color=disnake.Color.red() if punishment_type == 'Бан' else disnake.Color.orange() if punishment_type == 'Кик' else disnake.Color.blue()
        )
        embed.set_thumbnail(url=avatar_url)
        await log_channel.send(embed=embed)

    @commands.slash_command(name='рольмут', description='Настройка роли мута')
    async def set_mute_role(
        self,
        ctx,
        роль: disnake.Role = commands.Param(description='Роль для мута')
    ):
        self.mute_role_settings[str(ctx.guild.id)] = {'mute_role_id': str(роль.id)}
        self.save_mute_role_settings()
        await ctx.send(f'Роль мута успешно установлена: {роль.mention}', ephemeral=True)

    @commands.slash_command(name='бан', description='Забанить пользователя')
    async def ban(
        self,
        ctx,
        участник: disnake.Member = commands.Param(description='Пользователь для бана'),
        причина: str = commands.Param(description='Причина бана')
    ):
        await участник.ban(reason=причина)
        await ctx.send(f'{участник.mention} был забанен.', ephemeral=True)

        await self.log_punishment(ctx, участник, 'Бан', reason=причина)
        await self.send_punishment_dm(участник, 'Бан', '-', причина)


    @commands.slash_command(name='кик', description='Выгнать пользователя')
    async def kick(
        self,
        ctx,
        участник: disnake.Member = commands.Param(description='Пользователь для кика'),
        причина: str = commands.Param(description='Причина кика')
    ):
        await участник.kick(reason=причина)
        await ctx.send(f'{участник.mention} был выгнан.', ephemeral=True)
        await self.log_punishment(ctx, участник, 'Кик', reason=причина)        
        await self.send_punishment_dm(участник, 'Кик', '-', причина)


    @commands.slash_command(name='мут', description='Замутить пользователя на время')
    async def mute(
        self,
        ctx,
        участник: disnake.Member = commands.Param(description='Пользователь для мута'),
        время: int = commands.Param(description='Длительность мута в минутах'),
        причина: str = commands.Param(description='Причина мута')
    ):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.mute_role_settings:
            await ctx.send('Роль мута не установлена. Используйте /рольмут для установки.',ephemeral=True)
            return

        мут_роль_id = self.mute_role_settings[guild_id].get('mute_role_id')
        if not мут_роль_id:
            await ctx.send('ID роли мута не найдено. Установите роль мута снова с помощью /рольмут.',ephemeral=True)
            return

        мут_роль = ctx.guild.get_role(int(мут_роль_id))
        if not мут_роль:
            await ctx.send('Роль мута не найдена. Укажите корректный ID роли в коде кога или установите роль мута снова с помощью /рольмут.',ephemeral=True)
            return

        user_id = участник.id
        if user_id in self.muted_users:
            await ctx.send(f'{участник.mention} уже замучен. Используйте /размут перед новым мутом.',ephemeral=True)
            return

        await участник.add_roles(мут_роль, reason=причина)
        await ctx.send(f'{участник.mention} был замучен на {время} минут.', ephemeral=True)
        await self.log_punishment(ctx, участник, 'Мут', duration=время, reason=причина)
        await self.send_punishment_dm(участник, 'Мут', время, причина)

        self.muted_users[user_id] = {'duration': время, 'reason': причина}
        self.save_muted_users()

        await asyncio.sleep(время * 60)
        if user_id in self.muted_users:
            await участник.remove_roles(мут_роль)
            del self.muted_users[user_id]
            self.save_muted_users()




    @commands.slash_command(name='размут', description='Размутить пользователя')
    async def unmute(
        self,
        ctx,
        участник: disnake.Member = commands.Param(description='Пользователь для размута'),
        причина: str = commands.Param(description='Причина размута')
    ):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.mute_role_settings:
            await ctx.send('Роль мута не установлена. Используйте /рольмут для установки.',ephemeral=True)
            return

        мут_роль_id = self.mute_role_settings[guild_id].get('mute_role_id')
        if not мут_роль_id:
            await ctx.send('ID роли мута не найдено. Установите роль мута снова с помощью /рольмут.',ephemeral=True)
            return

        мут_роль = ctx.guild.get_role(int(мут_роль_id))
        if not мут_роль:
            await ctx.send('Роль мута не найдена. Укажите корректный ID роли в коде кога или установите роль мута снова с помощью /рольмут.',ephemeral=True)
            return

        if участник.id not in self.muted_users:
            await ctx.send(f'{участник.mention} не был замучен. Используйте /мут перед /размутом.',ephemeral=True)
            return

        await участник.remove_roles(мут_роль)
        await ctx.send(f'{участник.mention} был размучен.', ephemeral=True)

        await self.log_punishment(ctx, участник, 'Размут', причина)

        del self.muted_users[участник.id]
        self.save_muted_users()

def setup(bot):
    bot.add_cog(ModerationCog(bot))
