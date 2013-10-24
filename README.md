Daxlabbase
===================
Central application for managing [CU Language Project](http://psych.colorado.edu/~colungalab/CULanguage/CU-LANGUAGE.html) MCDI data.


### Authors and License
* (c) 2013 [Sam Pottinger](http://gleap.org).
* (c) 2013 [CU Language Project](http://psych.colorado.edu/~colungalab/CULanguage/CU-LANGUAGE.html) at the [University of Colorado Boulder](http://colorado.edu/).

Released under the [MIT License](http://opensource.org/licenses/MIT).


### Background and Motivation

Daxlabbase affords the CU Language Project a standardized dataset for all child language inventory data regardless of study and the format of the MCDI or equivalent questionnaire used.

This allows lab members to:

* Remotely enter MCDI data directly into Daxlabbase's centralized database.
* Send MCDI forms to parents over email and automatically collect responses securely over the Internet.
* Download existing MCDI data in CSV files using different "presentation formats" that, to support lab members' various custom and commercial software solutions, specifies how standard values like true, false, male, and female are reported in the resulting download.
* Download MCDI data from multiple studies even if different MCDI forms were used, allowing the user to specify if the application should combine all results in a single CSV or if Daxlabbase should render a ZIP archive.
* Fine tune user access control, specifying which lab members should have access to what functionality of the web application.
* Send parent forms through external applications using Daxlabbase's API.


### Technologies Used

Daxlabbase itself is written in [Flask](flask.pocoo.org/) and targets a [sqlite3](www.sqlite.org) database. The production (server) environment runs a [Gunicorn](http://gunicorn.org/) instance managed by [Supervisor](http://supervisord.org/) behind public facing [nginx](http://wiki.nginx.org/Main). The application already withstood [OIT](oit.colorado.edu) security audit and, due to [IRB](http://www.colorado.edu/vcr/irb) restrictions, requires HTTPS. Finally, the project leverages [jQuery](http://jquery.com/), [Jinja2](jinja.pocoo.org), and Google's [pymox](https://code.google.com/p/pymox/) for automated testing.


### Development Environment Setup

New developers should seek access to [Daxlabbase's codebase](https://github.com/Samnsparky/daxlabbase), a git repository hosted privately on GitHub. After gaining access...

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

* Get a copy of ```flask_config.cfg```. This is not included in the GitHub repo for security reasons. It can be found in a previous development environment or on the server itself. As with most Flask applications, flask_config.cfg lives in the root folder of the application.

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


### Downloading a local copy of the production DB

If you elect to use the production DB in your local development environment, be sure to download the uploads directory as well.


### Automated Testing

Run unit tests with:
```
$ python run_test.py
```

You should see output that looks like:
```
$ python run_test.py 

Ran 57 tests in 0.545s 

OK
```


### Local Testing

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


### Notes on software architecture

The application consists of models, views (templates), controllers, and utilities. While following MVC, those utilities split out more complex logic not dealing directly with user responses to increase testability. Both can be found in the utilities and controllers directories respectively under the prog_code directory.


### Standards, Conventions, and State of Development

Ideally future development should follow an 80% unit testing coverage guidelines for the controllers with discretionary unit test coverage for the utilities. Python code should include [epydoc](http://epydoc.sourceforge.net/) inline documentation and should follow [Google's Python Style Guidelines](http://google-styleguide.googlecode.com/svn/trunk/pyguide.html).


### Staging

At this time, this project, unfortunately, does not have a staging server.


### Deployment

You will need to be given the location of the code as well as directory access permissions by the server superuser. After securing that, navigate to the daxlabbase environment.

The code can be uploaded by pulling from the master branch of the project's repository.
```
$ git pull
```

The gunicorn server processes are monitored by supervisor. To reload the new code:
```
$ sudo supervisorctl
supervisor> stop daxlabbase
daxlabbase: stopped
supervisor> start daxlabbase
daxlabbase: started
supervisor> exit
```