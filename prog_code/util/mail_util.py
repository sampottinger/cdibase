"""Logic for sending email through the application.

Copyright (C) 2014 A. Samuel Pottinger ("Sam Pottinger", gleap.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

@author: Sam Pottinger
@license: GNU GPL v3
"""

import threading

import flask.ext.mail as flask_mail

TESTING = False
DEBUG_PRINT_EMAIL = False

mail_lock = threading.Lock()


class MailKeeper:
    """Singleton to maintain SMTP mail client."""

    instance = None

    @classmethod
    def get_instance(cls):
        """Get a shared instance of this singleton.

        @return: Shared instance of the MailKeeper singleton.
        @rtype: MailKeeper
        """
        return cls.instance

    @classmethod
    def init_mail(cls, app):
        """Initialize the global MailKeeper singleton for the given app.

        @param app: The Flask app to initialize with.
        @type app: flask.Flask
        """
        cls.instance = MailKeeper(app)

    def __init__(self, app):
        """Create a new MailKeeper.

        @param app: The Flask app to create mailing capabilites for.
        @type app: flask.Flask
        """
        self.__mail = flask_mail.Mail(app)
        self.__from_addr = app.config['MAIL_SEND_FROM']

    def get_mail_instance(self):
        """Get the underlying Flask-Mail client.

        @return: Flask-Mail SMTP client / facade.
        @rtype: flaskext.mail.Mail
        """
        return self.__mail

    def get_from_addr(self):
        return self.__from_addr


def init_mail(app):
    """Initialize the MailKeeper singleton to enable SMTP capabilities.

    Creates the system-wide MailKeeper singleton which allows the application to
    send email. This should be called once at the initialization of the Flask
    application.

    @param app: The flask application to initialize the MailKeeper with.
    @type app: flask.Flask
    """
    MailKeeper.init_mail(app)


def disable_mail():
    MailKeeper.instance = None


def get_mail_keeper():
    return MailKeeper.get_instance()


def send_msg(email, subject, message):
    """Send an email.

    Sends an email through the current MailKeeper or takes no action if a
    mail keeper is not available.

    @param message: The message to send.
    @type message: flaskext.mail.Message
    """
    with mail_lock:
        
        mail_keeper = get_mail_keeper()
        
        if mail_keeper:
            flask_message = flask_mail.Message(
                subject,
                sender=mail_keeper.get_from_addr(),
                recipients=[email.replace(' ', '')],
                body=message
            )
            mail_keeper.get_mail_instance().send(flask_message)
        
        else:
            if DEBUG_PRINT_EMAIL:
                print message
