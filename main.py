import os
import discord
from discord.ext import commands
from datetime import datetime
import pytz
import asyncio
from datetime import datetime, timedelta

from myserver import server_on


# Setup intents and bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global data storage
start_data = {}
start_time = None
finish_time = None

async def scheduled_task():
    await bot.wait_until_ready()
    channel_id = 1329786018353778760  # 🔁 ใส่ Channel ID ที่ต้องการให้บอทส่งข้อความ
    channel = bot.get_channel(channel_id)

    while not bot.is_closed():
        now = datetime.now(pytz.timezone("Asia/Tokyo"))
        target = now.replace(hour=00, minute=10, second=0, microsecond=0)

        # ถ้าเวลาตอนนี้เกินเป้าหมายแล้ว ให้เลื่อนไปวันถัดไป
        if now > target:
            target += timedelta(days=1)

        # รอจนกว่าจะถึงเวลาเป้าหมาย
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        if channel:
            await channel.send("日本人 Are you 眠い？？ ᶻ 𝗓 𐰁")

@bot.event
async def on_ready():
    print('Bot is online!! He ready to work now!')

    asyncio.create_task(scheduled_task())

    #channel_id = 1329786018353778760  # 🔁 ใส่ Channel ID ที่ต้องการให้บอทส่งข้อความ
    #channel = bot.get_channel(channel_id)
    #if channel:
    #    await channel.send("ระวังตื่นสายเด้อ")
    #asyncio.create_task(scheduled_task())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()

    # ✅ ตอบ hi เมื่อพิมพ์ hello
    if content == "hello":
        await message.channel.send(f"Hello {message.author.mention} Ekae")
        return

    # ✅ ตอบ xxxx ถ้ามีคำว่า zzzzz หรือคำใกล้เคียง
    if any(keyword in content for keyword in ["good night", "おやすみ", "gn", "oyasumi" , 'นอน']):
        await message.channel.send(f"sweet dreams~ 😴😴 {message.author.mention}")
        return
    
    if any(keyword in content for keyword in ["ohayou", "おはよう", "good morning"]):
        await message.channel.send(f"Good morning (❁´◡`❁) 😃🌞 {message.author.mention}")
        return
    
    if any(keyword in content for keyword in ["he is"]):
        await message.channel.send(f"He is the fastest cashier I know 🏃🏻‍♂️🏃🏻‍♂️")
        return
    
    if any(keyword in content for keyword in ["love",'♡']):
        await message.channel.send(f"I love you (´▽`ʃ♡ƪ) {message.author.mention}")
        return
    
    if any(keyword in content for keyword in ["crystie chu contente"]) :
        await message.channel.send(f"Are you calling me ?? (≧∀≦)ゞ\nCrystie Chu Contente, that's my name! ∘ ∘ ∘ ( °ヮ° ) ? {message.author.mention}")
        return
    
    if any(keyword in content for keyword in ["kak",'noob','heta','กาก']):
        await message.channel.send(f"No!! Mui kak trust me ദ്ദി(˵ •̀ ᴗ - ˵ ) ✧ \n Ammy tell me this")
        return


    # ✅ รองรับหลายคำสั่งในข้อความเดียว
    lines = message.content.strip().split('\n')
    for line in lines:
        message.content = line.strip()
        await bot.process_commands(message)



# /////////////////////////////////////////////////////////////////////////////////////////
# Command

@bot.command()
async def start(ctx, name: str, value: int):
    global start_time
    if start_time is None:
        start_time = datetime.now(pytz.timezone("Asia/Tokyo"))
    start_data[name] = {'start': value, 'result': None}
    await ctx.send(f"📥 Got it! now {name} have {value} crystal")

@bot.command()
async def finish(ctx, name: str, value: int):
    global finish_time
    if name not in start_data:
        await ctx.send(f"⚠️ Are you forget to tell me how many crystal that {name} have?")
        return
    if finish_time is None:
        finish_time = datetime.now(pytz.timezone("Asia/Tokyo"))
    result = value - start_data[name]['start']
    start_data[name]['result'] = result
    await ctx.send(f"{name.capitalize()} : {result}")

@bot.command()
async def reset(ctx, name: str = None):
    global start_time, finish_time
    if name:
        if name in start_data:
            del start_data[name]
            await ctx.send(f"🧹 Reset {name}'s Data")
        else:
            await ctx.send(f"⚠️ Cannot find {name}'s Data")
    else:
        start_data.clear()
        start_time = None
        finish_time = None
        await ctx.send("🧼 Reset everyone Data")

@bot.command()
async def summary(ctx):
    global start_data, start_time, finish_time
    if not start_time or not finish_time or all(data['result'] is None for data in start_data.values()):
        await ctx.send("❌ Not enough data to summarize. Make sure to use !start and !finish first.")
        return

    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    date_str = now.strftime("%d/%m/%Y")
    start_str = start_time.strftime("%H:%M:%S")
    finish_str = finish_time.strftime("%H:%M:%S")
    total_duration = str(finish_time - start_time).split(".")[0]

    sorted_results = sorted(
        [(name, data['result']) for name, data in start_data.items() if data['result'] is not None],
        key=lambda x: x[1],
        reverse=True
    )

    rankings = "\n".join([f"{i+1}# {name} ({result})" for i, (name, result) in enumerate(sorted_results)])

    embed = discord.Embed(
        title="📊 Summary of today!",
        color=discord.Color.gold()
    )
    embed.add_field(name="📅 Date", value=date_str, inline=False)
    embed.add_field(name="🕒 Start", value=start_str, inline=True)
    embed.add_field(name="🕓 Finish", value=finish_str, inline=True)
    embed.add_field(name="⏱️ Total time spent", value=total_duration, inline=False)
    embed.add_field(name="🏆 The winner of today is", value=rankings or "No one finished yet!", inline=False)

    await ctx.send(embed=embed)

    # Reset all data after summary
    start_data.clear()
    start_time = None
    finish_time = None

server_on()

# Run the bot
bot.run(os.getenv('TOKEN'))
