import disnake
from disnake.ext import commands
from disnake import ui
import json
from chat_exporter import chat_exporter
import io
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "ticket_config.json"
        self.log_config_file = "log_settings.json"
        self.load_config()
        self.load_log_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def load_log_config(self):
        try:
            with open(self.log_config_file, 'r') as f:
                self.log_config = json.load(f)
        except FileNotFoundError:
            self.log_config = {}

    def save_log_config(self):
        with open(self.log_config_file, 'w') as f:
            json.dump(self.log_config, f, indent=4)

    @commands.slash_command(name="тикет")
    async def ticket_setup(self, ctx, категория: disnake.CategoryChannel, канал: disnake.TextChannel, админ: disnake.Role):
        guild_id = str(ctx.guild.id)
        self.config[guild_id] = {
            'category_id': категория.id,
            'channel_id': канал.id,
            'moderators_role_id': админ.id
        }
        self.save_config()
        await ctx.send(f"Настройки тикетов сохранены: Категория - {категория.mention}, Канал - {канал.mention}, Роль модераторов - {админ.mention}", ephemeral=True)
        embed = disnake.Embed(
            title="Тех. Поддержка",
            description="📦 **Нажмите на кнопку чтобы открыть тикет**",
            color=disnake.Color.blurple()
        )
        await канал.send(
            embed=embed,
            components=[
                disnake.ui.Button(
                    label="📦",
                    style=disnake.ButtonStyle.success,
                    custom_id="create_ticket"
                ),
            ]
        )

    async def create_ticket_channel(self, guild, user):
        guild_id = str(guild.id)
        category_id = self.config[guild_id]['category_id']
        category = guild.get_channel(category_id)

        if category is None:
            return await user.send("Не удалось найти указанную категорию для тикетов.")

        ticket_channel = await category.create_text_channel(f"ticket-{user}")

        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            guild.me: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            user: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        await ticket_channel.edit(overwrites=overwrites)
        return ticket_channel

    async def send_ticket_embed(self, channel, user, staff_role):
        embed = disnake.Embed(
            title=f"Тикет",
            description="Вы открыли тикет",
            color=disnake.Color.blurple()
        )

        content = f"{user.mention} {staff_role.mention}"

        await channel.send(content=content, embed=embed, components=[
            disnake.ui.Button(
                label="Закрыть тикет",
                style=disnake.ButtonStyle.secondary,
                custom_id="close_ticket"
            ),
        ])

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        if inter.component.custom_id == "create_ticket":
            user = inter.user
            guild = inter.guild
            guild_id = str(guild.id)
            staff_role_id = self.config[guild_id]['moderators_role_id']
            staff_role = guild.get_role(staff_role_id)

            if staff_role is None:
                return await inter.send("Не удалось найти роль модератора. Укажите корректный ID роли.", ephemeral=True)

            ticket_channel = await self.create_ticket_channel(guild, user)
            await self.send_ticket_embed(ticket_channel, user, staff_role)
            await inter.send(f"Тикет {ticket_channel.mention} успешно создан!", ephemeral=True)

        elif inter.component.custom_id == "close_ticket":
            channel = inter.channel
            transcript = await chat_exporter.export(
                inter.channel,
                limit=100,
                tz_info="UTC",
            )

            if transcript is None:
                return

            transcript_file = disnake.File(
                io.BytesIO(transcript.encode()),
                filename=f"transcript-{inter.channel.name}.html",
            )
            guild_id = str(channel.guild.id)

            guild_config = self.log_config.get(guild_id, {})

            if "log_channel_id" in guild_config:
                log_channel_id = int(guild_config["log_channel_id"])
                log_channel = channel.guild.get_channel(log_channel_id)

                if log_channel is not None:
                    await log_channel.send(content=f"**Экспорт чата из тикета #{channel.name}**")
                    await log_channel.send(file=transcript_file)
                else:
                    print(f"Чел не прописал канал для логов")
            else:
                print("Не найден ID канала для логов в конфигурации")

            await channel.delete()


def setup(bot):
    bot.add_cog(TicketCog(bot))
