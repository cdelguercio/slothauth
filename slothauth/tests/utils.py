from functools import wraps
import json as json_reader


def get_objects(json):
    try:
        objects = json
        if objects is None:
            objects = False
        return objects
    except AttributeError:
        raise Exception('Invalid JSON = "%s"' % json)


# Decorators

def disable_for_loaddata(signal_handler):
    """
    Decorator that turns off signal handlers when loading fixture data.
    """

    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if 'raw' in kwargs and kwargs['raw']:
            return
        signal_handler(*args, **kwargs)
    return wrapper


def verify_json(fn):
    def wrapped(json, *args, **kwargs):
        if not issubclass(json.__class__, (dict, list)):
            raise Exception('''Verify JSON could not find JSON object.  Found:\n\n %s''' % (json,))
        else:
            return fn(json, *args, **kwargs)
    return wrapped


def get_data(fn):
    def wrapped(json, *args, **kwargs):
        json = json_reader.loads(json)
        objects = get_objects(json)
        if objects:
            return fn(json, objects, *args, **kwargs)
    return wrapped


def capture_exception(fn):
    def wrapper(obj, against):
        try:
            return fn(obj, against)
        except Exception, e:
            missing = [key for key in against.keys() if not key in obj.keys()]
            extra = [key for key in obj.keys() if not key in against.keys()]
            raise Exception('''%s

                When comparing:
                %s

                ---- against ---

                %s
                -------
                Extra: %s
                Missing: %s
                ''' % (e, obj, against.keys(), extra, missing))
    return wrapper


# Test Functions

def is_none_or(fn):
    def f(x):
        return x is None or x == 'None' or fn(x)
    return f


def is_array(verify_fn):
    def f(data):
        return all([verify_fn(obj) for obj in data])
    return f

is_str = lambda x: issubclass(x.__class__, (str, unicode))
is_int = lambda x: issubclass(x.__class__, int) or (issubclass(x.__class__, str) and x.isdigit())
is_bool = lambda x: issubclass(x.__class__, bool) or x == 'true' or x == 'false'
is_float = lambda x: issubclass(x.__class__, float)
is_date = lambda x: is_int(x)


# Functions to read datasets

@get_data
@verify_json
def obj_is(json, data, verify_fn):
    return verify_fn(data)


@capture_exception
@verify_json
def verify_json_object(obj, against):
    obj_keys = set(obj.keys())
    against_keys = set(against.keys())

    if obj_keys == against_keys:
        for key in obj.keys():
            lam = against[key]
            val = obj[key]
            if not lam(val):
                raise Exception('''Key error for "%s". Value was "%s"''' % (key, val))
    else:
        missing_keys = obj_keys - against_keys
        extra_keys = against_keys - obj_keys
        raise Exception('''Keys were mismatched.
            Missing Keys: %s
            Extra Keys: %s
        ''' % (', '.join(missing_keys), ', '.join(extra_keys)))
    return True
