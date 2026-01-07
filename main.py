import os
import discord
from discord.ext import commands
from datetime import datetime
import pytz
import asyncio
from datetime import datetime, timedelta
import random
from myserver import server_on
from deep_translator import GoogleTranslator
from pykakasi import kakasi
import re


# Setup intents and bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Global data storage
last_world = None
start_data = {}
start_time = None
finish_time = None
special_mentions = {
    "21/02": 1267811966769041451, # tori
    "01/03": 1249685648789606462, # yuki
    "19/03": 1007576032762658888,  # Nutcha
    "23/03": 759408411132952587, #Ammy
    "17/08": 505280516266786819, #Mui
    "27/08": 1172547640840429690, # Julia
    "18/11": 1247535447576547382 # kemomimi
}

birthday_message = "🎉 Happy Birthday!!ヾ( ˃ᴗ˂ )◞ • *✰🎂🎈"

# ช่องส่งงานเขียน
WRITTING_CHANNEL_ID = 1361195575470719026  # 🔁 ใส่ Channel ID ของแชท writting

# 3 คนที่ต้องส่งงานทุกวัน (ใช้เป็น user id จริง)
WRITING_USERS = {
    "Yuki": 1249685648789606462,  # แทน y
}

# เก็บวันที่ล่าสุดที่แต่ละคน "ส่งงานแล้ว" (ต่อวัน)
last_submit_date = {}  # user_id -> datetime.date

#แปลภาษา

TR_CHANNEL_ID = 1312842359330963497  # 🔁 ใส่ Channel ID ปลายทางที่ให้บอทส่งข้อความ

# --- kakasi สำหรับ romaji ---
_kks = kakasi()
_kks.setMode("J", "a")
_kks.setMode("H", "a")
_kks.setMode("K", "a")
_kks.setMode("r", "Hepburn")
_kks.setMode("s", True)
_conv = _kks.getConverter()

def to_romaji(text: str) -> str:
    return _conv.do(text).title()

def is_japanese(text: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u4e00-\u9faf]", text))

def is_thai(text: str) -> bool:
    return bool(re.search(r"[\u0E00-\u0E7F]", text))



# /////////////////////////////////////////////////////////////////////////////////////////
# ส่งทุกวันเวลา เที่ยงคืน 10นาที ญี่ปุ่น

ANNIV_START_YEAR = 2024  # ปีเริ่มรู้จักกัน

async def anniversary_task():
    await bot.wait_until_ready()
    channel_id = 1312781504400588883  # ช่องที่ต้องการให้ส่งข้อความ
    channel = bot.get_channel(channel_id)

    while not bot.is_closed():
        now = datetime.now(pytz.timezone("Asia/Tokyo"))
        # ส่งตอน 00:48
        target = now.replace(hour=0, minute=48, second=0, microsecond=0)

        if now > target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        # เช็กเฉพาะวันที่ 26/11
        if target.month == 11 and target.day == 27 and target.year >= ANNIV_START_YEAR:
            years = target.year - ANNIV_START_YEAR
            await channel.send(
                f"Happy anniversary of the year we first met! It has been {years} years now ٩(ˊᗜˋ*)و ♡"
                f"I hope we’ll continue to receive this message together for many more years to come. (≧ヮ≦) 💕"
            )

async def scheduled_task():
    await bot.wait_until_ready()
    channel_id = 1312781504400588883  # 🔁 Channel ที่บอทจะส่งข้อความ
    channel = bot.get_channel(channel_id)

    while not bot.is_closed():
        now = datetime.now(pytz.timezone("Asia/Tokyo"))
        target = now.replace(hour=0, minute=10, second=0, microsecond=0)

        if now > target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        if channel:
            # รายวัน
            await channel.send("日本人 Are you 眠い？？ ᶻ 𝗓 𐰁")

            # วันพิเศษแบบเปลี่ยนคน แต่ข้อความเดิม
            today = target.strftime("%d/%m")
            if today in special_mentions:
                mention_id = special_mentions[today]
                mention_text = ""

                try:
                    user = await bot.fetch_user(mention_id)
                    mention_text = f"{user.mention} "
                except:
                    pass  # ไม่เจอ user ก็ไม่แท็ก

                await channel.send(f"{mention_text}{birthday_message}")


