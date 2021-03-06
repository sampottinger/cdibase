CDIBase
===================

Data management application for early language labs that allowing the reading, searching, storing, and entry of Communicative Development Inventories data. **Developed by and for language labs, free and open source CDI management software for great good.**

<br>

### Authors and License

Released under the [GNU GPL v3 License](https://www.gnu.org/licenses/gpl-3.0.txt), this open source project was started by [Sam Pottinger of Data Driven Empathy LLC](http://gleap.org) and has enjoyed gracious guidance from [Professor Eliana Colunga's](http://psych.colorado.edu/~colunga/) [CU Language Project](http://psych.colorado.edu/~colungalab/CULanguage/CU-LANGUAGE.html) at the [University of Colorado Boulder](http://colorado.edu/) (though the project is not officially affiliated or owned by the university).

[Sam Pottinger](http://gleap.org) continues to be the active maintainer / project lead.

(c) 2020 [Sam Pottinger](http://gleap.org)

<br>

### Background and Motivation

CDIBase allows early language labs software to maintain a standardized dataset for all child language inventory data regardless of study and the format of the CDI used. This allows labs to query / manage all of their data from all of their studies at once even across multiple languages.

This web (public Internet or private Intranet) application allows lab members to:

* Remotely enter CDI data directly into a centralized database.
* Send forms to parents over email and automatically collect responses to CDIs securely over the Internet.
* Download existing CDI data in CSV files using different "presentation formats" that, to support lab members' various custom and commercial software solutions, specifies how standard values like true, false, male, and female are reported in the resulting download.
* Download CDI data from multiple studies even if different CDI forms were used. The application allows the user to specify if the application should combine all results in a single CSV or if Cdibase should render a ZIP archive with a CSV file for each type of CDI used.
* Fine tune user access control, specifying which lab members should have access to what functionality of the web application.
* Automatically control and integrate with other lab software through a programmatically accesible API.

At the time of writing, only [sqlite3](www.sqlite.org) databases are supported. However, we need help in deciding what other databases to support. Patches welcome or speak up in the issue tracker!

<br>

### Technologies Used

Cdibase itself is written in [Flask](flask.pocoo.org/). The original version targets a [sqlite3](www.sqlite.org) database but any SQL database can be used with minimal modification. The front-end, rendered by [Jinja2](jinja.pocoo.org) templates, uses some [jQuery](http://jquery.com/) and [d3](https://d3js.org/).

The suggested production (server) environment runs a [Gunicorn](http://gunicorn.org/) instance managed by [Supervisor](http://supervisord.org/) behind public facing [nginx](http://wiki.nginx.org/Main). That said, other deployments are possible.

Want support for other types of databases? Speak up in the issue tracker and, of course, patches are welcome.

<br>

### Environment Setup

Note that you will need to [install Python 3](https://docs.python-guide.org/starting/installation/). Python 2 support was deprecated in September 2020.

* Checkout the repository:
```
$ git clone git@github.com:Samnsparky/cdibase.git
```

* [Optional] The development team suggests using Python's [virtualenv](http://www.virtualenv.org/en/latest/). If you do not already have that installed, use [pip](http://www.pip-installer.org/en/latest/):
```
$ pip install virtualenv
```

* [Optional] Create a new virtual environment:
```
$ cd cdibase
$ virtualenv venv
```

* [Optional] Enter into the virtual environment:
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

At this time, only sqlite databases at ./db/cdi.db are supported. We would love to improve on this so, if you have other types of databases you want to see supported, speak up or submit a patch!

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
$ sqlite3 cdi.db < create_local_db.sql
```

* Create an uploads directory
```
$ cd ..
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
$ sqlite3 cdi.db < create_test_user.sql
```

Use the forgot password feature to get a temporary password for that new user. Please be aware that ```create_test_user.sql``` gives test@example.com full permissions.

Finally, before some features of the application can be used, you will also need to provide YAML descriptions of CDI forms, a CSV of percentile information, and a YAML specification of a presentation format. Examples are available in a [private gist](https://gist.github.com/Samnsparky/db2ac1b742b98f954245).

These can be provided through the edit formats tab or at ```http://127.0.0.1:5000/base/edit_formats```.

<br>

### Deployment / Production Server

You will need to be given the location of the code as well as directory access permissions by the server superuser. After securing that, navigate to the cdibase environment.

The code can be uploaded by pulling from the master branch of the project's repository.
```
$ git pull
```

The suggested deployment is a gunicorn server processes monitored by supervisor. The installation instructions vary by operating system.

However, after setting up the server, reload the application with:
```
$ sudo supervisorctl
supervisor> stop cdibase
cdibase: stopped
supervisor> start cdibase
cdibase: started
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

You may also check type hints with ```$ mypy cdibase.py```. Note that test code does not have type hints.

<br>

### Notes on software architecture

The application consists of models, views (templates), controllers, and utilities. While following MVC, those utilities split out more complex logic not dealing directly with user responses to increase testability. Both can be found in the utilities and controllers directories respectively under the prog_code directory.

<br>

### Standards, Conventions, and State of Development

Ideally future development should follow an 80% unit testing coverage guidelines for the controllers with discretionary unit test coverage for the utilities. Python code should include [epydoc](http://epydoc.sourceforge.net/) inline documentation and should follow [Google's Python Style Guidelines](http://google-styleguide.googlecode.com/svn/trunk/pyguide.html). Note, after the drop of mox, test code is excluded from the style guidelines due to things like line length but conformance is still recommended when convenient.

<br>

### Open Source Libraries Used

The following third party open source libraries are used:

 - [Flask](https://flask.palletsprojects.com/en/1.1.x/) under the [BSD license](https://flask.palletsprojects.com/en/1.1.x/license/)
 - [Flask-Mail](https://flask-mail.readthedocs.io/en/latest/) under the [BSD license](https://github.com/mattupstate/flask-mail/blob/master/LICENSE)
 - [itsdangerous](https://itsdangerous.palletsprojects.com/en/1.1.x/) under the [BSD licnese](https://itsdangerous.palletsprojects.com/en/1.1.x/license/)
 - [Jinja2](https://jinja.palletsprojects.com/en/2.11.x/) under the [BSD license](https://github.com/pallets/jinja/blob/master/LICENSE.rst)
 - [MarkupSafe](https://palletsprojects.com/p/markupsafe/) under the [BSD license](https://palletsprojects.com/license/)
 - [PyYAML](https://pyyaml.org/) under the [MIT license](https://pypi.org/project/PyYAML/)
 - [python-dateutil](https://dateutil.readthedocs.io/en/stable/) under the [Apache v2 license](https://github.com/dateutil/dateutil/blob/master/LICENSE)
 - [Werkzeug](https://palletsprojects.com/p/werkzeug/) under the [BSD license](https://palletsprojects.com/license/)
 - [gunicorn](https://gunicorn.org/) under the [MIT license](https://github.com/benoitc/gunicorn/blob/master/LICENSE)

On the front-end:
 - [bootstrap](https://getbootstrap.com/) under the [MIT license](https://github.com/twbs/bootstrap/blob/main/LICENSE)
 - [d3](https://d3js.org/) under the [BSD license](https://opensource.org/licenses/BSD-3-Clause)
 - [jquery](https://jquery.com/) under the [MIT license](https://jquery.org/license/)
 - [sprintf](http://www.diveintojavascript.com/projects/javascript-sprintf) under the [BSD license](https://opensource.org/licenses/BSD-3-Clause).
