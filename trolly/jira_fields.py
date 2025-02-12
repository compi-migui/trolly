#!/usr/bin/python3

import re  # NOQA
from collections import OrderedDict
from trolly.decor import pretty_date, color_string, vsep_print


#
# Field rendering functions. Return a string, or None if you want the field
# suppressed.
#
def _list_of_key(field, key):
    return ', '.join([item[key] for item in field])


def string(field, fields):
    return field


def key(field, fields):
    return field['key']


def value(field, fields):
    return field['value']


def name(field, fields):
    return field['name']


def user(field, fields):
    return field['displayName'] + ' - ' + field['emailAddress']


def user_list(field, fields):
    return _list_of_key(field, 'emailAddress')


def array(field, fields):
    return ', '.join(field)


def value_list(field, fields):
    return _list_of_key(field, 'value')


def name_list(field, fields):
    return _list_of_key(field, 'name')


def date(field, fields):
    return pretty_date(field)


def _ratio(field, fields):
    if int(field) < 0:
        return None
    return str(field)


def _status_colorized(field, fields):
    return color_string(field['name'], 'white', field['statusCategory']['colorName'])


def _priority(field, fields):
    if field['name'] not in ('Undefined', 'undefined'):
        return field['name']
    return None


def _reporter(field, fields):
    if field['emailAddress'] != fields['creator']['emailAddress']:
        return user(field, fields)
    return None


def _created_updated(field, fields):
    created = pretty_date(field)
    if field != fields['updated']:
        updated = pretty_date(fields['updated'])
        return f'{created} (Updated {updated})'
    return created


def _votes(field, fields):
    if field['votes'] in (0, '0'):
        return None
    return str(field['votes'])


# these can functions can be referenced in custom user
# config files.  These should be generic and should not
# utilize custom fields.
_field_renderers = {
    'string': string,
    'key': key,
    'value': value,
    'name': name,
    'user': user,
    'user_list': user_list,
    'array': array,
    'email_list': user_list,  # Is this duplicate needed?
    'value_list': value_list,
    'name_list': name_list,
    'date': date
}


# Rule of thumb: if it's using an above generic
# renderer, use the key above.  If it's custom
# for that field, use the function. The goal is to
# provide as many generic items as possible to reduce
# the need for config-side rendering via code snippets.
#
# That said, in the config, one can call the functions:
#
#    "code": "name(field, fields)"
#
#     ===
#
#    "display": "name"
#
# 'id': matches your JIRA instance
# 'name': What to display as output when printing
# 'immutable': If True, user configurations cannot
#              overwrite/register handler for this
#              field
# 'display': Omitted: Display the field rendered as a
#                     string
#            False: Do not display this field at all
#            String: Predefined key from above field
#                    renderer table.
# 'code': Should really only be used by custom user
#         configs when here_there_be_dragons is True
#         Note: 'display' supersedes 'code' if both
#         are present.
# 'verbose': if True, Only show this field in
#            verbose mode
#
_base_fields = [
    {
        'id': 'issuetype',
        'name': 'Issue Type',
        'immutable': True,
        'display': 'name'
    },
    {
        'id': 'parent',
        'name': 'Parent',
        'immutable': True,
        'display': 'key'
    },
    {
        'id': 'priority',
        'name': 'Priority',
        'display': _priority
    },
    {
        'id': 'created',
        'name': 'Created',
        'immutable': True,
        'verbose': True,
        'display': _created_updated
    },
    {
        'id': 'duedate',
        'name': 'Due Date',
        'display': 'date'
    },
    {
        # This is part of above.
        'id': 'updated',
        'name': 'Updated',
        'immutable': True,
        'display': False
    },
    {
        'id': 'assignee',
        'name': 'Assignee',
        'display': 'user'
    },
    {
        'id': 'status',
        'name': 'Status',
        'display': _status_colorized
    },
    {
        'id': 'resolution',
        'name': 'Resolution',
        'display': 'name'
    },
    {
        'id': 'resolutiondate',
        'name': 'Resolved',
        'display': 'date'
    },
    {
        'id': 'security',
        'name': 'Security Level',
        'display': 'name'
    },
    {
        'id': 'workratio',
        'name': 'Work Ratio',
        'display': _ratio
    },
    {
        'id': 'creator',
        'name': 'Creator',
        'display': 'user',
        'verbose': True,
    },
    {
        'id': 'reporter',
        'name': 'Reporter',
        'verbose': True,
        'display': _reporter
    },
    {
        'id': 'archivedby',
        'name': 'Archiver',
        'verbose': True,
        'display': 'user'
    },
    {
        'id': 'archiveddate',
        'name': 'Archived',
        'verbose': True,
        'display': 'date'
    },
    {
        'id': 'labels',
        'name': 'Labels',
        'display': 'array',
    },
    {
        'id': 'votes',
        'name': 'Votes',
        'display': _votes
    },
    {
        'id': 'components',
        'name': 'Component(s)',
        'display': 'name_list'
    },
    {
        'id': 'versions',
        'name': 'Affects Version(s)',
        'display': 'name_list'
    },
    {
        'id': 'fixVersions',
        'name': 'Fix Version(s)',
        'display': 'name_list'
    },
]


