""" Custom Errors """


class UnsupportedRecurrence(Exception):

    def __init__(self, date_string):
        super().__init__('Unsupported recurrence: %s' % date_string)
        self.date_string = date_string

