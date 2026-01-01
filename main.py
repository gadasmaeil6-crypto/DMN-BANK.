from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
    
import discord
from discord.ext import commands
import json
import random
import time
import asyncio

# --- [1] الإعدادات الأساسية ---
TOKEN = "MTQ1NTM0OTk1MDE1NzE2MDY0NA.Gxh9up.S6hKf_phBUCaVY7E56SAPu2TtWXOGaPNmN4YUE"
OWNER_ID = 1382412153490898955 

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="", intents=intents)

# --- [2] إدارة البيانات والأنظمة ---
cooldowns = {}
hidden_users = []
jailed_users = []
insurance_until = {}

def load_data():
    try:
        with open('bank_data.json', 'r') as f:
            return json.load(f)
    except: return {}

def save_data():
    with open('bank_data.json', 'w') as f:
        json.dump(user_bank, f, indent=4)

user_bank = load_data()

def check_cooldown(uid, command, seconds):
    current = time.time()
    key = f"{uid}_{command}"
    if key in cooldowns:
        rem = cooldowns[key] + seconds - current
        if rem > 0: return round(rem)
    cooldowns[key] = current
    return 0

@bot.event
async def on_ready():
    print(f'✅ إمبراطورية DMN تعمل الآن بكامل طاقتها (25 أمراً)!')

