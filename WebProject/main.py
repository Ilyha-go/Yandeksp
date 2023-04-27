import os
from PIL import Image
from flask import Flask, render_template, request
from werkzeug.utils import redirect, secure_filename
from flask_login import LoginManager, current_user, login_required, logout_user

from data import db_session
from data.users import User
from data.wallpapers import WallPapers
from forms.user import RegisterForm
from forms.wallpapers import WallPapersForm
from data.tags import Tags

UPLOAD_FOLDER = './static/img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)

def add_user(name, email):
    user = User()
    user.name = name
    user.email = email
    return user


def add_tags(wallpaper):
    tags = []
    for elem in wallpaper.content.lower().replace(',', '').split():
        tag = Tags()
        tag.title = elem
        tag.wallpaper = wallpaper
        tags.append(tag)
    return tags



def add_wallpaper(title, file_name, content,  user):
    wallpaper = WallPapers()
    wallpaper.title = title
    wallpaper.file = file_name
    wallpaper.content = content
    wallpaper.user = user
    return wallpaper


def created(session):
    # Создание администратора
    admin = add_user('Admin', 'er@gmail.com')
    session.add(admin)
    # Создание пользователя user1
    user1 = add_user('user1', 'user1@gamil.com')
    session.add(user1)
    # Создание обоев пользователем user1
    user1 = session.query(User).filter(User.id == 2).first()
    wallpaper = add_wallpaper('forest', 'forest_1.png', 'лес, весна', user1)
    session.add(wallpaper)
    user1.wallpapers.append(wallpaper)
    tags = add_tags(wallpaper)
    
    '''for tag in tags:
        session.add(tag)'''

    for tag in tags:
        user1.tags.append(tag)
    session.commit()


@app.route("/")
def index():
    db_sess = db_session.create_session()
    # wallpapers = db_sess.query(WallPapers)
    if current_user.is_authenticated:
        wallpapers = db_sess.query(WallPapers).filter(
            (WallPapers.user == current_user) | (WallPapers.is_private != True))
        name = current_user.name
        text = f'Обои пользователя {name}'
    else:
        wallpapers = db_sess.query(WallPapers)
        text = 'Все обои'
        name = ''
    return render_template("index.html", wallpapers=wallpapers, text=text, name=name)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    from forms.loginform import LoginForm
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            from flask_login import login_user
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/wallpapers',  methods=['GET', 'POST'])
@login_required
def add_wallpapers():
    form = WallPapersForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        wallpapers = WallPapers()
        wallpapers.title = form.title.data
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            im = Image.open(f'static/img/{filename}')
            im_resize = im.resize((1900, 1200))
            im_resize.save(f'static/img/{filename}')
            wallpapers.file = filename
        wallpapers.content = form.content.data

        current_user.wallpapers.append(wallpapers)

        for tag in add_tags(wallpapers):
            current_user.tags.append(tag)

        db_sess.merge(current_user)
        db_sess.commit()

        return redirect('/')
    return render_template('wallpapers.html', title='Добавление',
                           form=form)


@app.route('/wallpapers_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def wallpapers_delete(id):
    db_sess = db_session.create_session()
    wallpapers = db_sess.query(WallPapers).filter(WallPapers.id == id,
                                                  WallPapers.user == current_user
                                                  ).first()
    if wallpapers:
        tags_delete = db_sess.query(Tags).filter(Tags.wallpaper_id == wallpapers.id)
        for tag in tags_delete:
            db_sess.delete(tag)
        db_sess.delete(wallpapers)
        db_sess.commit()
    else:
        os.abort(404)
    return redirect('/')


@app.route("/show_tags/<tagname>")
def show_tags(tagname):
    # logout()
    db_sess = db_session.create_session()
    tags = db_sess.query(Tags).filter(Tags.title == tagname)
    wallpapers_id = db_sess.query(Tags.wallpaper_id).filter(Tags.title == tagname).all()
    wallpapers_id = [item[0] for item in wallpapers_id]
    wallpapers = db_sess.query(WallPapers).filter(WallPapers.id.in_(wallpapers_id))
    text = f'Обои с тегом {tagname}'
    return render_template("index.html", wallpapers=wallpapers, text=text, name='')


@app.route("/show_user/<int:userid>")
def show_user(userid):
    # logout()
    db_sess = db_session.create_session()
    wallpapers = db_sess.query(WallPapers).filter(WallPapers.user_id == userid)
    user = db_sess.query(User).filter(User.id == userid).first()
    text = f'Обои пользователя {user.name}'
    return render_template("index.html", wallpapers=wallpapers, text=text, name='')


def main():
    db_session.global_init("db/wallpaper.db")
    session = db_session.create_session()
    # Тестовое создание базы данных
    # created(session)
    # Проверка базы данных
    '''for user in session.query(User):
        print(user)
    for elem in session.query(WallPapers):
        print(elem)'''
    app.run()


if __name__ == '__main__':
    main()