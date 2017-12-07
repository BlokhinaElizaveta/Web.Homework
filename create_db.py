import sqlite3

con = sqlite3.connect('data.db')
con.execute('''create table visitor(
            id integer primary key,
            ip varchar(30) not null,
            last_time varchar(30),
            browser varchar(30))''')

con.execute('''create table comment(
            id integer primary key,
            ip varchar(30) not null,
            comment_time varchar(30),
            comment text,
            name varchar(30),
            number_photo varchar(10))''')

con.execute("create table hits (hits integer not null);")
con.execute("insert into hits values (?)", (0,))
con.commit()