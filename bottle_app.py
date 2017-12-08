import bottle
import sqlite3
import os
import re
import httpagentparser
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from bottle.ext import sqlite
from bs4 import BeautifulSoup


app = bottle.Bottle()
plugin = sqlite.Plugin(dbfile='data.db')
app.install(plugin)

time_format = '%Y-%m-%d %H:%M:%S'
comment_time_format = '%H:%M:%S %d.%m.%Y'

index = 1

@app.post('/add_comment')
def add_comment(db):
    name = bottle.request.forms.username
    comment = bottle.request.forms.comment
    if is_correct(comment, {"b", "i"}) and is_correct(name, set()):
        ip = get_ip()
        comment_time = datetime.now().strftime(comment_time_format)
        db.execute("insert into comment (ip, comment_time, comment, name, number_photo) values (?, ?, ?, ?, ?)",
                      (ip, comment_time, comment, name, index))
    return bottle.redirect('/')

def is_correct(comment, valid_tags):
    openTag = re.compile(r'(<[a-z1-9]*>)')
    closeTag = re.compile(r'(</[a-z1-9]*>)')
    open =  openTag.findall(comment)
    close = closeTag.findall(comment)
    if not check_tags(valid_tags, open, False) or not  check_tags(valid_tags, close, True):
        return False

    soup = BeautifulSoup(comment, "html.parser")
    tags = [tag.name for tag in soup.find_all()]
    tags = set(tags)
    for tag in valid_tags:
        if tag in tags:
            tags.remove(tag)
    return not len(tags)

def check_tags(valid, tags, isClose):
    for o in tags:
        if isClose:
            tag = o[2:-1]
        else:
            tag = o[1:-1]
        if tag not in valid:
            return False
    return True

@app.post('/save_index')
def save_index(db):
    global index
    index = bottle.request.forms.index
    return bottle.redirect('/')

@app.get('/load_comment')
def load_comment(db):
    comments = db.execute("""select * from comment as c where c.number_photo = ?""", (index, )).fetchall()
    result = ""
    for comment in comments:
        result += """<div class="comm">
                    <p class = "date">{}</p>
                    <p class = "username">{}</p>
                    <p class = "data">{}</p>
                    </div>""".format(comment['comment_time'],comment['name'],comment['comment'])
    return result

@app.route('/')
def root(db):
    last_visit = format_message(get_date_last_visit(db))
    update_visits(db)
    hits = get_hits(db)
    visits = get_visits(db)
    visits_today = get_visits_today(db)

    image = Image.new("RGBA", (88, 31), 'rgb(255, 255, 255)')
    draw = ImageDraw.Draw(image)
    draw.rectangle(((0, 0), (87, 30)), outline="rgb(95, 158, 160)")
    draw.rectangle(((0, 0), (88, 10)), fill="rgb(95, 158, 160)")
    draw.text((3, 1), str(hits))
    draw.text((3, 11), str(visits), fill='rgb(0, 0, 0)')
    draw.text((3, 21), str(visits_today), fill='rgb(0, 0, 0)')
    image_name = 'counter.png'
    #image.save( '/home/BlokhinaElizaveta/mysite/static/' + image_name, 'PNG')
    image.save( 'static/' + image_name, 'PNG')

    #return bottle.template('/home/BlokhinaElizaveta/mysite/index.html', image_name = image_name, last_visit = last_visit)
    return bottle.template('index.html', image_name = image_name, last_visit = last_visit)

def update_visits(db):
    ip = get_ip()
    last_time = datetime.now().strftime(time_format)
    browser = get_browser()

    last_visit = get_last_visit(db, ip)

    if last_visit:
        time_last_visit = datetime.strptime(last_visit['last_time'], '%Y-%m-%d %H:%M:%S')
        delta_hours = (datetime.now() - time_last_visit).seconds // 3600
        if delta_hours >= 1:
            db.execute("insert into visitor (ip, last_time, browser) values (?, ?, ?)",
                   (ip,last_time, browser))
    else:
        db.execute("insert into visitor (ip, last_time, browser) values (?, ?, ?)",
            (ip, last_time, browser))

def get_visits(db):
    return db.execute("select count(*) as counter from visitor").fetchone()['counter']

def get_visits_today(db):
    current_day = datetime.now().strftime(time_format).split(' ')[0]
    return db.execute("""select count(*) as counter from
                        (select * from visitor as v
                         where substr(v.last_time, 1, 10) = ?) v""",
               (current_day,)).fetchone()['counter']

def get_hits(db):
    db.execute("update hits set hits = hits + 1")
    return db.execute("select hits from hits").fetchone()[0]

def get_ip():
    return bottle.request.environ.get('REMOTE_ADDR')

def get_browser():
    agent = bottle.request.environ.get('HTTP_USER_AGENT')
    browser = httpagentparser.detect(agent)
    if not browser or 'browser' not in browser:
        browser = agent.split('/')[0]
    else:
        browser = browser['browser']['name']
    return browser

def get_last_visit(db, ip):
    return db.execute("""select v1.*
        from visitor v1 left join visitor v2
        on (v1.ip = v2.ip and v1.id < v2.id)
        where v2.id is null and v1.ip = ?""", (ip,)).fetchone()

def get_date_last_visit(db):
    last_visit = get_last_visit(db, get_ip())
    if last_visit:
        time_last_visit = datetime.strptime(last_visit['last_time'], time_format)
        return time_last_visit.strftime('%d.%m.%Y')

def format_message(date):
    if date:
        return "Дата последнего посещения: {}".format(date)
    else:
        return "Вы ещё не посещали наш сайт"


@app.route('/<filename:path>')
def send_static(filename):
    #return bottle.static_file(filename, root='static/')
    return bottle.static_file(filename, root='st/')

app.run(host='localhost', port='8081', debug='True')