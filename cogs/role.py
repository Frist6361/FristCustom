import disnake
from disnake.ext import commands
import json

class AutoroleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_autorole_data(self):
        try:
            with open('autorole.json', 'r') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_autorole_data(self, autorole_data):
        with open('autorole.json', 'w') as file:
            json.dump(autorole_data, file, indent=4)

    @commands.slash_command(description ='При заходе на сервер выдаётся роль которую вы настроили')
    @commands.has_permissions(manage_messages = True, manage_channels = True)    
    async def автороль(self, ctx, роль: disnake.Role):
        autorole_data = self.load_autorole_data()
        server_id = str(ctx.guild.id)

        autorole_data[server_id] = {'role_id': роль.id}
        self.save_autorole_data(autorole_data)

        await ctx.send(f"Автороль установлена на роль {роль.mention}", ephemeral = True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        autorole_data = self.load_autorole_data()
        server_id = str(member.guild.id)

        if server_id in autorole_data:
            role_id = autorole_data[server_id].get('role_id')
            if role_id:
                role = member.guild.get_role(role_id)
                if role:
                    try:
                        await member.add_roles(role)
                    except disnake.errors.Forbidden:
                        pass
def setup(bot):
    bot.add_cog(AutoroleCog(bot))
