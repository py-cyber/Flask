from requests import request
from flask import Flask
from data1 import db_session, news_api, news_resources
from data1.users import User
from data1.news import News
from forms.news import NewsForm
from forms.user import RegisterForm, LoginForm
from flask import render_template, redirect
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import abort, Api

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
app = Flask(__name__)
api = Api(app)


def main():
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()
    '''user = User()
    user.name = "Пользователь 1"
    user.about = "биография пользователя 1"
    user.email = "email@email.ru"
    db_sess = db_session.create_session()
    db_sess.add(user)
    db_sess.commit()
    user = db_sess.query(User).first()
    print(user.name)
    for user in db_sess.query(User).all():
        print(user)
    for user in db_sess.query(User).filter(User.id > 1, User.email.notilike("%1%")):
        print(user)
    user = db_sess.query(User).filter(User.id == 1).first()
    print(user)
    user.name = "Измененное имя пользователя"
    user.created_date = datetime.datetime.now()
    db_sess.commit()'''

    @login_manager.user_loader
    def load_user(user_id):
        db_sess = db_session.create_session()
        return db_sess.query(User).get(user_id)

    @app.route("/")
    def index():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.is_private is not True)
        return render_template("index.html", news=news)

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
            user = User(
                name=form.name.data,
                email=form.email.data,
                about=form.about.data
            )
            user.set_password(form.password.data)
            db_sess.add(user)
            db_sess.commit()
            return redirect('/login')
        return render_template('register.html', title='Регистрация', form=form)

    @app.route("/cookie_test")
    def cookie_test():
        visits_count = int(request.cookies.get("visits_count", 0))
        if visits_count:
            res = make_response(
                f"Вы пришли на эту страницу {visits_count + 1} раз")
            res.set_cookie("visits_count", str(visits_count + 1),
                           max_age=60 * 60 * 24 * 365 * 2)
        else:
            res = make_response(
                "Вы пришли на эту страницу в первый раз за последние 2 года")
            res.set_cookie("visits_count", '1',
                           max_age=60 * 60 * 24 * 365 * 2)
        return res

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
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
        if current_user.is_authenticated:
            news = db_sess.query(News).filter(
                (News.user == current_user) | (News.is_private is not True))
        else:
            news = db_sess.query(News).filter(News.is_private is not True)
        return redirect("/")

    @app.route('/news', methods=['GET', 'POST'])
    @login_required
    def add_news():
        form = NewsForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            news = News()
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            current_user.news.append(news)
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect('/')
        return render_template('news.html', title='Добавление новости',
                               form=form)

    @app.route('/news/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_news(id):
        form = NewsForm()
        if request.method == "GET":
            db_sess = db_session.create_session()
            news = db_sess.query(News).filter(News.id == id,
                                              News.user == current_user
                                              ).first()
            if news:
                form.title.data = news.title
                form.content.data = news.content
                form.is_private.data = news.is_private
            else:
                abort(404)
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            news = db_sess.query(News).filter(News.id == id,
                                              News.user == current_user
                                              ).first()
            if news:
                news.title = form.title.data
                news.content = form.content.data
                news.is_private = form.is_private.data
                db_sess.commit()
                return redirect('/')
            else:
                abort(404)
        return render_template('news.html',
                               title='Редактирование новости',
                               form=form
                               )

    @app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
    @login_required
    def news_delete(id):
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            db_sess.delete(news)
            db_sess.commit()
        else:
            abort(404)
        return redirect('/')

    from flask import make_response

    @app.errorhandler(404)
    def abort_if_news_not_found(news_id):
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        if not news:
            abort(404, message=f"News {news_id} not found")

    # def not_found(error):
    #    return make_response(jsonify({'error': 'Not found'}), 404)

    # для списка объектов
    api.add_resource(news_resources.NewsListResource, '/api/v2/news')

    # для одного объекта
    api.add_resource(news_resources.NewsResource, '/api/v2/news/<int:news_id>')


def main_test():
    db_session.global_init("db/blogs.db")
    app.register_blueprint(news_api.blueprint)
    app.run()


if __name__ == '__main__':
    main()
    main_test()

# alembic revision --autogenerate -m "добавили признак публикации"
# alembic upgrade head
