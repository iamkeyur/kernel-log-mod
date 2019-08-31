from peewee import *
from playhouse.postgres_ext import DateTimeTZField
import config


db = PostgresqlDatabase(config.DB_NAME, user=config.DB_USER, password=config.DB_PASSWORD, host=config.DB_HOST,
                        port=config.DB_PORT)


class BaseModel(Model):
    class Meta:
        database = db


class Log(BaseModel):
    commit_id = CharField()
    file_path = TextField()
    component = TextField()
    embed_method = TextField()
    change_type = CharField()
    update_type = CharField(null=True)
    content_update_from = TextField(null=True)
    content_update_to = TextField()
    old_log_method = TextField(null=True)
    new_log_method = TextField(null=True)
    old_verb = TextField(null=True)
    new_verb = TextField(null=True)

    def is_type_added(self):
        return self.change_type == LogChangeType.ADDED_WITH_FILE or \
               self.change_type == LogChangeType.ADDED_WITH_METHOD or \
               self.change_type == LogChangeType.ADDED_INSIDE_METHOD

    def is_type_deleted(self):
        return self.change_type == LogChangeType.DELETED_WITH_FILE or \
               self.change_type == LogChangeType.DELETED_WITH_METHOD or \
               self.change_type == LogChangeType.DELETED_INSIDE_METHOD

    def is_type_updated(self):
        return self.change_type == LogChangeType.UPDATED


class LogChangeType(object):
    DELETED_WITH_FILE = 'DELETED_WITH_FILE'
    ADDED_WITH_FILE = 'ADDED_WITH_FILE'
    DELETED_WITH_METHOD = 'DELETED_WITH_METHOD'
    ADDED_WITH_METHOD = 'ADDED_WITH_METHOD'
    DELETED_INSIDE_METHOD = 'DELETED_INSIDE_METHOD'
    ADDED_INSIDE_METHOD = 'ADDED_INSIDE_METHOD'
    UPDATED = 'UPDATED'


class LogUpdateType(object):
    UPDATED_FORMAT = 'UPDATED_FORMAT'
    UPDATED_LOGGING_METHOD = 'UPDATED_LOGGING_METHOD'
    ADDED_TEXT = 'ADDED_TEXT'
    ADDED_VAR = 'ADDED_VAR'
    ADDED_SIM = 'ADDED_SIM'
    DELETED_TEXT = 'DELETED_TEXT'
    DELETED_VAR = 'DELETED_VAR'
    DELETED_SIM = 'DELETED_SIM'
    REPLACED_TEXT = 'REPLACED_TEXT'
    REPLACED_VAR = 'REPLACED_VAR'
    REPLACED_SIM = 'REPLACED_SIM'
    VERBOSITY_UPD = 'VERBOSITY_UPD'
