CDIBase
===================
Data management application for early language labs that allowing the reading, searching, storing, and entry of Communicative Development Inventories data. **Developed by and for language labs, free and open source CDI management software for great good.**

<br>
### Authors and License
Released under the [GNU GPL v3 License](https://www.gnu.org/licenses/gpl-3.0.txt), this open source project exists apart from its original creators. Still, it was started by:

* (c) 2014 [Sam Pottinger of Gleap LLC](http://gleap.org) (active maintainer).
* (c) 2014 [Professor Eliana Colunga](http://psych.colorado.edu/~colunga/) of the [CU Language Project](http://psych.colorado.edu/~colungalab/CULanguage/CU-LANGUAGE.html) at the [University of Colorado Boulder](http://colorado.edu/).

<br>
### Background and Motivation

CDIBase allows early language labs software to maintain a standardized dataset for all child language inventory data regardless of study and the format of the CDI used. This allows labs to query / manage all of their data from all of their studies at once even across multiple languages.

This web (public Internet or private Intranet) application allows lab members to:

* Remotely enter CDI data directly into a centralized database.
* Send forms to parents over email and automatically collect responses to CDIs securely over the Internet.
* Download existing CDI data in CSV files using different "presentation formats" that, to support lab members' various custom and commercial software solutions, specifies how standard values like true, false, male, and female are reported in the resulting download.
* Download CDI data from multiple studies even if different MCDI forms were used. The application allows the user to specify if the application should combine all results in a single CSV or if Daxlabbase should render a ZIP archive with a CSV file for each type of CDI used.
* Fine tune user access control, specifying which lab members should have access to what functionality of the web application.
* Automatically control and integrate with other lab software through a programmatically accesible API.

At the time of writing, only [sqlite3](www.sqlite.org) databases are supported. However, we need help in deciding what other databases to support. Patches welcome or speak up in the issue tracker!

<br>
### Technologies Used

Daxlabbase itself is written in [Flask](flask.pocoo.org/). The original version targets a [sqlite3](www.sqlite.org) database but any SQL database can be used with minimal modification. There is planned future support for MongoDB backends. The front-end, rendered by [Jinja2](jinja.pocoo.org) templates, uses some [jQuery](http://jquery.com/).

The suggested production (server) environment runs a [Gunicorn](http://gunicorn.org/) instance managed by [Supervisor](http://supervisord.org/) behind public facing [nginx](http://wiki.nginx.org/Main).

The project uses Google's [pymox](https://code.google.com/p/pymox/) for automated testing.

Want support for other types of databases? Speak up in the issue tracker and, of course, patches are welcome.

<br>
### Environment Setup

* Checkout the repository:
```
$ git clone git@github.com:Samnsparky/daxlabbase.git
```

* Development requires Python's [virtualenv](http://www.virtualenv.org/en/latest/). If you do not already have that installed, use [pip](http://www.pip-installer.org/en/latest/):
```
$ pip install virtualenv
```

* Create a new virtual environment:
```
$ cd daxlabbase
$ virtualenv venv
```

* Enter into the virtual environment:
```
$ source venv/bin/activate
```

* Install required software:
```
$ pip install -r requirements.txt
```

* Get a copy of ```flask_config.cfg``` or create a new one yourself. This is not included in the GitHub repo for security reasons. It can be found in a previous development / production environment. As with most Flask applications, flask_config.cfg lives in the root folder of the application. If creating from scratch, it should looke like the following:
```
NO_MAIL = False // [boolean] True for allowing the application to send email or False otherwise.
DEBUG = False // [boolean] True for showing debug information about any errors encountered. False otherwise. True is not suggested for production.
SECRET_KEY = "..." // [string] This is unique to the application. Generate your own with code below...
MAIL_SERVER = "..." // [string] Consider "localhost" if the server can send mail itself. Otherwise full address to the SMTP server. See below for more info.
MAIL_SEND_FROM = "someone@example.com" // The full email address from which application email should be sent.
DEBUG_PRINT_EMAIL = False // [boolean] True if the contents of emails being send should be printed to the terminal. False is suggested for production.
MAIL_PORT = 25 // [integer] The port the SMTP server is running on.
```

At this time, only sqlite databases at ./db/daxlab.db are supported. We would love to improve on this so, if you have other types of databases you want to see supported, speak up or submit a patch!

* If you are creating a flask_config.cfg from scratch, generate a secret key with:
```
>>> import os
>>> os.urandom(24)
'new secret key'
```

* If using an external SMTP server, use the configuration constants listed in the [Flask-Mail documentation](http://pythonhosted.org/flask-mail/). They can be included directly in flask_config.cfg.

* Depending on your operating system, you may need to install [sqlite3](http://www.sqlite.org/) locally.

* Create a local development db:
```
$ cd db
$ sqlite3 daxlab.db < create_local_db.sql
```

* Create an uploads directory
```
$ mkdir uploads
```

You can leave the virtual environment with ```$ deactivate```.

<br>
### Local Development Server

Start the local development server with:
```
$ python runserver.py
```

Navigate to ```http://localhost:5000/base``` to access the locally running development server. 

You may find it useful to have mail printed to the console as it does not send while in debug mode. Simply edit flask_config.cfg to read ```DEBUG_PRINT_EMAIL = True```.

Note that, if you created the local testing DB, the local copy of the application does not have any user accounts. To create a test account for test@example.com,
```
$ cd db
$ sqlite3 daxlab.db < create_test_user.sql
```

Use the forgot password feature to get a temporary password for that new user. Please be aware that ```create_test_user.sql``` gives test@example.com full permissions.

Finally, before some features of the application can be used, you will also need to provide YAML descriptions of MCDI forms, a CSV of percentile information, and a YAML specification of a presentation format. Examples are available in a [private gist](https://gist.github.com/Samnsparky/db2ac1b742b98f954245).

These can be provided through the edit formats tab or at ```http://127.0.0.1:5000/base/edit_formats```.

<br>
### Staging / Pre-production Server

At this time, this project, unfortunately, does not have a staging server feature or guidelines on running a stage server.

<br>
### Deployment / Production Server

You will need to be given the location of the code as well as directory access permissions by the server superuser. After securing that, navigate to the daxlabbase environment.

The code can be uploaded by pulling from the master branch of the project's repository.
```
$ git pull
```

The suggested deployment is a gunicorn server processes monitored by supervisor. The installation instructions vary by operating system.

However, after setting up the server, reload the application with:
```
$ sudo supervisorctl
supervisor> stop daxlabbase
daxlabbase: stopped
supervisor> start daxlabbase
daxlabbase: started
supervisor> exit
```

The uploads directory needs to be writable by the application. At this time, file storage services like S3 are not supported.

<br>
### Automated Testing

Run unit tests with:
```
$ python run_test.py
```

You should see output that looks like:
```
$ python run_test.py 

Ran XX tests in 0.545s 

OK
```

<br>
### Notes on software architecture

The application consists of models, views (templates), controllers, and utilities. While following MVC, those utilities split out more complex logic not dealing directly with user responses to increase testability. Both can be found in the utilities and controllers directories respectively under the prog_code directory.

<br>
### Standards, Conventions, and State of Development

Ideally future development should follow an 80% unit testing coverage guidelines for the controllers with discretionary unit test coverage for the utilities. Python code should include [epydoc](http://epydoc.sourceforge.net/) inline documentation and should follow [Google's Python Style Guidelines](http://google-styleguide.googlecode.com/svn/trunk/pyguide.html).
