import discord
import json
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler

intents = discord.Intents.all()
bot = discord.Bot(intents = intents)

def load_data(file):
    with open(file, 'r') as f:
        return json.load(f)
    
def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)
        
def upload_cache(user_id, item, value):
    cache = load_data('data/cache.json')
    
    if str(user_id) not in cache:
        cache[str(user_id)] = {
            "join_voice_time": 0,
            "leave_voice_time": 0,
            "open_mic_time": 0,
            "listen_time": 0
        }
        
    cache[str(user_id)][item] = value
    
    save_data('data/cache.json', cache)
    
def write_data(user_id, item, value):
    data = load_data('data/user.json')
    user_id = str(user_id)
    
    if user_id not in data:
        data[user_id] = {
            "msg_sent": 0,
            "voice_joined_time": 0,
            "voice_listen_time": 0,
            "voice_speak_time": 0,
            "total_xp": 0
        }
        
    data[user_id][item] += value
    
    save_data('data/user.json', data)
    
def calculate_level(xp):
    lvl = 0
    while True:
        xp_needed = 5 * (lvl ** 2) + (50 * lvl) + 100
        if xp >= xp_needed:
            lvl += 1
        else:
            break
        
    if lvl <= 0:
        return 0
    else:
        return lvl - 1
    
