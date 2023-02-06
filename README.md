# Warbler
A Twitter clone with a Springboard spin! Warbler is a platform where users can post and like tweets (warbles) and follow other users. This application is built using Flask and is intended to practice reading and understanding an existing application, as well as fixing bugs, writing tests, and extending it with new features.

## Log

1. Fix Current Features
- Read and understand the model
- Fix the logout
- Fix the user profile
- Fix the user cards
- Profile edit
- Fix the homepage
- Research and understand the login strategy
2. Likes
- Allow users to like and unlike warbles written by other users. Show the number of liked warbles on a user's profile page.
3. Tests
- Add tests for the user and message models and views.

## Tech Stack
This project was made using the following technologies:
- Python
- Flask
- Flask-SQLAlchemy
- Flask-Bcrypt
- Flask-WTForms

## Setup

To set up Warbler, follow these steps:

1. Create a Python virtual environment:
```
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```
> Note: If you are using Python 3.8, then you may face issues while installing the packages in the requirements.txt file. In that case, delete pyscopg2-binary from the requirements.txt file and use pip install pyscopg2-binary in the terminal to install it successfully.
2. Set up the database:
```
(venv) $ createdb warbler
(venv) $ python seed.py
```
3. Start the server:
```
(venv) $ flask run
```
