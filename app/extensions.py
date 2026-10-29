from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import IMAGES, UploadSet
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()
mail = Mail()

covers = UploadSet("covers", IMAGES)
