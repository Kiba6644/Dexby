from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from instagrapi import Client
from os import path
import time
from threading import Thread, Event
import random
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
db = SQLAlchemy(app)

sleep_mode = Event()
sleep_mode.set()

last_activity_time = time.time()

delays = [5, 10, 15, 20, 25, 30, 50]

username = "trupthiwho_"
password = "zxcvbnm@420"

cl = Client()
cl.login(username, password)

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

pending_moods = {}
delay_index = 0
delay = 5
def check_and_respond():
    global last_activity_time
    global delay_index
    global delay
    while True:
        if not sleep_mode.is_set():
            delay = delays[delay_index]
            if delay_index < len(delays) - 1:
                delay_index += 1
                print(delay_index)
            
            try:
                with app.app_context():
                    messages = cl.direct_threads(amount=1)
                    for message in messages:
                        print("working")
                        thread_id = message.id
                        last_message = cl.direct_messages(thread_id, amount=1)[0]
                        user_id = last_message.user_id
                        last_activity_time = time.time()
                        if user_id in pending_moods:
                            try:
                                mood = int(last_message.text.strip())
                                if 1 <= mood <= 10:
                                    journal_id = pending_moods.pop(user_id)
                                    journal_entry = Journal.query.get(journal_id)
                                    if journal_entry:
                                        journal_entry.mood = mood
                                        db.session.commit()
                                        response = f"Thanks! I've updated your mood as {mood}/10 for today's journal."
                                    else:
                                        response = "Could not find your journal entry to update the mood."
                                else:
                                    response = "Please enter a mood rating between 1 and 10."
                            except ValueError:
                                response = "Please enter a valid number for your mood rating."
                            delay_index = 0
                            cl.direct_send(response, [user_id])
                        else:
                            handle_commands(last_message, user_id)

                time.sleep(delay + random.uniform(-2.0, 2.0))
                
            except Exception as e:
                cl.direct_send(f"An Error Occured!\n\n{e}", [user_id])
        
        else:
            if time.time() - last_activity_time > 180:
                sleep_mode.set()
            time.sleep(5)

def handle_commands(last_message, user_id):
    text = last_message.text.lower()
    global delay_index
    global delay
    response = ""
    with app.app_context():
        if text.startswith("log"):
            note = text[4:].strip() 
            entry = Journal(entry=note, date=str(time.strftime("%d-%m-%y")))
            db.session.add(entry)
            db.session.commit()
            pending_moods[user_id] = entry.id
            response = f"Your journal for today has been updated with the ID: {entry.id}. Could you rate your mood on a scale of 1/10 for me?"
            
        elif text.startswith("nitlog"):
            note = text[7:].strip()
            entry = nit(entry=note, date=str(time.strftime("%d-%m-%y")))
            db.session.add(entry)
            db.session.commit()
            response = f"Updated! ID: {entry.id}"

        elif text.startswith("view"):
            if text[5:].startswith("id"):
                log = Journal.query.filter_by(id=int(text[8:].strip())).first()
                if log.deleted == False:
                    response = f"Hey da! heres the journal with ID:{log.id}\n\n{log.entry}\n-{log.date}, Mood: {log.mood}/10"
                else:
                    response = f"Could not find the entry you are looking for!"

            elif text[5:].startswith("date"):
                logs = Journal.query.filter_by(date=text[10:].strip()).all()
                response = f"Here are your journal entries for {text[10:].strip()}:\n\n"
                response += "\n".join(f"ID: {log.id} - {log.entry[:30]}..." for log in logs if log.deleted == False)
            
            elif text[5:].startswith("last"):
                a = db.session.query(Journal).count()
                response = f"Here are the last {text[10:].strip()} journal entries!"
                for i in range(int(text[10:].strip())):
                    log = Journal.query.filter_by(id=((a-i))).first()
                    if log.deleted == False:
                        response += f"ID: {log.id} - {log.entry[:30]}..."

            elif text[5:].startswith("nithi"):
                a = db.session.query(nit).count()
                response = "Sure! Heres the latest entry by him:"
                for i in range(a):
                    log = nit.query.filter_by(id=(i+1)).first()
                    if log.read == False:
                        response += f"\n\n{log.entry}\n-{log.date}"
                        log.read = True
                        db.session.commit()
                        break
                if response == "Sure! Heres the latest entry by him:":
                    response = "Unfortunately i could not find any new entries from him."

        elif text.startswith("delete"):
            log = Journal.query.filter_by(id=int(text[7:].strip())).first()
            log.deleted = True
            db.session.commit()
            response = f"Successfully Deleted entry with ID {log.id}"

        elif text.startswith("grat"): 
            if text[5:].startswith("view"):
                a = db.session.query(grat).count()
                response = "Heres a list of things to feel happy about in life!"
                for i in range(a):
                    log = grat.query.filter_by(id=(i+1)).first()
                    response += f"\n{(i+1)}. {log.entry}" 
            else:
                db.session.add(grat(entry=str(text[5:].strip())))
                db.session.commit()
                response = f"You are greatful to have {text[5:].strip()} in life!. Understood."

        elif text.startswith("sleep"):
            sleep_mode.set()

        elif text.startswith("help"):
            response = "Heres a list of all the commands:\n"
            response += "\nlog <your journal>: Adds a new entry to your Journal."
            response += "\nview <id>/<date>: View the Journal with given ID or Date."
            response += "\nview last <n>: View the last N journals."
            response += "\ndelete <id>: Deletes the journal."
            response += "\ngrat <entry>: Add into a list of things that youre greatful for."
            response += "\ngrat view: View the gratitude list."
            response += "\nview nithi: Shows the Latest note he wrote."
            #response += "\ngood mood: Shows a list of all the notes you wrote with a good mood."
            response += "\n\n*Made with love for Clarol <3*"

        if response != "":
            cl.direct_send(response, [last_message.user_id]) 
            delay = 5
            delay_index = 0

@app.route('/')
def index():
    global last_activity_time
    last_activity_time = time.time()
    sleep_mode.clear()
    return "Dexby is now active and checking for new messages!"

if __name__ == '__main__':
    bot_thread = Thread(target=check_and_respond, daemon=True)
    bot_thread.start()
    
    app.run(debug=False)