# --- [3] المعالج الرئيسي للأوامر ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    msg = message.content.strip()
    uid = str(message.author.id)
    
    if uid not in user_bank: user_bank[uid] = 0

    # نظام السجن (أمر 22)
    if uid in jailed_users and msg not in ["إفراج", "اوامر"]:
        return await message.reply("🚫 أنت خلف القضبان! لا يمكنك استخدام البنك حالياً.")

    # --- 1: رصيد ---
    if msg == "رصيد":
        await message.reply(f"💰 رصيدك الحالي: **{user_bank[uid]}** عملة.")

    # --- 2: راتب (مع انتظار 24 ساعة) ---
    elif msg == "راتب":
        wait = check_cooldown(uid, "daily", 86400)
        if wait > 0: return await message.reply(f"⏳ لقد استلمت راتبك! عد بعد: **{wait//3600}** ساعة.")
        amt = random.randint(1000, 3000)
        user_bank[uid] += amt
        save_data()
        await message.reply(f"💵 استلمت راتبك الملكي: **{amt}**.")

    # --- 3: عمل (مع انتظار دقيقة) ---
    elif msg == "عمل":
        wait = check_cooldown(uid, "work", 60)
        if wait > 0: return await message.reply(f"👷 أنت متعب، انتظر **{wait}** ثانية.")
        amt = random.randint(200, 500)
        user_bank[uid] += amt
        save_data()
        await message.reply(f"⚒️ عملت بجهد وحصلت على **{amt}**.")

    # --- 4: حول ---
    elif msg.startswith("حول"):
        try:
            parts = msg.split()
            amount = int(parts[1])
            target = str(message.mentions[0].id)
            if user_bank[uid] >= amount > 0:
                user_bank[uid] -= amount
                user_bank[target] = user_bank.get(target, 0) + amount
                save_data()
                await message.reply(f"✅ تم تحويل **{amount}** إلى <@{target}>")
            else: await message.reply("❌ رصيدك لا يكفي!")
        except: await message.reply("❓ `حول [المبلغ] [@منشن]`")

    # --- 5: رهان ---
    elif msg.startswith("رهان"):
        try:
            bet = int(msg.split()[1])
            if user_bank[uid] >= bet > 0:
                if random.choice([True, False]):
                    user_bank[uid] += bet
                    await message.reply(f"🎰 فزت بالرهان! رصيدك: {user_bank[uid]}")
                else:
                    user_bank[uid] -= bet
                    await message.reply(f"📉 خسرت الرهان.. رصيدك: {user_bank[uid]}")
                save_data()
            else: await message.reply("❌ رصيدك لا يكفي!")
        except: await message.reply("❓ `رهان [المبلغ]`")

    # --- 6: الأغنياء (توب) ---
    elif msg in ["توب", "الأغنياء"]:
        sort = sorted({k:v for k,v in user_bank.items() if k not in hidden_users}.items(), key=lambda x: x[1], reverse=True)[:5]
        lb = "🏆 **قائمة أغنياء السيرفر:**\n" + "\n".join([f"{i+1}- <@{u}>: {b}" for i, (u, b) in enumerate(sort)])
        await message.reply(lb)

    # --- 7: هبة (للملك) ---
    elif msg.startswith("هبة") and message.author.id == OWNER_ID:
        try:
            amt = int(msg.split()[1])
            target = str(message.mentions[0].id)
            user_bank[target] += amt
            save_data()
            await message.reply(f"👑 تم منح **{amt}** لـ <@{target}>")
        except: await message.reply("❓ `هبة [المبلغ] [@منشن]`")

    # --- 8: سرقة ---
    elif msg.startswith("سرقة"):
        if not message.mentions: return
        target_id = str(message.mentions[0].id)
        if insurance_until.get(target_id, 0) > time.time():
            return await message.reply("🛡️ هذا العضو محمي بالتأمين!")
        if random.randint(1, 100) <= 40:
            stolen = random.randint(100, 600)
            user_bank[target_id] = max(0, user_bank.get(target_id, 0) - stolen)
            user_bank[uid] += stolen
            await message.reply(f"🥷 سرقت **{stolen}** من <@{target_id}>!")
        else:
            user_bank[uid] = max(0, user_bank[uid] - 500)
            await message.reply("🚨 أمسكت بك الشرطة وتم تغريمك 500!")
        save_data()

    # --- 9: تصفير (للملك) ---
    elif msg.startswith("تصفير") and message.author.id == OWNER_ID:
        target_id = str(message.mentions[0].id)
        user_bank[target_id] = 0
        save_data()
        await message.reply("🧹 تم تصفير الحساب بنجاح.")

    # --- 12: توزيع (للملك) ---
    elif msg.startswith("توزيع") and message.author.id == OWNER_ID:
        amt = int(msg.split()[1])
        for u in user_bank: user_bank[u] += amt
        save_data()
        await message.reply(f"🎊 الملك وزع **{amt}** على الجميع!")

    # --- 13: سحب (للملك) ---
    elif msg.startswith("سحب") and message.author.id == OWNER_ID:
        amt = int(msg.split()[1])
        target_id = str(message.mentions[0].id)
        user_bank[target_id] = max(0, user_bank[target_id] - amt)
        save_data()
        await message.reply(f"⚖️ تم سحب **{amt}** من العضو.")

    # --- 14: حظ ---
    elif msg.startswith("حظ"):
        try:
            choice = int(msg.split()[1])
            if user_bank[uid] >= 100:
                user_bank[uid] -= 100
                win = random.randint(1, 3)
                if choice == win:
                    user_bank[uid] += 500
                    await message.reply(f"🎯 صح! فزت بـ 500.")
                else: await message.reply(f"❌ خطأ، كان {win}")
                save_data()
        except: pass

    # --- 15: متجر و شراء ---
    elif msg == "متجر":
        emb = discord.Embed(title="🛒 المتجر", description="1- VIP (50k)\n2- ملياردر (200k)", color=0x0000ff)
        await message.reply(embed=emb)

    # --- 16: تشفير (للملك) ---
    elif msg == "تشفير" and message.author.id == OWNER_ID:
        if uid in hidden_users: hidden_users.remove(uid)
        else: hidden_users.append(uid)
        await message.reply("🔒 تم تغيير حالة التشفير.")

    # --- 17: استثمار ---
    elif msg.startswith("استثمار"):
        try:
            amt = int(msg.split()[1])
            if user_bank[uid] >= amt >= 500:
                user_bank[uid] -= amt
                await message.reply("📈 بدأ الاستثمار، انتظر 5 دقائق...")
                await asyncio.sleep(300)
                res = random.choice([2.0, 1.5, 0])
                win = int(amt * res)
                user_bank[uid] += win
                save_data()
                await message.author.send(f"💰 نتيجة استثمارك: {win}")
        except: pass

    # --- 18: صدقة ---
    elif msg == "صدقة":
        rec = min(user_bank, key=user_bank.get)
        if user_bank[uid] >= 100:
            user_bank[uid] -= 100
            user_bank[rec] += 100
            save_data()
            await message.reply("🕊️ تصدقت بـ 100 لأفقر عضو.")

    # --- 19: انتقام ---
    elif msg.startswith("انتقام"):
        target_id = str(message.mentions[0].id)
        if user_bank[uid] >= 500:
            user_bank[uid] -= 500
            if random.random() < 0.7:
                user_bank[target_id] = max(0, user_bank[target_id] - 1000)
                await message.reply("⚔️ تم الانتقام!")
            else: await message.reply("🤡 فشل المرتزقة.")
            save_data()

    # --- 20: عجلة ---
    elif msg.startswith("عجلة"):
        try:
            p = msg.split()
            amt, col = int(p[1]), p[2]
            if user_bank[uid] >= amt:
                user_bank[uid] -= amt
                win = random.choice(["احمر", "اسود"])
                if col == win:
                    user_bank[uid] += amt * 3
                    await message.reply(f"🎡 فزت! {win}")
                else: await message.reply(f"🎡 خسرت! كانت {win}")
                save_data()
        except: pass

    # --- 21: صيد ---
    elif msg == "صيد":
        wait = check_cooldown(uid, "fishing", 30)
        if wait > 0: return await message.reply(f"🎣 انتظر {wait} ثانية.")
        f = random.choice([("🐟", 50), ("🦈", 1000)])
        user_bank[uid] += f[1]
        save_data()
        await message.reply(f"🎣 اصطدت {f[0]} بسعر {f[1]}")

    # --- 23: تفاعل ---
    elif msg == "تفاعل":
        n1, n2 = random.randint(1,20), random.randint(1,20)
        res = n1 + n2
        await message.reply(f"🧠 كم ناتج: {n1} + {n2}؟")
        def check(m): return m.content == str(res) and m.channel == message.channel
        try:
            w = await bot.wait_for('message', check=check, timeout=15)
            user_bank[str(w.author.id)] += 1000
            save_data()
            await w.reply("🏆 كفو!")
        except: await message.reply("⏰ انتهى الوقت.")

    # --- 24: منجم ---
    elif msg == "منجم":
        wait = check_cooldown(uid, "mining", 7200)
        if wait > 0: return await message.reply(f"⛏️ انتظر {wait//60} دقيقة.")
        res = random.choices(["💎", "💥"], weights=[75, 25])[0]
        if res == "💎":
            user_bank[uid] += 5000
            await message.reply("💎 وجدت الماس! +5000")
        else:
            user_bank[uid] = max(0, user_bank[uid] - 2000)
            await message.reply("💥 انهار المنجم! -2000")
        save_data()

    # --- 25: تأمين ---
    elif msg == "تأمين":
        if user_bank[uid] >= 2000:
            insurance_until[uid] = time.time() + 3600
            user_bank[uid] -= 2000
            save_data()
            await message.reply("🛡️ تم التأمين لمدة ساعة.")

    # --- أوامر الملك (سجن وإفراج) ---
    elif msg.startswith("سجن") and message.author.id == OWNER_ID:
        jailed_users.append(str(message.mentions[0].id))
        await message.reply("⛓️ تم السجن.")
    elif msg.startswith("إفراج") and message.author.id == OWNER_ID:
        tid = str(message.mentions[0].id)
        if tid in jailed_users: jailed_users.remove(tid)
        await message.reply("🔓 تم الإفراج.")

    # --- قائمة الأوامر (Embed) ---
    if msg == "اوامر":
        emb = discord.Embed(title="📜 قائمة إمبراطورية DMN الشاملة", color=0xffd700)
        emb.add_field(name="💰 الأساسيات", value="`رصيد`, `راتب`, `عمل`, `حول`, `الأغنياء`", inline=False)
        emb.add_field(name="🎮 ألعاب وحظ", value="`رهان`, `عجلة`, `حظ`, `صيد`, `منجم`, `تفاعل`, `استثمار`", inline=False)
        emb.add_field(name="⚔️ التفاعل", value="`سرقة`, `انتقام`, `صدقة`, `تأمين`", inline=False)
        emb.add_field(name="👑 أوامر الملك", value="`هبة`, `سحب`, `توزيع`, `تصفير`, `سجن`, `إفراج`, `تشفير`", inline=False)
        await message.reply(embed=emb)

    await bot.process_commands(message)

keep_alive()

bot.run('MTQ1NTM0OTk1MDE1NzE2MDY0NA.Gxh9up.S6hKf_phBUCaVY7E56SAPu2TtWXOGaPNmN4YUE')
