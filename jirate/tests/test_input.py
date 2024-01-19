#!/usr/bin/env python

from jirate.tests import fake_metadata
from jirate.jira_input import transmogrify_input

import os
import time

import pytest

os.environ['TZ'] = 'America/New_York'
time.tzset()


def test_trans_string_reflective():
    # identity
    inp = {'description': 'This is a description'}
    out = {'description': 'This is a description'}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_string_nym():
    # We translate to JIRA field IDs
    inp = {'Description': 'This is a description'}
    out = {'description': 'This is a description'}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_priority():
    inp = {'Priority': 'blocker'}
    out = {'priority': {'name': 'Blocker'}}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_custom_basic():
    inp = {'fixed_in_build': 'build123'}
    out = {'customfield_1234567': 'build123'}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_number():
    inp = {'score': '1'}
    out = {'customfield_1234568': 1.0}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_array_options():
    inp = {'array_of_options': 'One,Two'}
    out = {'customfield_1234569': [{'value': 'One'}, {'value': 'Two'}]}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_array_missing_option():
    with pytest.raises(ValueError):
        transmogrify_input(fake_metadata, **{'option_value': 'One,Two,Three'})


def test_trans_array_versions():
    inp = {'array_of_versions': '1.0.1,1.0.2'}
    out = {'customfield_1234570': [{'name': '1.0.1'}, {'name': '1.0.2'}]}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_array_users():
    inp = {'array_of_users': 'user1,user2'}
    out = {'customfield_1234571': [{'name': 'user1'}, {'name': 'user2'}]}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_array_strings():
    inp = {'array_of_strings': '"string one","string 2"'}
    out = {'customfield_1234572': ['string one', 'string 2']}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_array_groups():
    inp = {'array_of_groups': 'group1,group2'}
    out = {'customfield_1234573': [{'name': 'group1'}, {'name': 'group2'}]}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_array_any():
    inp = {'any_value': 'one,2'}
    out = {'customfield_1234574': 'one,2'}

    assert transmogrify_input(fake_metadata, **inp) == out


# TODO: Fixup date and datetime; these should take various input formats
# but are strings


def test_trans_option():
    inp = {'option_value': 'one'}
    out = {'customfield_1234578': {'value': 'One'}}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_missing_option():
    with pytest.raises(ValueError):
        transmogrify_input(fake_metadata, **{'option_value': 'Four'})


def test_trans_missing_field():
    inp = {'not_a_real_field': 'one'}
    out = {}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_user_value():
    inp = {'User Value': 'user1'}
    out = {'customfield_1234580': 'user1'}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_version_value():
    inp = {'version_value': '1.0.1'}
    out = {'customfield_1234581': {'name': '1.0.1'}}

    assert transmogrify_input(fake_metadata, **inp) == out


def test_trans_missing_version():
    with pytest.raises(ValueError):
        transmogrify_input(fake_metadata, **{'version_value': '999'})
