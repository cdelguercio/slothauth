from .utils import verify_json_object, is_int, is_array, is_float, is_none_or, is_str, is_bool


def is_user_me(obj):
    return verify_json_object(obj, TestDictionaries.user_me)


class TestDictionaries(object):
    # These objects show the JSON formatting of API endpoint responses

    user_me = {
        'id': is_int,
        'first_name': is_str,
        'last_name': is_str,
        'email': is_str,
        'auth_token': is_str,
    }
