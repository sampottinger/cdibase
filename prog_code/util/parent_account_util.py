from ..struct import models

import db_util
import filter_util
import mail_util
import user_util

MCDI_EMAIL_SUBJECT = 'CU Language Project'

MCDI_EMAIL_TEMPLATE = '''Hello!

Thank you for helping the CU Language Project. Please complete an MCDI for
%s by going to the URL below.

Form URL: %s

Thanks,
Sam
daxlab.colorado.edu
Application Curator
'''

URL_TEMPLATE = 'https://daxlab.colorado.edu/base/parent_mcdi/%s'


class AttributeResolutionResolver:

    def __init__(self):
        self.__target_user = None

    def is_valid_value(self, value):
        return value != None and value != ""

    def set_global_id(self, new_global_id):
        if not self.is_valid_value(new_global_id):
            return

        try:
            new_global_id = int(new_global_id)
        except ValueError:
            return

        child_id_filter = models.Filter("child_id", "eq", new_global_id)
        results = filter_util.run_search_query([child_id_filter], "snapshots")
        if len(results) == 0:
            return

        results.sort(key=lambda x: x.session_date, reverse=True)
        self.__target_user = results[0]

    def set_study_id(self, study, study_id):
        if not self.is_valid_value(study) or not self.is_valid_value(study_id):
            return

        study_filter = models.Filter("study", "eq", study)
        study_id_filter = models.Filter("study_id", "eq", study_id)
        results = filter_util.run_search_query([study_filter, study_id_filter],
            "snapshots")
        if len(results) == 0:
            return

        results.sort(key=lambda x: x.session_date, reverse=True)
        self.__target_user = results[0]

    def fill_field(self, current_value, field_name):
        if self.__target_user == None:
            return current_value
        if not self.is_valid_value(current_value):
            return getattr(self.__target_user, field_name)
        return current_value

    def fill_parent_form_defaults(self, parent_form):
        self.set_global_id(parent_form.database_id)
        self.set_study_id(parent_form.study, parent_form.study_id)

        parent_form.database_id = self.fill_field(
            parent_form.database_id,
            "database_id"
        )
        
        parent_form.study = self.fill_field(
            parent_form.study,
            "study"
        )

        parent_form.study_id = self.fill_field(
            parent_form.study_id,
            "study_id"
        )

        parent_form.gender = self.fill_field(
            parent_form.gender,
            "gender"
        )

        parent_form.birthday = self.fill_field(
            parent_form.birthday,
            "birthday"
        )

        parent_form.items_excluded = self.fill_field(
            parent_form.items_excluded,
            "items_excluded"
        )

        parent_form.extra_categories = self.fill_field(
            parent_form.extra_categories,
            "extra_categories"
        )

        parent_form.languages = self.fill_field(
            parent_form.languages,
            "languages"
        )

        parent_form.num_languages = self.fill_field(
            parent_form.num_languages,
            "num_languages"
        )

        parent_form.hard_of_hearing = self.fill_field(
            parent_form.hard_of_hearing,
            "hard_of_hearing"
        )


def generate_unique_mcdi_form_id():
    found = False
    ret_id = None
    while not found:
        ret_id = user_util.generate_password().lower()
        found = db_util.get_parent_form_by_id(ret_id) == None

    return ret_id


def send_mcdi_email(parent_form):
    form_url = URL_TEMPLATE % parent_form.form_id
    mail_util.send_msg(
        parent_form.parent_email,
        MCDI_EMAIL_SUBJECT,
        MCDI_EMAIL_TEMPLATE % (parent_form.child_name, form_url)
    )
