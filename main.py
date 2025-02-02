from flask import Flask, render_template, redirect, url_for, request,session
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

MOVIES_URL="https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1"
API_KEY="f6306609e13bf331a3d4c4957ad85836"
API_DB_KEY="eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmNjMwNjYwOWUxM2JmMzMxYTNkNGM0OTU3YWQ4NTgzNiIsIm5iZiI6MTczNzk4NzYwMi42NjgsInN1YiI6IjY3OTc5NjEyYzdiMDFiNzJjNzI0MTEyYSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.LrERYYWjUyjoLIxWOpE76SVXOBPZdX1X3nBr5ujlwsA"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db=SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    title:Mapped[str]=mapped_column(String(250),unique=True,nullable=False)
    year:Mapped[int]=mapped_column(Integer,nullable=False)
    description:Mapped[str]=mapped_column(String(500),nullable=False)
    rating:Mapped[float]=mapped_column(Float,nullable=True)
    ranking:Mapped[int]=mapped_column(Integer,nullable=True)
    review:Mapped[str]=mapped_column(String(250),nullable=True)
    img_url:Mapped[str]=mapped_column(String(250),nullable=False)

with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

class AddMovieForm(FlaskForm):
    movie_title=StringField("Movie Title")
    submit=SubmitField("Add Movie")


@app.route("/")
def home():
    # READ ALL THE RECORDS 
    result=db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies=result.scalars().all()
    for i in range(len(all_movies)):# 3
        all_movies[i].ranking=len(all_movies)-i

        db.session.commit()
        

    return render_template("index.html",movies=all_movies)

@app.route("/edit",methods=['GET','POST'])
def rate_movie():
    form=RateMovieForm()
    #Getting the id of movie which we want to edit
    movie_id=request.args.get("id")
    movie_selected=db.get_or_404(Movie,movie_id)

    if form.validate_on_submit():
        #Get the input of updated rating and update in databse
        movie_selected.rating = float(form.rating.data)
        movie_selected.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html",movie=movie_selected,form=form)


@app.route("/delete")
def delete_movie():
    movie_id=request.args.get("id")

    # DELETE BY ID 
    movie_to_delete=db.get_or_404(Movie,movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add",methods=['GET','POST'])
def add():
    form=AddMovieForm()
    if form.validate_on_submit():
        movie_title=form.movie_title.data
        session['movie_title'] = movie_title
        response=requests.get(MOVIES_URL,params={"api_key":API_KEY,"query":movie_title})
        data=response.json()["results"]
        print(f"ADD DATA : {data}")

        return render_template("select.html",options=data)
    return render_template("add.html",form=form)


@app.route("/find", methods=['GET'])
def find_movie():
    movie_api_id = request.args.get("id")
    # print(f"THE TYPE OF ID IS: {type(movie_api_id)}")
    movie_title = session.get('movie_title')  # Retrieve the movie title from the session
    # print(movie_title)

    if movie_api_id and movie_title:
        print(f"THE MOVIE ID: {movie_api_id}\n")
        response = requests.get(MOVIES_URL, params={"api_key": API_KEY, "query": movie_title})
        data = response.json()["results"]
        # print(f"DATA : {data}")

        # Now find the movie in the response data based on the ID
        for movie in data:
            print("WE ARE IN LOOP----------------------------")
            if str(movie["id"]) == movie_api_id:
                new_movie = Movie(
                    title=movie["title"],
                    year=movie["release_date"].split("-")[0],
                    img_url=f"{MOVIE_DB_IMAGE_URL}{movie['poster_path']}",
                    description=movie["overview"]
                )
                db.session.add(new_movie)
                db.session.commit()
                break

        return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))  # Redirect to home if no movie_title or movie_api_id

if __name__ == '__main__':
    app.run(debug=True)