# Shortcut to avoid making above list enormous
# These are all standard fields we don't presently
# have rendering for, but might in the future.
# Remember ordering matters in above list.  Since
# it "shouldn't" for things we're not printing out,
# alphabetic is fine.
_quiet_fields = [
    'aggregateprogress',
    'aggregatetimeestimate',
    'aggregatetimeoriginalestimate',
    'aggregatetimespent',
    'archivedby',
    'archiveddate',
    'environment',
    'lastViewed',
    'progress',
    'project',
    'reporter',
    'timeestimate',
    'timeoriginalestimate',
    'timespent',
    'timetracking',
    'versions',
    'watches',
    'worklog',
    'workratio'
]

_quiet_fields_applied = False


if not _quiet_fields_applied:
    _quiet_fields_applied = True
    for field in _quiet_fields:
        val = {'id': field, 'name': field, 'display': False}
        _base_fields.append(val)


# These are fields we should never provide
# custom rendering for; they are inherently
# complicated or positional.
_ignore_fields = [
    'attachment',
    'comment',
    'description',
    'issuekey',
    'issuelinks',
    'subtasks',
    'summary',
    'thumbnail'
]


_fields = None


def eval_custom_field(__code__, field, fields):
    # Proof of concept.
    #
    # Only used if 'here_there_be_dragons' is set to true.  Represents
    # an obvious security issue if you are not in control of your
    # trolly configuration file:
    #     "code": "os.system('rm -rf ~/*')"
    #

    # field:    is your variable name for your dict
    # fields:   dict of fields indexed by id
    # __code__: is inline in your config and can reference field
    if field is None or not field:
        return None
    if '__code__' in __code__:
        raise ValueError('Reserved keyword in code snippet')
    try:
        return eval(str(__code__))
    except Exception as e:
        return str(e)


# kinda slow but...
def apply_field_renderers(custom_field_defs=None):
    global _fields
    base_fields = OrderedDict()
    custom_fields = OrderedDict()
    ret = OrderedDict()

    if not custom_field_defs:
        for field in _base_fields:
            if field['id'] in _ignore_fields:
                continue
            ret[field['id']] = field
        _fields = ret
        return

    # First go through base fields
    for field in _base_fields:
        base_fields[field['id']] = field

    # reorder
    for field in custom_field_defs:
        if field['id'] in _ignore_fields:
            continue
        if field['id'] in base_fields:
            bf = base_fields[field['id']]
            if 'immutable' in bf and bf['immutable']:
                custom_fields[field['id']] = bf
                continue
            custom_fields[field['id']] = field
            if 'display' in bf and 'display' not in field:
                custom_fields[field['id']]['display'] = bf['display']
        else:
            custom_fields[field['id']] = field

    for key in base_fields:
        if key not in custom_fields:
            ret[key] = base_fields[key]

    for key in custom_fields:
        ret[key] = custom_fields[key]

    _fields = ret


def render_field_data(field_key, field, fields, verbose=False, allow_code=False):
    if field_key not in _fields:
        return None
    if not field:
        return None
    field_config = _fields[field_key]

    if 'verbose' in field_config:
        if field_config['verbose'] is True and not verbose:
            return None
    if 'disabled' in field_config and field_config['disabled'] is True:
        return None
    # display supersedes code
    if 'display' in field_config:
        r_info = field_config['display']
        if isinstance(r_info, bool):
            return None if not r_info else str(field)
        if isinstance(r_info, str):
            if r_info not in _field_renderers:
                return f'<invalid renderer: {r_info} for {field_key}>'
            else:
                return _field_renderers[r_info](field, fields)
        else:
            return r_info(field, fields)
    if 'code' in field_config and allow_code:
        return eval_custom_field(field_config['code'], field, fields)
    return str(field)


def field_ordering():
    return [_fields.keys()]


def max_field_width(issue, verbose, allow_code):
    width = 0

    for field_key in _fields:
        if field_key not in issue:
            continue
        field = issue[field_key]
        val = render_field_data(field_key, field, issue, verbose, allow_code)
        if not val:
            continue
        width = max(width, len(_fields[field_key]['name']))
    return width


def render_issue_fields(issue, verbose=False, allow_code=False, width=None):
    global _fields

    if not width:
        width = max_field_width(issue, verbose, allow_code)

    for field_key in _fields:
        if field_key not in issue:
            continue
        field = issue[field_key]
        val = render_field_data(field_key, field, issue, verbose, allow_code)
        if not val:
            continue
        vsep_print(' ', _fields[field_key]['name'], width, val)
        # print(_fields[field_key]['name'].ljust(width), sep, val)