async def writing_reminder_task():
    await bot.wait_until_ready()
    channel = bot.get_channel(WRITTING_CHANNEL_ID)

    if channel is None:
        print("⚠️ ไม่เจอช่อง WRITTING_CHANNEL_ID ที่ตั้งไว้")
    
    while not bot.is_closed():
        now = datetime.now(pytz.timezone("Asia/Tokyo"))
        # ตั้งเวลาเช็กทุกวันตอน 23:55 (ปรับได้)
        target = now.replace(hour=23, minute=50, second=0, microsecond=0)

        if now > target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        # ดึง channel อีกรอบ กันกรณีบอทเพิ่ง join/เปลี่ยนแชนแนล
        channel = bot.get_channel(WRITTING_CHANNEL_ID)
        if channel is None:
            continue

        today = target.date()

        for key, user_id in WRITING_USERS.items():
            last_date = last_submit_date.get(user_id)

            member = channel.guild.get_member(user_id) or await bot.fetch_user(user_id)
            mention = member.mention if member else f"<@{user_id}>"

            # ยังไม่เคยมี record เลย → ถือว่าไม่ส่งวันนี้ แต่ยังไม่ด่าแรง ใช้ "ลืมส่งงานรึเปล่า"
            if last_date is None:
                await channel.send(f"{mention} Did you forget to do the writing? ∘ ∘ ∘ ( °ヮ° ) ?")
                continue

            days = (today - last_date).days

            if days <= 0:
                # ส่งงานแล้ววันนี้
                continue
            elif days == 1:
                # ขาด 1 วัน
                await channel.send(f"{mention} Did you forget to do the writing? ∘ ∘ ∘ ( °ヮ° ) ?")
            elif days >= 2:
                # ขาด 2 วันขึ้นไป → เมนชั่น + บอกจำนวนวัน
                member = channel.guild.get_member(user_id) or await bot.fetch_user(user_id)
                mention = member.mention if member else f"<@{user_id}>"
                await channel.send(f"{mention} ou haven't submitted your work for {days} days! Be careful and watch out! Don't you dare forget ! ( ◺˰◿ )")




# /////////////////////////////////////////////////////////////////////////////////////////
# แจ้งเตือนบอทออนไลน์ terminal

@bot.event
async def on_ready():
    print('Bot is online!! He ready to work now!')

    asyncio.create_task(scheduled_task())      # อันเดิม (00:10)
    asyncio.create_task(anniversary_task())    # 🎉 อันใหม่ (00:48 เฉพาะ 26/11)
    asyncio.create_task(writing_reminder_task())


    #channel_id = 1329786018353778760 # 🔁 ใส่ Channel ID ที่ต้องการให้บอทส่งข้อความ
    #channel = bot.get_channel(channel_id)
    #if channel:
    #    await channel.send("test")
    #asyncio.create_task(scheduled_task())



