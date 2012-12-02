"""Logic for sending email through the application.

@author: Sam Pottinger
@license: GNU GPL v2
"""


import flask.ext.mail as flask_mail

class MailKeeper:

    instance = None

    @classmethod
    def get_instance(cls):
        return cls.instance

    @classmethod
    def init_mail(cls, app):
        cls.instance = MailKeeper(app)

    def __init__(self, app):
        self.__mail = flask_mail.Mail(app)

    def get_mail_instance(self):
        return self.__mail

def init_mail(app):
    MailKeeper.init_mail(app)

def send_msg(message):
    mail_instance = MailKeeper.get_instance().get_mail_instance()
    mail_instance.send(message)
