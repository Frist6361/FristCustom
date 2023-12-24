import json
from disnake.ext import commands
import disnake
import yt_dlp
import asyncio

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_file = "queue.json"
        self.queue = {}
        self.check_voice_timer = self.bot.loop.create_task(self.check_voice_channel())

    async def save_queue(self):
        with open(self.queue_file, 'w') as f:
            json.dump(self.queue, f)

    async def load_queue(self):
        try:
            with open(self.queue_file, 'r') as f:
                content = f.read()
                if content:
                    self.queue = json.loads(content)
                else:
                    self.queue = {}
        except FileNotFoundError:
            self.queue = {}

    async def play_next(self, voice_client, error=None):
        if error:
            print(f'Error: {error}')

        guild_id = str(voice_client.guild.id)
        if self.queue[guild_id]:
            next_track = self.queue[guild_id].pop(0)
            url = next_track['url']
            title = next_track['title']

            FFMPEG_OPTIONS = {'before_options': '-reconnect 1', 'options': '-vn'}
            voice_client.play(disnake.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after=lambda e: self.bot.loop.create_task(self.after_play(voice_client, e)))
        else:
            self.is_playing = False
            await voice_client.disconnect()

    async def after_play(self, voice_client, error):
        if error:
            print(f'Error: {error}')
        await self.play_next(voice_client)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_queue()

    async def check_voice_channel(self):
        while True:
            await asyncio.sleep(1)
            for guild in self.bot.guilds:
                if guild.voice_client and guild.voice_client.is_connected():
                    if len(guild.voice_client.channel.members) <= 1:
                        await guild.voice_client.disconnect()

    @commands.slash_command(name="играть", description="Воспроизвести музыку")
    async def play(self, ctx, ссылка: str):
        member = ctx.author
        if not member.voice or not member.voice.channel:
            return await ctx.send("Вы должны быть в голосовом канале, чтобы использовать эту команду.", ephemeral=True)
        await ctx.send('Начинаю поиск...', ephemeral=True)

        ydl_opts = {'format': 'bestaudio/best'}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1', 'options': '-vn'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(ссылка, download=False)
            url = info['url'] if 'url' in info else None

            if not url:
                return await ctx.send("Не удалось получить прямой URL для данного запроса.", ephemeral=True)

            guild_id = str(ctx.guild.id)
            if guild_id not in self.queue:
                self.queue[guild_id] = []

            if not ctx.guild.voice_client or not ctx.guild.voice_client.is_connected():
                voice_channel = await member.voice.channel.connect()

            if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
                self.queue[guild_id].append({'url': url, 'title': info.get('title', 'Неизвестное название'), 'duration': info.get('duration', 'Неизвестная длительность')})
                await ctx.send(f"Трек '{info['title']}' добавлен в очередь.", ephemeral=True)
            else:
                try:
                    ctx.guild.voice_client.play(disnake.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after=lambda e: self.bot.loop.create_task(self.after_play(ctx.guild.voice_client, e)))
                except RuntimeError:
                    pass

                embed = disnake.Embed(title=f"Сейчас играет: {info['title']}", description=f"Длительность: {info['duration']} секунд", color=disnake.Color.blurple())
                embed.add_field(name="Позиция в очереди", value=f"{len(self.queue[guild_id])+1}", inline=True)
                await ctx.send(embed=embed, ephemeral=True)
                await self.save_queue()

    @commands.slash_command(name="очередь", description="Показать текущую очередь")
    async def queue_command(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.queue and self.queue[guild_id]:
            queue_info = "\n".join([f"{index + 1}. {track['title']} ({track['duration']} секунд)" for index, track in enumerate(self.queue[guild_id])])
            await ctx.send(f"Текущая очередь:\n{queue_info}", ephemeral=True)
        else:
            await ctx.send("Очередь пуста.", ephemeral=True)

        await self.save_queue()

    @commands.slash_command(name="скип", description="Пропустить текущий трек")
    async def skip(self, ctx):
        guild_id = str(ctx.guild.id)
        ffmpeg_path = "ffmpeg/ffmpeg.exe"
        
        if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
            ctx.guild.voice_client.stop()
            await ctx.send("Трек пропущен.", ephemeral=True)

            if guild_id in self.queue and self.queue[guild_id]:
                next_track = self.queue[guild_id].pop(0)
                url = next_track['url']
                title = next_track['title']

                voice_state = ctx.author.voice
                if voice_state:
                    voice_channel = voice_state.channel
                    if not voice_channel.guild.voice_client or not voice_channel.guild.voice_client.is_connected():
                        await voice_channel.connect()

                    FFMPEG_OPTIONS = {'before_options': '-reconnect 1', 'options': '-vn'}
                    ctx.guild.voice_client.play(disnake.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after=lambda e: self.bot.loop.create_task(self.after_play(ctx.guild.voice_client, e)))
                    await ctx.send(f"Сейчас играет: {title}", ephemeral=True)
                else:
                    await ctx.send("Вы не подключены к голосовому каналу.", ephemeral=True)
        else:
            await ctx.send("Нет активного трека для пропуска.", ephemeral=True)

        await self.save_queue()

    @commands.slash_command(name='выйти', description='Бот выходит из голосового канала')
    async def leave(self, ctx):
        member = ctx.author
        if member.voice and member.voice.channel:  
            if ctx.guild.voice_client:
                await ctx.guild.voice_client.disconnect()
                await ctx.send('Бот успешно вышел!', ephemeral=True)
            else:
                await ctx.send('Бот не подключен к голосовому каналу.', ephemeral=True)
        else:
            await ctx.send("Вы должны быть в голосовом канале, чтобы использовать эту команду.", ephemeral=True)

def setup(bot):
    bot.add_cog(MusicCog(bot))
