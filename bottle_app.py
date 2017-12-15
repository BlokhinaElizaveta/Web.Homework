import bottle
import sqlite3
import os
import re
import httpagentparser
from passlib.hash import sha256_crypt
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from bottle.ext import sqlite
from bs4 import BeautifulSoup
from beaker.middleware import SessionMiddleware

session_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 300,
    'session.auto': True
}

app = bottle.app()
plugin = sqlite.Plugin(dbfile='data.db')
app.install(plugin)

app = SessionMiddleware(app, session_opts)

time_format = '%Y-%m-%d %H:%M:%S'
comment_time_format = '%H:%M:%S %d.%m.%Y'

index = 1

@bottle.route('/statistic', method='POST')
def get_statistic(db):
    statistic = db.execute("""select * from visitor""").fetchall()
    result = ""
    for elem in statistic:
        result += """<div class="visit">
                    <p class = "ip">{}</p>
                    <p class = "time">{}</p>
                    <p class = "browser">{}</p>
                    <p class = "visit_id">{}</p>
                    <p class = "edit" onclick="deleteVisit(event)"> Удалить </p>
                    </div>""".format(elem['ip'], elem['last_time'], elem['browser'], elem['id'])
    return result

@bottle.route('/delete_visit', method='POST')
def delete_visit(db):
    id = bottle.request.forms.id
    db.execute("""delete from visitor where id=?""", (id,))
    return "OK"

@bottle.route('/put_like', method='POST')
def put_like(db):
    name = get_login()
    likes = db.execute("""select * from likes where login=? and number_photo=?""", (name, index)).fetchall()
    if (len(likes) != 0):
        db.execute("""delete from likes where  login=? and number_photo=?""",
            (name, index))
    else:
        db.execute("insert into likes (login, number_photo) values (?, ?)",
            (name, index))

@bottle.route('/get_count_like', method='POST')
def get_count_like(db):
    count_likes = db.execute("""select count(*) as counter from likes where number_photo=?""", (index, )).fetchone()['counter']
    return str(count_likes)

@bottle.route('/is_like', method='POST')
def is_like(db):
    name = get_login()
    likes = db.execute("""select * from likes where login=? and number_photo=?""", (name, index)).fetchall()
    return  str(len(likes) != 0)

@bottle.route('/register', method='POST')
def register(db):
    login = bottle.request.forms.login
    password = bottle.request.forms.password
    users = db.execute(
        """select * from users as u where u.login = ?""",
        (login,)).fetchall()
    if not login or not password:
        return "Empty"
    if (len(users) != 0):
        return "Exist"
    if (len(login) > 30 or len(password) > 30):
        return "Long"

    hashed_password = sha256_crypt.hash(password)
    db.execute("insert into users (login, hash_password) values (?, ?)",
                      (login, hashed_password))
    s = bottle.request.environ.get('beaker.session')
    s['login'] = login
    s.save()
    return "OK"

@bottle.route('/auth', method='POST')
def auth(db):
    login = bottle.request.forms.login
    password = bottle.request.forms.password
    user = db.execute(
        """select * from users as u where u.login = ?""",
        (login,)).fetchone()
    if user:
        if sha256_crypt.verify(password, user['hash_password'] ):
            s = bottle.request.environ.get('beaker.session')
            s['login'] = login
            s.save()
            return "OK"
    return "Error"


@bottle.route('/add_comment', method='POST')
def add_comment(db):
    name = get_login()
    comment = bottle.request.forms.comment
    if is_correct(comment, {"b", "i"}) and is_correct(name, set()):
        ip = get_ip()
        comment_time = datetime.now().strftime(comment_time_format)
        db.execute("insert into comment (ip, comment_time, comment, name, number_photo) values (?, ?, ?, ?, ?)",
                      (ip, comment_time, comment, name, index))

@bottle.route('/edit_comment', method='POST')
def edit_comment(db):
    comment = bottle.request.forms.text
    comment_id = bottle.request.forms.comment_id
    if is_correct(comment, {"b", "i"}):
        db.execute("update comment set comment = ? WHERE id = ?", (comment, comment_id))

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

@bottle.route('/save_index', method='POST')
def save_index(db):
    global index
    index = bottle.request.forms.index
    return bottle.redirect('/')

@bottle.route('/get_old_comment', method='POST')
def get_old_comment(db):
    comment_id = bottle.request.forms.comment_id
    comment = db.execute("""select * from comment as c where c.id = ?""", (comment_id, )).fetchone()
    return comment['comment']

@bottle.route('/load_comment', method='POST')
def load_comment(db):
    name = get_login()
    comments = db.execute("""select * from comment as c where c.number_photo = ?""", (index, )).fetchall()
    result = ""
    edit = ""
    for comment in comments:
        if name == comment['name']:
            edit = '<p class="edit" onclick="openEditForm(event)">Редактировать</p>'
        result += """<div class="comm">
                    <p class = "date">{}</p>
                    <p class = "username">{}</p>
                    <p class = "data">{}</p>
                    <p class = "comment_id">{}</p>
                    {}
                    </div>""".format(comment['comment_time'],comment['name'],comment['comment'], comment['id'], edit)
    return result


@bottle.route('/')
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

def get_login():
    s = bottle.request.environ.get('beaker.session')
    if 'login' in s:
        return s['login']

@bottle.route('/<filename:path>')
def send_static(filename):
    #return bottle.static_file(filename, root='static/')
    return bottle.static_file(filename, root='st/')

bottle.run(app=app, host='localhost', port='8044', debug='True')