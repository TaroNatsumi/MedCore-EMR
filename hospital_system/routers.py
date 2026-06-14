class HospitalRouter:
    """
    A simple router to direct database operations to the correct
    isolated database for each application.
    """
    route_app_labels = {'employees', 'patients', 'records'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'employees':
            return 'employees_db'
        elif model._meta.app_label == 'records':
            return 'temp_db'
        elif model._meta.app_label == 'patients':
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'employees':
            return 'employees_db'
        elif model._meta.app_label == 'records':
            return 'temp_db'
        elif model._meta.app_label == 'patients':
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'employees':
            return db == 'employees_db'
        elif app_label == 'records':
            return db == 'temp_db'
        elif app_label == 'patients':
            return db == 'default'
        return db == 'default'
