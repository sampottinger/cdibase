"""Logic for rendering views and responding to requests related to user specs.

Logic for rendering rendering views and responding requests related to MCDI
formats, CSV file / archive rendering options, and tables for calculating
participant percentiles.

@author: Sam Pottinger
@license: GNU GPL v2
"""

import os
import urllib

import flask

from ..util import db_util
from ..util import file_util
from ..util import session_util

from ..struct import models

from daxlabbase import app


class Format:
    """Strategy that contains information necessary to manage (CRD) a format.

    Strategy that contains information necessary to create, read, and delete a
    MCDI form, persentation format, or percentile table.
    """

    def __init__(self, upload_type, url_component, load_model_function,
        save_model_function, delete_model_function, model_metadata_class,
        model_full_class, file_extension):
        """Create a new Format management strategy.
        
        @param upload_type: The user-facing description of the appropriate
            upload format.
        @type upload_type: str
        @param url_component: The component of the URL that specifies that this
            this format type is in use.
        @type url_component: str
        @param load_model_function: Function to call to load an existing model
            instance. Should take a URL safe name as its only parameter.
        @type load_model_function: function
        @param save_model_function: Function to save a new format model to the
            application database. Should take a format model instance of type
            model_metadata_class as its only parameter.
        @type save_model_function: function
        @param delete_model_function: Function to delete an existing format
            model from the application database. Should take the format model
            instance of type model_metadata_class as its only parameter.
        @type delete_model_function: function
        @param model_metadata_class: The class representing the metadata (data
            without spec file loaded) for this format.
        @type model_metadata_class: class
        @param model_full_class: The class representing the metadata and spec
            file contents for this format.
        @type model_full_class: class
        @param file_extension: The file extension to use for uploaded files.
        @type file_extension: str
        """
        self.upload_type = upload_type
        self.url_component = url_component
        self.load_model_function = load_model_function
        self.save_model_function = save_model_function
        self.delete_model_function = delete_model_function
        self.model_metadata_class = model_metadata_class
        self.model_full_class = model_full_class
        self.file_extension = file_extension


FORMATS = {
    "mcdi": Format(
        "MCDI",
        "mcdi",
        db_util.load_mcdi_model,
        db_util.save_mcdi_model,
        db_util.delete_mcdi_model,
        models.MCDIFormatMetadata,
        models.MCDIFormat,
        ".yaml"
    ),
    "presentation": Format(
        "Presentation",
        "presentation",
        db_util.load_presentation_model,
        db_util.save_presentation_model,
        db_util.delete_presentation_model,
        models.PresentationFormatMetadata,
        models.PresentationFormat,
        ".yaml"
    ),
    "percentile": Format(
        "Percentile",
        "percentile",
        db_util.load_percentile_model,
        db_util.save_percentile_model,
        db_util.delete_percentile_model,
        models.PercentileTableMetadata,
        models.PercentileTable,
        ".csv"
    )
}


@app.route("/edit_formats")
@session_util.require_login(change_formats=True)
def edit_formats():
    """Index page for changing data management behavior.

    Index page with controls for editing formatting, forms, and percentile
    calculation behavior.

    @return: Rendered page with listing of MCDI formats, options for rendering
        database values as CSV files, and percentile tables.
    @rtype: flask.Response
    """
    return flask.render_template(
        "edit_formats.html",
        cur_page="edit_formats",
        mcdi_formats=db_util.load_mcdi_model_listing(),
        presentation_formats=db_util.load_presentation_model_listing(),
        percentile_tables=db_util.load_percentile_model_listing(),
        **session_util.get_standard_template_values()
    )


@app.route("/edit_formats/<format_type>/_add", methods=["GET", "POST"])
@session_util.require_login(change_formats=True)
def upload_format(format_type):
    """Handler to save a specification.

    format_type == mcdi:
    Handler to save a specification of what a form of the MCDI looks like,
    used in data entry and can be specified when downloading CSV / data
    archives from the application.

    format_type == presentation:
    Controller to handle upload of a specification of what numerical values
    should be used in CSV files returned from the server in place of various raw
    database values.

    format_type == percentile:
    Controller to handle upload of a table of data necessary to calculate
    percentiles for research participants against original MCDI distributions.

    @return: HTML form on GET and redirect on POST.
    @rtype: flask.Response
    """
    request = flask.request

    if not format_type in FORMATS:
        flask.session["error"] = "Invalid format type."
        return flask.redirect("/edit_formats")

    format = FORMATS[format_type]

    # Show form on browser vising page with GET
    if request.method == "GET":
        return flask.render_template(
            "upload_format.html",
            cur_page="edit_formats",
            upload_type=format.upload_type,
            **session_util.get_standard_template_values()
        )

    # Safe file and add record to db
    elif request.method == "POST":
        name = request.form.get("name", "")
        upload = request.files.get("newfile", None)

        if name == "":
            flask.session["error"] = "Name not specified. Please try again."
            return flask.redirect(
                "/edit_formats/%s/_add" % format.url_component)

        if upload == None:
            flask.session["error"] = "Upload not provided. Please try again."
            return flask.redirect(
                "/edit_formats/%s/_add" % format.url_component)

        safe_name = name.replace(" ", "")
        safe_name = urllib.quote_plus(safe_name)

        if format.load_model_function(safe_name) != None:
            flask.session["error"] = "\"%s\" already exists." % name
            return flask.redirect("/edit_formats")

        # Check file upload valid
        if upload and file_util.allowed_file(upload.filename):
            
            # Generate random filename
            filename = file_util.generate_unique_filename(format.file_extension)
            upload.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            
            # Create and save record
            new_model = format.model_metadata_class(name, safe_name, filename)
            format.save_model_function(new_model)
            
            flask.session["confirmation"] = "\"%s\" added." % name
            return flask.redirect("/edit_formats")

    flask.session["error"] = "File upload failed. Please try again."
    return flask.redirect("/edit_formats")


@app.route("/edit_formats/<format_type>/<format_name>/delete")
@session_util.require_login(change_formats=True)
def delete_format(format_type, format_name):
    """

    format_type == mcdi
    Controller to delete an existing registered MCDI format specification.

    format_type == presentation
    Delete one rendering "format" where raw database values are turned into
    numerical values selected by the user.

    format_type == percentile:
    Controller to handle delete of a table of data necessary to calculate
    percentiles for research participants against original MCDI distributions.

    @param format_name: The name of the format to delete.
    @type format_name: str
    @return: Redirect
    @rtype: flask.Response
    """
    if not format_type in FORMATS:
        flask.session["error"] = "Invalid format type."
        return flask.redirect("/edit_formats")

    format = FORMATS[format_type]

    format_model = format.load_model_function(format_name)
    if format_model == None:
        error_msg = "\"%s\" not found. Possibly already deleted." % format_name
        flask.session["error"] = error_msg
        return flask.redirect("/edit_formats")

    filename = os.path.join(app.config["UPLOAD_FOLDER"], format_model.filename)
    os.remove(filename)
    format.delete_model_function(format_model)

    flask.session["confirmation"] = "\"%s\" deleted." % format_name
    return flask.redirect("/edit_formats")


@app.route("/edit_formats/download/<filename>")
@session_util.require_login(change_formats=True)
def uploaded_file(filename):
    """Controller to render an uploaded file.

    @param filename: The name of the uploaded file to retrieve.
    @type filename: str
    @return: File contents
    @rtype: flask.Response
    """
    return flask.send_from_directory(app.config["UPLOAD_FOLDER"], filename)
