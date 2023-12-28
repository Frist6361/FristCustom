import disnake
from disnake.ext import commands
import json
import io
from chat_exporter import chat_exporter

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
    async def ticket_setup(
        self,
        ctx,
        категория: disnake.CategoryChannel = commands.Param(desc="Выберите категорию для тикетов"),
        канал: disnake.TextChannel = commands.Param(desc="Выберите текстовый канал для тикетов"),
        админ: disnake.Role = commands.Param(desc="Выберите роль модераторов"),
        заголовок_команды: str = commands.Param(desc="Заголовок тикета при вызове команды"),
        описание_команды: str = commands.Param(desc="Описание тикета при вызове команды"),
        цвет_команды: str = commands.Param(desc="Цвет тикета (HEX) при вызове команды (без #)"),
        заголовок_открытия: str = commands.Param(desc="Заголовок тикета при открытии"),
        описание_открытия: str = commands.Param(desc="Описание тикета при открытии"),
        цвет_открытия: str = commands.Param(desc="Цвет тикета (HEX) при открытии(без #)")
    ):
        guild_id = str(ctx.guild.id)
        channel_id = str(канал.id)
        self.config[guild_id] = self.config.get(guild_id, {})
        self.config[guild_id][channel_id] = {
            'category_id': категория.id,
            'moderators_role_id': админ.id,
            'embed_title_command': заголовок_команды,
            'embed_description_command': описание_команды,
            'embed_color_command': int(цвет_команды, 16) if цвет_команды.startswith("#") else int(цвет_команды, 16),
            'embed_title_opening': заголовок_открытия,
            'embed_description_opening': описание_открытия,
            'embed_color_opening': int(цвет_открытия, 16) if цвет_открытия.startswith("#") else int(цвет_открытия, 16)
        }
        self.save_config()
        await ctx.send(f"Настройки тикетов сохранены: Категория - {категория.mention}, Канал - {канал.mention}, Роль модераторов - {админ.mention}", ephemeral=True)
        embed = disnake.Embed(
            title=заголовок_команды,
            description=описание_команды,
            color=disnake.Color(int(цвет_команды, 16) if цвет_команды.startswith("#") else int(цвет_команды, 16))
        )
        await канал.send(
            embed=embed,
            components=[
                disnake.ui.Button(
                    label="Отрыть тикет",
                    style=disnake.ButtonStyle.success,
                    custom_id="create_ticket"
                ),
            ]
        )

    async def create_ticket_channel(self, guild, user, channel_id):
        guild_id = str(guild.id)
        category_id = self.config[guild_id][channel_id]['category_id']
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

    async def send_ticket_embed(self, channel, user, staff_role, channel_id, is_command=True):
        embed_title_key = 'embed_title_command' if is_command else 'embed_title_opening'
        embed_description_key = 'embed_description_command' if is_command else 'embed_description_opening'
        embed_color_key = 'embed_color_command' if is_command else 'embed_color_opening'

        embed = disnake.Embed(
            title=self.config[str(channel.guild.id)][channel_id][embed_title_key],
            description=self.config[str(channel.guild.id)][channel_id][embed_description_key],
            color=disnake.Color(self.config[str(channel.guild.id)][channel_id][embed_color_key])
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
            if inter.guild is None:
                return

            user = inter.user
            guild = inter.guild
            guild_id = str(guild.id)
            channel_id = str(inter.channel.id)

            if guild_id not in self.config or channel_id not in self.config[guild_id]:
                return await inter.send("Настройки тикетов не найдены для этого сервера или канала.", ephemeral=True)

            staff_role_id = self.config[guild_id][channel_id]['moderators_role_id']
            staff_role = guild.get_role(staff_role_id)

            if staff_role is None:
                return await inter.send("Не удалось найти роль модератора. Укажите корректный ID роли.", ephemeral=True)

            ticket_channel = await self.create_ticket_channel(guild, user, channel_id)
            await self.send_ticket_embed(ticket_channel, user, staff_role, channel_id, is_command=False)
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
