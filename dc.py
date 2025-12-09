from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
from flask import Flask, render_template, redirect, request, flash
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from discord.ext import tasks
from threading import Thread
from os import path
import requests
import datetime
import discord
import json

client = discord.Client(intents=discord.Intents.default(), activity=discord.Game(name="Yes im awake"))
app = Flask(__name__)
used_kiba_pics = []
first_start = True
website_domain = "huh"
test_date = datetime.datetime.today()
old_date = datetime.datetime.today().date()
app.secret_key = "jkbiy(*^Thb86T87hvcer86"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///users.db'
db = SQLAlchemy(app)
lg = LoginManager()
lg.login_view = "login"
lg.init_app(app=app)


@client.event
async def on_ready():
    print("we have logged in as {0.user}".format(client))
    a = await client.fetch_user(726029874505973781)
    await a.send("YOOO IM UP ENTER MY URL")
    reset_func.start()
    reminder.start()

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    dc_acc = db.Column(db.Integer)
    verified = db.Column(db.Boolean)

class diary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person = db.Column(db.String)
    dc_id = db.Column(db.Integer)
    date = db.Column(db.Date)
    shared = db.Column(db.String)
    content = db.Column(db.String)

class user_settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person = db.Column(db.String)
    dc_id = db.Column(db.Integer)
    quotes_api = db.Column(db.String)
    shared = db.Column(db.String)
    share_ask = db.Column(db.Boolean)
    reminder = db.Column(db.Boolean)
    today_count = db.Column(db.Boolean)

def create_database(app):
    if not path.exists("/users.db"):
        db.create_all(app=app)
        print("Created Database!") 

def date_now():
    return datetime.datetime.today()

def get_random_quote():
	try:
		response = requests.get("https://zenquotes.io/api/random")
		if response.status_code == 200:
			data = response.json()

			return f"{data[0]['q']}      -{data[0]['a']}"
		else:
			return f"Error while getting quote, response_code={response.status_code}"
	except Exception as e:
		return f"Something went wrong! Try Again! {e}"

def date_range_list(start_date, end_date):
    date_list = []
    curr_date = start_date
    while curr_date <= end_date:
        date_list.append(datetime.datetime.strptime(datetime.datetime.strftime(curr_date, "%x"), "%x").date())
        curr_date += timedelta(days=1)
    return date_list

@lg.user_loader
def load_user(id):
    return Users.query.get(int(id))

@tasks.loop(seconds=86400)
async def reminder():
    global first_start
    if first_start != True:
        row = user_settings.query.all()
        for i in row:
            if i.reminder == True:
                if i.today_count != True:
                    user_to_send = await client.fetch_user(i.dc_id)
                    await user_to_send.send("Heya how are you doing, Dont forget to update your diary today :p")
                    i.today_count = True
                else:
                    pass
        db.session.commit()
    else:
        first_start = False

@tasks.loop(seconds=2400)
async def reset_func():
    global old_date
    if old_date == date_now().date():
        pass
    else:
        row = user_settings.query.all()
        for i in row:
            i.today_count = False
        old_date = date_now().date()
        db.session.commit()

