import disnake
from disnake.ext import commands

import sqlite3

class Voice:

    def __init__(self):
        self.db = sqlite3.connect(f'voice.db')
        self.table = self.db.cursor()

    async def check_owner_in_voice(self, inter, members, voice):
        self.table.execute("SELECT owner FROM VoiceChannels WHERE voiceID = ?",(voice,))
        voice_owner = self.table.fetchone()
        user = await self.bot.fetch_user(int(voice_owner[0]))
        
        x = None
        for owner in members:
            if owner == user:
                x = 1
                break
            if owner != user:
                x = 0
            
        if x == 0:
            self.table.execute("UPDATE VoiceChannels SET owner = ? WHERE voiceID = ?",(inter.author.id, voice,))
            self.db.commit()
            await inter.send('**Вы стали новым владельцем канала**', ephemeral = True)
            before_owner = await self.bot.fetch_user(voice_owner[0])
            after_owner = await self.bot.fetch_user(inter.author.id)
            await inter.channel.set_permissions(before_owner, view_channel = None, connect = None, manage_channels = None)
            await inter.channel.set_permissions(after_owner, view_channel = True, connect = True, manage_channels = True)
            
        if x == 1:
            await inter.send('**Владелец канала находится в нём**', ephemeral = True)
    
    async def check_user_in_voice(self, inter, members, kick_member):
        try:
            user_kick = disnake.utils.get(inter.guild.members, id = int(kick_member))
            x = 0
            for kick in members:
                if kick == user_kick:
                    x = 1
                    break
                if kick != user_kick:
                    x = 0
            
            if x == 1:
                await inter.channel.set_permissions(user_kick, connect = False)
                await user_kick.move_to(None)
                await inter.send(f'**Пользователь {user_kick.mention} кикнут из вашего войса**', ephemeral = True)
                
            if x == 0:
                await inter.send(f'**{user_kick.mention} не получилось кикнуть из войса**', ephemeral = True)
        except ValueError:
            await inter.send('**ОШИБКА: Необходимо упомянуть участника, которого вы хотите кикнуть из войса. Нажмите на кнопку ещё раз и пинганите участника**', ephemeral = True)

    async def voice_panel_edit(self, inter):
        self.table.execute("SELECT * FROM VoiceChannels WHERE voiceID = ?",(inter.channel.id,))
        voice_info = self.table.fetchone()
        embed1 = disnake.Embed(title = 'Информация о канале', description = f'**Владелец:** <@{voice_info[0]}>\n**Видимость:** {voice_info[1]}\n**Доступ:** {voice_info[2]}', color = disnake.Colour(0x2f3136))             
        await inter.message.edit(embeds = [embed1, self.embed])

    async def name_channel_check(self, member, name = None):
        user = await self.bot.fetch_user(int(member))
        names = None
        if name is None:
            self.table.execute("SELECT name FROM VoiceName WHERE userID = ?",(member,))
            names_db = self.table.fetchone()
            names = None
            if names_db is None:
                names = f'Комната {user.name}'
            if names_db is not None:
                names = names_db[0]

        if name is not None:
            self.table.execute("SELECT * FROM VoiceName WHERE userID = ?",(member,))
            name_db = self.table.fetchone()
            if name_db is not None:
                self.table.execute("UPDATE VoiceName SET name = ? WHERE userID = ?",(name, member,))
                self.db.commit()   
            
            if name_db is None:
                self.table.execute("INSERT INTO VoiceName VALUES (?, ?)",(member, name,))
                self.db.commit()
            
        return names 
