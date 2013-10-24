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


### Technologies Used

Daxlabbase itself is written in [Flask](flask.pocoo.org/) and targets a [sqlite3](www.sqlite.org) database. The production (server) environment runs a [Gunicorn](http://gunicorn.org/) instance managed by [Supervisor](http://supervisord.org/) behind public facing [nginx](http://wiki.nginx.org/Main). The application already withstood [OIT](oit.colorado.edu) security audit and, due to [IRB](http://www.colorado.edu/vcr/irb) restrictions, requires HTTPS. Finally, the project leverages [jQuery](http://jquery.com/), [Jinja2](jinja.pocoo.org), and Google's [pymox](https://code.google.com/p/pymox/) for automated testing.


### Development Environment Setup

New developers should seek access to [Daxlabbase's codebase](https://github.com/Samnsparky/daxlabbase), a git repository hosted privately on GitHub. After gaining access...

Checkout the repository:
```bash
$ 
```


### Automated Testing


### Local Testing


### Standards, Conventions, and State of Development


### Staging


### Deployment