@client.event
async def on_message(message):
    try:
        global today_count
        username = str(message.author)
        channel = int(message.channel.id)
        print(f"{username} in channel {channel}: {message.content}")
        user_message = str(message.content).lower().split()
        lst = []
        tempvar = True
        if message.author == client.user:
            return
        elif message.channel.id != client.user:
            if str(message.channel.type) == "private":
                query = user_settings.query.filter_by(person=username).first()
                if query == None:
                    new_user = user_settings(person=username, dc_id = message.author.id, share_ask = False, reminder = False)
                    db.session.add(new_user)
                    db.session.commit()
                    if user_message[0] != "-help" or user_message[0] != "-log":
                        await message.channel.send("I see you're a new user to this bot, Welcome! Please run -help to see the commands i have :)")
                    else:
                        await message.channel.send("Also, your account is now registered to have its own unique diary :D")
                    query = user_settings.query.filter_by(person=username).first()
                if user_message[0] == "-log":
                    if user_message[1]== "today":
                        query.today_count = True
                        if query.share_ask == True:
                            while tempvar == True:
                                await message.channel.send(f'Alright! i added your diary for today, Would you like to share this with someone? (yes/no)')
                                shares = await client.wait_for("message")
                                shares = shares.content.split()
                                if shares[0] == "no":
                                    new_entry = diary(person=username, dc_id=message.author.id, date=date_now(), content=" ".join(user_message[2:]))
                                    db.session.add(new_entry)
                                    db.session.commit()
                                    await message.channel.send("Gotcha! not sharing this with anyone")
                                    tempvar = False
                                elif shares[0] == "yes":
                                    await message.channel.send
                                    users_to_send = await client.wait_for("message")
                                    new_entry = diary(person=username, dc_id=message.author.id, date=date_now(),shared=users_to_send.content, content=" ".join(user_message[2:]))
                                    db.session.add(new_entry)
                                    db.session.commit()
                                    await message.channel.send(f"{users_to_send.content} Can now see this entry! im glad you decided to let others know how you feel :)")
                                    tempvar = False
                                else:
                                    await message.channel.send("Thats not a valid response! Please try again")
                        elif query.share_ask == False:
                            new_entry = diary(person=username, dc_id=message.author.id, date=date_now(), content=" ".join(user_message[2:]))
                            db.session.add(new_entry)
                            db.session.commit()
                            await message.channel.send(f"Alright! i added your diary for today\n heres a random quote to make your day better >:) \"{get_random_quote()}\"")

                    if user_message[1]== "edit":
                        print_date = "non"
                        if user_message[2]=="yesterday":
                            date_edit = date_now() - timedelta(days=1)
                            print_date = "yesterday"
                        elif user_message[2]=="today":
                            date_edit = date_now()
                            print_date = "today"
                        if "/" in user_message[2]:
                            try:
                                date_edit = datetime.date(year=int(message.content[16:20]), month=int(message.content[13:15]), day=int(message.content[10:12]))
                                print_date = datetime.datetime.strftime(date_edit, "%x")
                            except IndexError:
                                await message.channel.send('Please use the format "-log edit <DD>/<MM>/<YYYY>" or today/yesterday example:\n``-log edit today``\n``-log edit yesterday``\n``-log edit 23/08/2022``')
                                return

                        if print_date != "non":
                            row = diary.query.filter_by(date=date_edit, person=username).all()
                            if len(row) > 1:
                                for i in range(len(row)):
                                    if len(row[i].content) > 35:
                                        lst.append(f"{i+1}- {row[i].content[:35]}.....")
                                    else:
                                        lst.append(f"{i+1}- {row[i].content}")
                                await message.channel.send(f"There are more than one entries for this day, which one would you like to edit?")
                                for i in lst:
                                    await message.channel.send(i)
                                id_to_choose = await client.wait_for("message")
                                if len(row[int(id_to_choose.content)-1].content) > 20:
                                    await message.channel.send(f"Alright, editing \"{row[int(id_to_choose.content)-1].content[:20]}\"....., Send your new entry!")
                                else:
                                    await message.channel.send(f"Alright, editing {print_date}'s record, Send your new entry!")
                                new_msg = await client.wait_for("message")
                                row[int(id_to_choose.content)-1].content = new_msg.content
                                db.session.commit()
                                await message.channel.send(f"Done!. just sayin, dont have to edit anything, just be true to your feelings, noones here to jurdge you anyways :), this is a safe space <3")
                            else:
                                if len(row[0].content) > 20:
                                    await message.channel.send(f"Alright, editing \"{row[0].content[:20]}\"....., Send your new entry!")
                                else:
                                    await message.channel.send(f"Alright, editing {print_date}'s record, Send your new entry!")
                                new_msg = await client.wait_for("message")
                                row[0].content = new_msg.content
                                db.session.commit()
                                await message.channel.send(f"Done!. just sayin, dont have to edit anything, just be true to your feelings, noones here to jurdge you anyways :), this is a safe space <3")
                        else:
                            print(print_date)
                            print(str(user_message[2]))
                            await message.channel.send("Please use the format <DD>/<MM>/<YY> or today/yesterday example:\n``-log edit today`` \n``-log edit yesterday`` \n``-log edit 23/08/2022``")

                    if user_message[1] == "view":
                        if user_message[2] == "today":
                            date_view = date_now()
                        elif user_message[2] == "yesterday":
                            date_view = date_now() - timedelta(days=1)
                        elif "/" in user_message[2]:
                            try:
                                date_view = datetime.date(year=int(message.content[16:20]), month=int(message.content[13:15]), day=int(message.content[10:12]))
                            except IndexError:
                                await message.channel.send('Please use the format "-log view <DD>/<MM>/<YYYY>" or today/yesterday example:\n``-log view today``\n``-log view yesterday``\n``-log view 23/08/2022``')
                                return 
                        else:
                            await message.channel.send('Please use the format "-log view <DD>/<MM>/<YYYY>" or today/yesterday example:\n``-log view today``\n``-log view yesterday``\n``-log view 23/08/2022``')
                            return
                        row = diary.query.filter_by(date=date_view, person=username).all()
                        if len(row) > 1:
                            for i in range(len(row)):
                                if len(row[i].content) > 35:
                                    lst.append(f"{i+1}- {row[i].content[:35]}.....")
                                else:
                                    lst.append(f"{i+1}- {row[i].content}")
                            await message.channel.send("I found multiple records, choose one!")
                            for i in lst:
                                await message.channel.send(i)
                            id_to_choose = await client.wait_for("message")
                            await message.channel.send(f"{datetime.datetime.strftime(row[int(id_to_choose.content)-1].date, '%x')}- \"{row[int(id_to_choose.content)-1].content}\"")
                        elif len(row) <= 1:
                            try:
                                await message.channel.send(f"{datetime.datetime.strftime(date_view, '%x')}- \"{row[0].content}\"")
                            except IndexError:
                                await message.channel.send("There were no entries found for this day!")

                if user_message[0] == "-msg":
                    if user_message[1] == "kiba":
                        user_to_msg = await client.fetch_user(726029874505973781)
                        await user_to_msg.send(f'{user_to_msg}: {" ".join(user_message[2:])}')
                        await message.channel.send("Sent Your message to Kiba! (u could have literally just dm'ed me directly but ok-)")
                    elif user_message[1] != "kiba":
                        try:
                            user_to_msg = await client.fetch_user(int(user_message[1]))
                            await user_to_msg.send(" ".join(user_message[2:]))
                            await message.channel.send(f"Sent Your message to {user_to_msg}!")
                        except ValueError:
                            await message.channel.send('Please use the format "-msg <member_id> <message>" example:\n``-msg 726029874505973781 hi this is a message im sending you``')
                            return

                if user_message[0] == "-announce":
                    if username == "Kiba#6644":
                        ct=0
                        row = user_settings.query.all()
                        await message.channel.send("alright dude announcing, send the heading")
                        embed_title = await client.wait_for("message")
                        await message.channel.send("ok, send content now")
                        embed_content = await client.wait_for("message")
                        embed = discord.Embed(
                        title = embed_title.content,
                        description = embed_content.content,
                        colour = discord.Color.from_rgb(166, 82, 187),
                        )
                        embed.set_footer(text="Made with love for Sylvester and the Discord Community <3")
                        await message.channel.send("thats right?", embed=embed)
                        confirm = await client.wait_for("message")
                        if confirm.content == "yes":
                            for i in row:
                                try:
                                    user = await client.fetch_user(int(i.dc_id))
                                    await user.send(embed=embed)
                                    ct = ct +1
                                except Exception as E:
                                    await message.channel.send(f"Could not send {i.person}, {E}")
                            await message.channel.send(f"sent this announcement to {ct} people! Peace")
                        elif confirm.content == "no":
                            await message.channel.send(f"ok just run this command again im lazy to code an system to ask u for new message")
                        else:
                            await message.channel.send("valid response where")

                if user_message[0] == "-userbase":
                    if username == "Kiba#6644":
                        row = user_settings.query.count()
                        await message.channel.send(str(row))

                if user_message[0] == "-notesmade":
                    if username == "Kiba#6644":
                        row = diary.query.count()
                        await message.channel.send(str(row))

                if user_message[0] == "-url":
                    if username == "Kiba#6644":
                        global website_domain
                        website_domain = user_message[1]
                        await message.channel.send("OKAY MR KIBA THE NEW URL IS NOW UP")

                if "quote" in message.content:
                    await message.channel.send(f"Heres a quote for ya! \n {get_random_quote()}")

                if user_message[0] == "-help":
                    embed = discord.Embed(
                    title = "User Manual for Dummies",
                    description = "***-log today <message>: **Just type your heart out, its a private space UwU*\n\n***-log edit <DD>/<MM>/<YYYY>: **Edit Any of your 'diary' message*\n\n***-log view <DD>/<MM>/<YYYY>: **Display the text you stored for that specific day*\n\n***-msg kiba/<member_id> <message>: **Sends me/the member you mentioned a message via the bot(me- the person who made this bot)*\n\n***quotes: **A random quote to make your day better*\n\n***-config help: **displays help menu of the config command*\n\n***-website: **displays the website url and tells you about the website*",
                    colour = discord.Color.from_rgb(166, 82, 187),
                    )
                    embed.set_footer(text="Made with love for Sylvester and the Discord Community <3")
                    await message.channel.send(embed=embed)

                if user_message[0] == "-verify":
                    user = Users.query.filter_by(username=user_message[1]).first()
                    if user == None:
                        await message.channel.send("This account dosent exist on the website!")
                    elif user.dc_acc == 1:
                        user.dc_acc = message.author.id
                        db.session.commit()
                        await message.channel.send("Linked Successfully! you can now read your entries via the website")
                    else:
                        await message.channel.send("This account is already linked!")

                if user_message[0] == "-website":
                    embed = discord.Embed(
                        title = "Website Manual for Dummies",
                        description = f"***What it actually is: **its basically a place where you can view all your diaries written between 2 dates :D (yes you can set the dates between which you wanna view)*\n\n***URL:** {website_domain}*\n\n***The hosting thing im using is kinda weird so please let me know if the website is down and ill make sure to update it with the new url :)***",
                        colour = discord.Color.from_rgb(166, 82, 187)
                    )
                    embed.set_footer(text="Made with love for Sylvester and the Discord Community <3")
                    await message.channel.send(embed=embed)

                if user_message[0] == "-config":
                    if user_message[1] == "help":
                        embed = discord.Embed(
                            title = "Config Manual for Dummies",
                            description = "***-config help: **you know what this does dude*\n\n***-config reminder <on/off>: **turns on or off the reminder to update your diary*",
                            colour = discord.Color.from_rgb(166, 82, 187),
                        )
                        embed.set_footer(text="Made with love for Sylvester and the Discord Community <3")
                        await message.channel.send(embed=embed)
                    elif user_message[1] == "reminder":
                        if user_message[2] == "on":
                            query.reminder = True
                            await message.channel.send("you will now get notifs from this bot every 24h to update your diary :>")
                        elif user_message[2] == "off":
                            query.reminder = False
                            await message.channel.send("no more annoying notifs")
                    else:
                        await message.channel.send("That command dosent exist-")
                    db.session.commit()
                            
        db.session.commit()
    except Exception as e:
        await message.channel.send(f"Error: {e}")

