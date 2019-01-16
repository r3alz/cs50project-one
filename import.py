import csv
import os

from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


f = open("books.csv")
reader = csv.reader(f)
next(reader) #skips header from first line
for isbn, title, author, year in reader: #loop gives each column a name
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
    print(f"Added {isbn}, {title}, {author}, {year} to the books table.")

db.commit()