async def auto_roles():
    data = load_data('data/user.json')
    config = load_data('config.json')
    
    for user_id in data:
        data[user_id]['level'] = calculate_level(data[user_id]['total_xp'])
        
        save_data('data/user.json', data)
        
        if data[user_id]['voice_joined_time'] >= 6000*60:
            level = int(data[user_id]['voice_joined_time'] // 6000*60)
            
            if level > 5:
                level = 5
            elif level < 1:
                continue
            
            guild = bot.get_guild(int(config['guild_id']))
            user = guild.get_member(int(user_id))
            role = guild.get_role(int(config['roles'][str(level)]))
            
            if role not in user.roles:
                print(f'{user} got {role}')
                
                await user.add_roles(role)
                
            if level > 1:
                for i in range(1, level):
                    old_role = guild.get_role(int(config['roles'][str(i)]))
                    
                    if old_role in user.roles:
                        print(f'{user} lost {old_role}')
                        
                        await user.remove_roles(old_role)
                        
async def auto_record():
    cache = load_data('data/cache.json')
    
    for user in bot.get_all_members():
        if user.voice is not None:
            write_data(user.id, 'voice_joined_time', time.time() - cache[str(user.id)]['join_voice_time'])
            upload_cache(user.id, 'join_voice_time', time.time())
            
            if not user.voice.self_mute:
                write_data(user.id, 'voice_speak_time', time.time() - cache[str(user.id)]['open_mic_time'])
                upload_cache(user.id, 'open_mic_time', time.time())
                
            if not user.voice.self_deaf:
                write_data(user.id, 'voice_listen_time', time.time() - cache[str(user.id)]['listen_time'])
                upload_cache(user.id, 'listen_time', time.time())
        
scheduler = AsyncIOScheduler(timezone="Asia/Taipei")

scheduler.add_job(auto_roles, 'interval', seconds=10)
scheduler.add_job(auto_record, 'interval', seconds=60)
        
scheduler.start()

config = load_data('config.json')
        
@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')
    
    cache = load_data('data/cache.json')
    
    for user in bot.get_all_members():
        if str(user.id) not in cache:
            cache[str(user.id)] = {
                "join_voice_time": 0,
                "leave_voice_time": 0,
                "open_mic_time": 0,
                "listen_time": 0
            }
            
            save_data('data/cache.json', cache)
        
        if user.voice is not None:
            if cache[str(user.id)]['join_voice_time'] == 0:
                upload_cache(user.id, 'join_voice_time', time.time())
            
            if not user.voice.self_mute and cache[str(user.id)]['open_mic_time'] == 0:
                upload_cache(user.id, 'open_mic_time', time.time())
                
            if not user.voice.self_deaf and cache[str(user.id)]['listen_time'] == 0:
                upload_cache(user.id, 'listen_time', time.time())
                
        else:
            if cache[str(user.id)]['leave_voice_time'] == 0:
                upload_cache(user.id, 'leave_voice_time', time.time())
    
@bot.event
async def on_member_join(member):
    print(f'{member} joined the server')
    
    data = load_data('data/user.json')
    cache = load_data('data/cache.json')
    
    if str(member.id) not in data:
        data[str(member.id)] = {
            "msg_sent": 0,
            "voice_joined_time": 0,
            "voice_listen_time": 0,
            "voice_speak_time": 0,
            "total_xp": 0
        }
        
    if str(member.id) not in cache:
        cache[str(member.id)] = {
            "join_voice_time": 0,
            "leave_voice_time": 0,
            "open_mic_time": 0,
            "listen_time": 0
        }
        
    save_data('data/user.json', data)
    save_data('data/cache.json', cache)
    
@bot.event
async def on_message(message):
    data = load_data('data/user.json')
    
    if message.author.bot:
        return
    
    if str(message.author.id) not in data:
        data[str(message.author.id)] = {
            "msg_sent": 0,
            "voice_joined_time": 0,
            "voice_listen_time": 0,
            "voice_speak_time": 0,
            "total_xp": 0
        }
        
    data[str(message.author.id)]['msg_sent'] += 1
    
    save_data('data/user.json', data)
    
@bot.event
async def on_message_delete(message):
    data = load_data('data/user.json')
    
    if message.author.bot:
        return
    
    if str(message.author.id) not in data:
        data[str(message.author.id)] = {
            "msg_sent": 0,
            "voice_joined_time": 0,
            "voice_listen_time": 0,
            "voice_speak_time": 0,
            "total_xp": 0
        }
        
    data[str(message.author.id)]['msg_sent'] -= 1
    
    save_data('data/user.json', data)
    
    channel = bot.get_channel(int(config['log_channel']))
    
    content = message.content if message.content else '(附件)'
    
    embed = discord.Embed(
        title='訊息刪除',
        description=f'使用者: {message.author}\n 刪除訊息: {content}',
        color=discord.Color.red()
    )
    
    await channel.send(embed=embed)
    
    if message.attachments:
        await channel.send(message.attachments[0].url)
    
@bot.event
async def on_message_edit(before, after):
    channel = bot.get_channel(int(config['log_channel']))
    
    before_content = before.content if before.content else '(附件)'
    after_content = after.content if after.content else '(附件)'
    
    embed = discord.Embed(
        title='訊息編輯',
        description=f'使用者: {before.author}\n 修改前: {before_content}\n 修改後: {after_content}',
        color=discord.Color.blue()
    )
    
    await channel.send(embed=embed)
    
    if after.attachments:
        await channel.send(after.attachments[0].url)

@bot.event
async def on_voice_state_update(member, before, after):
    cache = load_data('data/cache.json')
        
    if before.channel is None and after.channel is not None:
        print(f'{member} joined {after.channel}')
        
        upload_cache(member.id, 'join_voice_time', time.time())
        
        if not member.voice.self_mute:
            upload_cache(member.id, 'open_mic_time', time.time())
            
        if not member.voice.self_deaf:
            upload_cache(member.id, 'listen_time', time.time())
        
    elif before.channel is not None and after.channel is None:
        print(f'{member} left {before.channel}')
        
        write_data(member.id, 'voice_joined_time', time.time() - cache[str(member.id)]['join_voice_time'])
        
        if not before.self_mute:
            write_data(member.id, 'voice_speak_time', time.time() - cache[str(member.id)]['open_mic_time'])
            
        if not before.self_deaf:
            write_data(member.id, 'voice_listen_time', time.time() - cache[str(member.id)]['listen_time'])
        
    elif before.channel is not None and after.channel is not None:
        if before.self_mute and not after.self_mute:
            print(f'{member} open mic')
            
            upload_cache(member.id, 'open_mic_time', time.time())
        
        elif not before.self_mute and after.self_mute:
            print(f'{member} close mic')
            
            write_data(member.id, 'voice_speak_time', time.time() - cache[str(member.id)]['open_mic_time'])
            
        if before.self_deaf and not after.self_deaf:
            print(f'{member} listen')
            
            upload_cache(member.id, 'listen_time', time.time())
            
        elif not before.self_deaf and after.self_deaf:
            print(f'{member} no listen')
            
            write_data(member.id, 'voice_listen_time', time.time() - cache[str(member.id)]['listen_time'])  
        
        pass
    
@bot.command(name='使用者資訊', description='顯示使用者資訊')
async def show_info(ctx: discord.ApplicationContext, member: discord.Member = None):
    data = load_data('data/user.json')
    member_id = ctx.author.id
    
    if member is not None and ctx.author.guild_permissions.manage_guild:
        member_id = member.id
    
    elif member is not None and not ctx.author.guild_permissions.manage_guild:
        await ctx.respond('你沒有權限查詢別人的資訊')
        return
    
    if str(member_id) not in data:
        data[str(member_id)] = {
            "msg_sent": 0,
            "voice_joined_time": 0,
            "voice_listen_time": 0,
            "voice_speak_time": 0,
            "total_xp": 0
        }
    
    user_data = data[str(member_id)]
    
    embed = discord.Embed(
        title=f'{bot.get_user(member_id)} 的資訊',
        description=f'總發言次數: {user_data["msg_sent"]}\n'
                    f'總進入語音頻道時間: {time.strftime("%H:%M:%S", time.gmtime(user_data["voice_joined_time"]))}\n'
                    f'總語音收聽時間: {time.strftime("%H:%M:%S", time.gmtime(user_data["voice_listen_time"]))}\n'
                    f'總語音說話時間: {time.strftime("%H:%M:%S", time.gmtime(user_data["voice_speak_time"]))}\n'
                    f'總經驗值: {user_data["total_xp"]}',
        color=discord.Color.green()
    )
    
    await ctx.respond(embed=embed)
            
if __name__ == '__main__':
    bot.run(config['bot_token'])