#------------------------------------------------------FLASK---------------------------------------------------------

@app.route("/login", methods=["POST", "GET"])
def login():
    try:
        user = Users.query.filter_by(id=current_user.id).first()
        flash("your already logged in, where brains?", category='error')
        return render_template("home.html")
    except AttributeError:
        if request.method == 'POST':
            email = request.form.get("email").lower()
            password = request.form.get("password")
                
            user = Users.query.filter_by(email=email).first()
            if user:
                if user.password == password:
                    flash('Heya! logged in yay', category='success')
                    login_user(user, remember=True)
                    return render_template('home.html')
                else:
                    flash('cant even type a simple password right smh', category='error')
            else:
                flash('BRO?? that email dosent exist', category='error')

        return render_template("login.html")

@app.route('/register', methods=["POST", "GET"])
def register():
        if request.method == 'POST':
            username = request.form.get("username").lower()
            email = request.form.get("email").lower()
            password = request.form.get("password")
            password1 = request.form.get("password1")
            email_exists = Users.query.filter_by(email=email).first()
            username_exists = Users.query.filter_by(username=username).first()
            if email_exists:
                flash('someone made an acc with ur email ;-;', category='error')
            elif username_exists:
                flash('hippity hoppity ur username is my property(try a diff username)', category='error')
            elif password1 != password:
                flash('you couldnt enter the password right 2 times???(pass 1 dosent match pass2)', category='error')
            else:
                new_user = Users(email=email, 
                                username=username, 
                                password=password,
                                dc_acc=1)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Registered successfully! to activate your account, send "-verify <your username> to the bot!', category='success')
                return redirect("/home")

        return render_template("register.html")

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', category='success')
    return render_template("home.html")

@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/view-data/<start_date>/<end_date>')
@login_required
def data(start_date, end_date):
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    data_to_send = {}
    dates_to_check = date_range_list(start_date, end_date)
    if current_user.dc_acc == 1:
        return {}
    else:
        row = diary.query.filter_by(dc_id=current_user.dc_acc).all()
        print(row)
        for i in range(len(row)):
            if row[i].date in dates_to_check:
                data_to_send[f"{str(row[i].date)} -({i+1})"] = str(row[i].content)

        data_to_send = json.dumps(data_to_send)
        data_to_send = json.loads(data_to_send)
        return data_to_send

@app.route('/view-data/')
@login_required
def view_page():
    if current_user.dc_acc == 1:
        flash("Please link your account with your discord account to use this!", category="error")
        return render_template("view.html")
    else:
        return render_template("view.html")

create_database(app=app)

def flask_start():
    create_database(app=app)
    app.run(host='0.0.0.0')
t = Thread(target=flask_start)
t.start()
client.run('') #stabely
