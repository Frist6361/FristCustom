import disnake
from disnake.ext import commands

class ClearCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='очистка', description='Удалить указанное количество сообщений из текущего канала')
    @commands.has_permissions(manage_messages = True, manage_channels = True)    
    async def clear_messages(
        self,
        ctx,
        количество_сообщений: int = commands.Param(description='Количество сообщений для удаления')
    ):
        if количество_сообщений <= 0:
            await ctx.send('Количество сообщений для удаления должно быть положительным числом.', ephemeral=True)
            return

        try:
            await ctx.channel.purge(limit=количество_сообщений)
            await ctx.send(f'Удалено {количество_сообщений} сообщений.', ephemeral=True)
        except disnake.errors.Forbidden:
            await ctx.send('У меня нет прав на удаление сообщений.', ephemeral=True)
def setup(bot):
    bot.add_cog(ClearCog(bot))