# /////////////////////////////////////////////////////////////////////////////////////////
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
    await ctx.send(f"Got {name.capitalize()}'s result! Let's see who the winner's gonna be! (¬ ₃ ͡¬)👊🏻")

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
async def help(ctx):
    hembed = discord.Embed(
        title="📚 How My Commands Work",
        description="Here's a quick guide to using my commands!",
        color=discord.Color.blue()
    )
    
    hembed.add_field(
        name="🛠️ `!start`",
        value="Enter your name and the number of crystals before mining.\n➔ Example: `!start name 0`",
        inline=False
    )
    hembed.add_field(
        name="⛏️ `!finish`",
        value="Enter your name and the number of crystals after mining.\n➔ Example: `!finish name 0`",
        inline=False
    )
    hembed.add_field(
        name="♻️ `!reset`",
        value="Reset input data.\n➔ Example: `!reset` (reset all users) | `!reset name` (reset specific user)",
        inline=False
    )
    hembed.add_field(
        name="📄 `!summary`",
        value="Enter the name of the world owner you mined with.\n➔ Example: `!summary name`",
        inline=False
    )
    hembed.add_field(
        name="📄 `!tr`",
        value="Enter the word you want to translate.\n➔ Example: `!tr rain`",
        inline=False
    )

    hembed.set_thumbnail(url="https://media.tenor.com/kYVuwpAqbfUAAAAM/genshin-impact-furina.gif")
    hembed.set_image(url="https://upload-os-bbs.hoyolab.com/upload/2024/01/07/304153211/babd6d552ea0572ae90483188c4f6a7e_8170120446407218376.gif")
    hembed.set_footer(text="Happy mining! 🚀")

    await ctx.send(embed=hembed)


@bot.command()
async def summary(ctx, name: str = None):
    global start_data, start_time, finish_time, last_world

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

    # กำหนดชื่อโลกใน title
    if name:
        last_world = f"{name}'s world"
    else:
        last_world = None

    title_suffix = f" ({last_world})" if last_world else ""
    embed = discord.Embed(
        title=f"📊 Summary of today!{title_suffix}",
        color=discord.Color.blue()
    )
    embed.add_field(name="📅 Date", value=date_str, inline=False)
    embed.add_field(name="🕒 Start", value=start_str, inline=True)
    embed.add_field(name="🕓 Finish", value=finish_str, inline=True)
    embed.add_field(name="⏱️ Total time spent", value=total_duration, inline=False)
    embed.add_field(name="🏆 The winner of today is", value=rankings or "No one finished yet!", inline=False)
    embed.set_thumbnail(url='https://upload-os-bbs.hoyolab.com/upload/2024/05/04/37093677/e141a50c00a93db971c6f3ea8452cd30_7882568107366365724.gif')
    embed.set_image(url="https://i.redd.it/give-me-your-best-genshin-memes-and-you-get-mine-v0-8opqa6xdc78e1.gif?width=749&auto=webp&s=346e147410646fd9b46adfb2be03d3bc0912ea8c")

    await ctx.send(embed=embed)

    # ล้างข้อมูลหลังสรุป
    start_data.clear()
    start_time = None
    finish_time = None

@bot.command()
async def tr(ctx, *, text: str):
    target_channel = bot.get_channel(TR_CHANNEL_ID)

    if target_channel is None:
        await ctx.send("⚠️ Translate channel not found.")
        return

    try:
        # 1) แปลเป็นญี่ปุ่นก่อนเสมอ
        jp = text if is_japanese(text) else GoogleTranslator(
            source="auto", target="ja"
        ).translate(text)

        # 2) ญี่ปุ่น → อังกฤษ
        en = GoogleTranslator(
            source="ja", target="en"
        ).translate(jp).lower()

        # 3) โรมาจิ
        romaji = to_romaji(jp)

        # 4) ถ้าต้นฉบับเป็นไทย ใส่ไทยต่อท้าย
        extra = f", {text}" if is_thai(text) and not is_japanese(text) else ""

        result = f"{jp} ({romaji}) = {en}{extra}"

        # ส่งไปช่องที่กำหนด
        await target_channel.send(result)

        # แจ้งคนที่ใช้คำสั่ง (ลบได้ถ้าไม่อยากให้เด้ง)
        await ctx.send("📘 Translation sent!")

    except Exception as e:
        await ctx.send("❌ Translate failed")



# /////////////////////////////////////////////////////////////////////////////////////////
# ตอบกลับข้อความตามคำที่มี

