# NaHan: A Tiny Forum.

[NaHan](http://bbs.selfboot.cn/) is a tiny forum written by Python flask and bootstrap.  Its goal is to learn flask and web development in practice.

Topic page:

![][1]

Admin page:

![][2]

# Features

Major features:

1. Whole user manage system, containing registration, login, password change, retrieve;
2. Topic management system, login users can create topics, append topics, have comments on topics.
3. Markdown support in topic, appendix of topic and comment.
4. Can use `@someone` to remind other user anywhere.  The user which be is reminded will receive notify.
5. A convenient administrator system, super user can block or activate users, topics, nodes and comments.
6. A simple keyword search engine, one can search some specific topics.

You can sign up for an account and have a explore as normal user.  You can even login as an administrator in [admin page](http://bbs.selfboot.cn/admin/) with username 1291023320@qq.com, password 1.  Then you can try to block some topics(comments and users as well) and reactive them again.

# How to Run

1. Firstly, make sure all the relevant modules installed.

    You'd better use [virtualenv](https://virtualenv.pypa.io/en/stable/) to create a isolated python environments, and then use pip to install all the requirements.
    
        pip install -r requirements.txt
        
2. Do some custom configure in `config.py`, have a glance as followers:

        # flask config
        SECRET_KEY = os.environ.get('SECRET_KEY') or '!@#$%^&*12345678'
        
        # Config about senting email.
        MAIL_SERVER = 'smtp.qq.com'
        MAIL_PORT = 465
        MAIL_USE_SSL = True
        MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
        MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
        FORUM_MAIL_SUBJECT_PREFIX = 'NaHan'
        FORUM_MAIL_SENDER = 'Nahan <selfboot@qq.com>'

        # Optional, setting about translation.
        BABEL_DEFAULT_LOCALE = 'zh'
        BABEL_DEFAULT_TIMEZONE = 'CST'
        
        # Some config about forum, containing pagination page size, saving position and limit of avatar.
        PER_PAGE = 10   
        UPLOAD_FOLDER = os.path.join(basedir, 'nahan/static/upload')
        ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
        MAX_CONTENT_LENGTH = 512 * 1024
        
        # Database setting.
        SQLALCHEMY_DATABASE_URI = (os.environ.get('DEV_DATABASE_URL') or
                               'mysql://root:******@localhost/nahan')

3. Start corresponding database service.

    In MacOS, start mysql using the following command:
    
        mysql.server start
         
4. Go to the project's directory, run `python manage.py runserver`. 

For more about how to run a flask project, you need to have much knowledge about flask, [docs](http://flask.pocoo.org/docs/0.11/) can be found here. 

[1]: picture/front_page.png
[2]: picture/admin_page.png


