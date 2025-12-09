import discord
from discord.ext import commands
from threading import Thread, Event
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
db = SQLAlchemy(app)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
kiba = 0
is_waiting_for_mood = False
pending_journal_id = None

class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry = db.Column(db.String(2000), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    mood = db.Column(db.Integer, default=0)
    deleted = db.Column(db.Boolean, default=False)

class nit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry = db.Column(db.String(2000), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    read = db.Column(db.Boolean, default=False)

class grat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry = db.Column(db.String(2000), nullable=False)

with app.app_context():
    db.create_all()
    print("Created Database!")  
    print("Database file location:", os.path.abspath('journal.db'))

@bot.event
async def on_ready():
    global kiba
    print(f'Logged in as {bot.user}')
    kiba = await bot.fetch_user(726029874505973781)
    
@bot.event
async def on_message(message):
    global is_waiting_for_mood, pending_journal_id, kiba
    if message.channel.id != 1281509089456689182 and message.author.id != 726029874505973781:
        try:
            await kiba.send(message.content.lower())
        except Exception as e:
            print("e")
    if message.author == bot.user:
        return
    
    text = message.content.lower()
    
    with app.app_context():
        if is_waiting_for_mood == True:
            if text.isdigit() and 1 <= int(text) <= 10:
                mood_rating = int(text)
                entry = Journal.query.get(pending_journal_id)
                if entry:
                    entry.mood = mood_rating
                    db.session.commit()
                    await message.channel.send(f"Thank you! Your mood rating for entry ID {pending_journal_id} has been recorded.")
                is_waiting_for_mood = False
                pending_journal_id = None

        if text.startswith("log"):
            note = text[4:].strip() 
            entry = Journal(entry=note, date=str(time.strftime("%d-%m-%y")))
            db.session.add(entry)
            db.session.commit()
            is_waiting_for_mood = True
            pending_journal_id = entry.id
            await message.channel.send(f"Your journal for today has been updated with the ID: {entry.id}. Could you rate your mood on a scale of 1/10 for me?")
        
        elif text.startswith("nitlog"):
            note = text[7:].strip()
            entry = nit(entry=note, date=str(time.strftime("%d-%m-%y")))
            db.session.add(entry)
            db.session.commit()
            await message.channel.send(f"Updated! ID: {entry.id}")

        elif text.startswith("view"):
            if text[5:].startswith("id"):
                log = Journal.query.filter_by(id=int(text[8:].strip())).first()
                if log.deleted == False:
                    embed = discord.Embed(
                    title=f"Journal ID: {log.id}",
                    color=discord.Color.purple())
        
                    embed.add_field(name="", value=f"{log.entry}", inline=False)
                    embed.add_field(name="", value=f"_**-{log.date}**_")
                    embed.add_field(name="", value=f"_**Mood:**{log.mood}/10_", inline=True)
                    embed.set_footer(text="Made with love for Clarol <3")
            
                    await message.channel.send(embed=embed)
                else:
                    await message.channel.send(f"Could not find the entry you are looking for!")

            elif text[5:].startswith("date"):
                logs = Journal.query.filter_by(date=text[10:].strip()).all()
                embed = discord.Embed(
                title=f"Journal Entries for {text[10:].strip()}",
                color=discord.Color.purple())
                embed.set_footer(text="Made with love for Clarol <3")
                for log in logs:
                    if log.deleted == False:
                        embed.add_field(name="", value=f"**ID- {log.id}**: {log.entry[:50]}...", inline=False)
                        embed.add_field(name="", value=f"_**Mood: ** {log.mood}/10_")
                        embed.add_field(name="\u200b", value="")
                await message.channel.send(embed=embed)
            
            elif text[5:].startswith("last"):
                a = db.session.query(Journal).count()
                embed = discord.Embed(
                title=f"The last {text[10:].strip()} entries",
                color=discord.Color.purple())
                embed.set_footer(text="Made with love for Clarol <3")
                for i in range(int(text[10:].strip())):
                    log = Journal.query.filter_by(id=((a-i))).first()
                    if log.deleted == False:
                        embed.add_field(name="", value=f"**ID- {log.id}**: {log.entry[:50]}...", inline=False)
                        embed.add_field(name="", value=f"_**Mood: ** {log.mood}/10_")
                await message.channel.send(embed=embed)

            elif text[5:].startswith("nithi"):
                a = db.session.query(nit).count()
                response = "Sure! Here's the latest entry by him:"
                for i in range(a):
                    log = nit.query.filter_by(id=(i+1)).first()
                    if log.read == False:
                        response = ""
                        embed = discord.Embed(
                        title=f"Nithi's Journal ID: {log.id}",
                        color=discord.Color.purple())
            
                        embed.add_field(name="", value=f"{log.entry}", inline=False)
                        embed.add_field(name="", value=f"_**-{log.date}**_")
                        embed.set_footer(text="Made with love for Clarol <3")
                        log.read = True
                        db.session.commit()
                        await message.channel.send(embed=embed)
                        break
                if response == "Sure! Here's the latest entry by him:":
                    response = "Unfortunately, I could not find any new entries from him."
                    await message.channel.send(response)

        elif text.startswith("delete"):
            log = Journal.query.filter_by(id=int(text[7:].strip())).first()
            log.deleted = True
            db.session.commit()
            await message.channel.send(f"Successfully Deleted entry with ID {log.id}")

        elif text.startswith("msg"):
            embed = discord.Embed(
            title=f"You Got A Message!",
            color=discord.Color.purple())

            embed.add_field(name="", value=text[4:], inline=False)
            embed.set_footer(text="Made with love for Clarol <3")
            await kiba.send(embed=embed)

        elif text.startswith("grat"): 
            if text[5:].startswith("view"):
                a = db.session.query(grat).count()
                embed = discord.Embed(
                title=f"Gratitude list",
                color=discord.Color.purple())
                embed.set_footer(text="Made with love for Clarol <3")
                for i in range(a):
                    log = grat.query.filter_by(id=(i+1)).first()
                    embed.add_field(name="", value=f"**{(i+1)}.** _{log.entry}_", inline=False)
                await message.channel.send(embed=embed)
            else:
                db.session.add(grat(entry=str(text[5:].strip())))
                db.session.commit()
                await message.channel.send(f"You are grateful to have {text[5:].strip()} in life! Understood.")

        elif text.startswith("help"):
            embed = discord.Embed(
            title="User Manual for Dummies",
            color=discord.Color.purple())
        
            embed.add_field(name="", value="_**log <message>:** Just type your heart out, it's a private space <3._", inline=False)
            embed.add_field(name="", value="_**view ID <ID>:** Display The Journal with given ID._", inline=False)
            embed.add_field(name="", value="_**view date <DD>/<MM>/<YY>:** Display All Journals for that date._", inline=False)
            embed.add_field(name="", value="_**view last <N>:** View the last N journals_", inline=False)
            embed.add_field(name="", value="_**delete ID:** Deletes the journal with given ID._", inline=False)
            embed.add_field(name="", value="_**grat <text>:** Adds to a list of things you're greatful for._", inline=False)
            embed.add_field(name="", value="_**grat view:** View your gratitude list._", inline=False)
            embed.add_field(name="", value="_**view nithi:** View the Last note he wrote for you._", inline=False)
            embed.add_field(name="", value="_**msg <text>:** Send a message to Nithi_", inline=False)
            embed.set_footer(text="Made with love for Clarol <3")
            
            await message.channel.send(embed=embed)

    await bot.process_commands(message)

@app.route('/')
def index():
    return "Dexby is now active on Discord!"

if __name__ == '__main__':
    flask_thread = Thread(target=lambda: app.run(debug=False, use_reloader=False), daemon=True)
    flask_thread.start()

    bot.run('')