@bot.event
async def on_message(message):
    # เมสเสจจากบอท (รวมทั้งบอทอื่น) ไม่ต้องสนใจ
    if message.author.bot:
        return

    # ---- แก้จุดนี้: ถ้ามีคำสั่ง (ขึ้นต้นด้วย prefix) ให้ประมวลผลคำสั่งทั้งหมดแล้ว return ----
    lines = [l.strip() for l in message.content.split('\n') if l.strip()]
    has_command = any(l.startswith(bot.command_prefix) for l in lines)

    if has_command:
        # รองรับหลายคำสั่งในข้อความเดียว
        for line in lines:
            if line.startswith(bot.command_prefix):
                fake_message = message
                fake_message.content = line
                await bot.process_commands(fake_message)
        return
    # ------------------------------------------------------------------------------

        # 🔻🔻🔻 ส่วนใหม่: เช็กการส่งงานในแชท writting 🔻🔻🔻
    if message.channel.id == WRITTING_CHANNEL_ID and message.author.id in WRITING_USERS.values():
        # เช็กว่ามีรูปไหม
        has_image = False
        for att in message.attachments:
            # บางที content_type อาจเป็น None เลยเผื่อเช็คจากชื่อไฟล์ด้วย
            if (att.content_type and att.content_type.startswith("image/")) or \
               att.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                has_image = True
                break

        if has_image:
            now = datetime.now(pytz.timezone("Asia/Tokyo"))
            last_submit_date[message.author.id] = now.date()
            # จะ print log ไว้ดูก็ได้
            print(f"[WRITING] {message.author} ส่งงานวันที่ {now.date()}")


    if bot.user in message.mentions:
        responses = [
            ["I'm here you n..need s..s..some help???", "https://i.redd.it/39eepulscwje1.gif"],
            ["Did you say something bad to me,right?", "https://i.redd.it/5e800xfmyy3d1.gif"],
            ["Helloooo", "https://tenor.com/lVh7OkqdilZ.gif"],
            ["Nuh uh,I won't work for you.Do it yourself", "https://tenor.com/c9WirOAoErq.gif"],
            ["zzzzzzzzz.............y..Yes？", "https://tenor.com/fs8ctDp8LUA.gif"],
            ["Dude, why do you keep calling me WTH", "https://tenor.com/fdcKMmQ3URF.gif"],
            ["HAHAHAHA you so funny ...................I lie FAQ" , "https://tenor.com/jEOjEdt861v.gif"],
            ["OHHHH ok k k  I understand (Don't understand)" , "https://tenor.com/qaChJnWwI1F.gif"],
            ["Hiiii,Do you miss me??I'm fineദ്ദി(｡•̀ ,<)~✩‧₊" , "https://tenor.com/en-GB/view/robin-robin-hsr-boy-slow-down-hsr-honkai-star-rail-gif-14230868558252524096"],
            ["Hmm Lets me see..Σ(°ロ°) No Do not No Dont NOnononononoooo" , "https://tenor.com/en-GB/view/robin-hsr-honkai-star-rail-gif-3108716992720495010"],
            ["AHSDAHSHDJASJDKASKJDASHJA LET ME SLEEPPPPPP" , "https://tenor.com/npMvn9ISgjO.gif"]
        ]
        chosen = random.choice(responses)
        for line in chosen:
            await message.channel.send(line)
        return

    content = message.content.lower()

    # ✅ ตอบ hi เมื่อพิมพ์ hello
    if content == "hello":
        if not message.content.startswith('!'):
            await message.channel.send(f"Hello {message.author.mention} Ekae")
            return

    # ✅ ตอบ xxxx ถ้ามีคำว่า zzzzz หรือคำใกล้เคียง
    if any(keyword in content for keyword in ["good night", "おやすみ", "gn", "oyasumi", 'นอน', 'nemui', 'sleep', '眠い', 'ねむい']):
        if not message.content.startswith('!'):
            await message.channel.send(random.choice([f"sweet dreams~ 😴😴 {message.author.mention}"
                                                    ,"Good night (⸝⸝ᴗ﹏ᴗ⸝⸝) ᶻ 𝗓 𐰁"
                                                    ,"see you tomorrowwww"]))
        return
    
    if any(keyword in content for keyword in ["ohayou", "おはよう", "morning"]):
        if not message.content.startswith('!'):
            await message.channel.send(random.choice([f"Good morning (❁´◡`❁) 😃🌞 {message.author.mention}",
                                    f"Ohayouuuu 🌻☀️🐝"]))
        return
    
    if any(keyword in content for keyword in ["he is"]):
        if not message.content.startswith('!'):
            await message.channel.send(f"He is the fastest cashier I know 🏃🏻‍♂️🏃🏻‍♂️")
        return
    
    if any(keyword in content for keyword in ["love",'♡']):
        if not message.content.startswith('!'):
            await message.channel.send(random.choice([f"I love youuuuu (´▽`ʃ♡ƪ) {message.author.mention}",
                                                    f"I love you no matter what {message.author.mention} (ෆ˙ᵕ˙ෆ)♡",
                                                    f"I cherish you naa!! ₍ᐢ. .ᐢ₎ ₊˚⊹♡"]))
        return
    
    if any(keyword in content for keyword in ["crystie chu contente"]) :
        if not message.content.startswith('!'):
            await message.channel.send(random.choice([f"Are you calling me ?? (≧∀≦)ゞ\nCrystie Chu Contente, that's my name! ∘ ∘ ∘ ( °ヮ° ) ? {message.author.mention}",
                                    f"Yes! I'm here! You need help? ᕙ(  •̀ ᗜ •́  )ᕗ",
                                    f"The coolest Bot in this server is here!!\nLet me know if there's anything I can do. ᓚ₍ ^. .^₎"]))
        return
    
    if any(keyword in content for keyword in ["kak",'noob','heta','กาก']):
        if not message.content.startswith('!'):
            await message.channel.send(random.choice([f"No!! Mui kak trust me ദ്ദി(˵ •̀ ᴗ - ˵ ) ✧ \n Ammy tell me this",
                                                    f"Who noob !?!?!( ˶°ㅁ°) !!"]))
        return

    if any(keyword in content for keyword in ["are you all ,all right ?",'are u all right','are you all all right']):
        if not message.content.startswith('!'):
            await message.channel.send(f"No!! We are ALL ,ALL LEFT ദ്ദി(ᵔᗜᵔ)")
        return
    
    if any(keyword in content for keyword in ["today whos world","today who's world",'today who world']):
        if not message.content.startswith('!'):
            if last_world:
                await message.channel.send(f"🌍 Last time, it was {last_world} ✨")
            else:
                await message.channel.send("🤔 I don't know yet... maybe Havuika's world?? Σ(°△°   )")
        return

    if any(keyword in content for keyword in ["ekae"]):
        if not message.content.startswith('!'):
            user_ids = [1172547640840429690, #julia 1
                        663541892201578507, #julia 2
                        759408411132952587, #Ammy
                        1166748170823413791, #Achi
                        ]
            chosen_user = await bot.fetch_user(random.choice(user_ids))

            await message.channel.send(random.choice([
                f"WHAT THE HELL {message.author.mention}",
                f"No!!! I think {chosen_user.mention} is EKae"
            ]))
        return

    
    if any(keyword in content for keyword in ["waiting"]):
        if not message.content.startswith('!'):
            await message.channel.send(f"No need to hurry naa (˶ᵔ ᵕ ᵔ˶)")
        return

    if any(keyword in content for keyword in ["no need to hurry na"]) :
        if not message.content.startswith('!'):
            await message.channel.send("HUH!?!?!?This you just mock me!?!?!?! <(ꐦㅍ _ㅍ)>")
            await message.channel.send("https://tenor.com/o0WqN4GKaoN.gif")
        return

    # ✅ รองรับหลายคำสั่งในข้อความเดียว
    lines = message.content.strip().split('\n')
    for line in lines:
        if line.strip():
            fake_message = discord.Message  # สร้างข้อความใหม่
            fake_message = message
            fake_message.content = line.strip()
            await bot.process_commands(fake_message)

server_on()

# Run the bot
bot.run(os.getenv('TOKEN'))











