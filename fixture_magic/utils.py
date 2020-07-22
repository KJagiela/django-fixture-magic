from django.db import models

from fixture_magic.handlers import (
    prepare_handlers,
    BaseModelHandler
)

serialize_me = []
seen = {}


def reorder_json(data, models, ordering_cond=None):
    """Reorders JSON (actually a list of model dicts).

    This is useful if you need fixtures for one model to be loaded before
    another.

    :param data: the input JSON to sort
    :param models: the desired order for each model type
    :param ordering_cond: a key to sort within a model
    :return: the ordered JSON
    """
    if ordering_cond is None:
        ordering_cond = {}
    output = []
    bucket = {}
    others = []

    for model in models:
        bucket[model] = []

    for object in data:
        if object['model'] in bucket.keys():
            bucket[object['model']].append(object)
        else:
            others.append(object)
    for model in models:
        if model in ordering_cond:
            bucket[model].sort(key=ordering_cond[model])
        output.extend(bucket[model])

    output.extend(others)
    return output


def get_fields(obj):
    try:
        return obj._meta.fields
    except AttributeError:
        return []


def get_m2m(obj):
    try:
        return obj._meta.many_to_many
    except AttributeError:
        return []


def serialize_fully():
    index = 0
    handlers = prepare_handlers()
    default_handler = BaseModelHandler()
    while index < len(serialize_me):
        full_model_name = get_instance_model_full_name(serialize_me[index])
        if full_model_name in handlers:
            handlers[full_model_name].handle(serialize_me[index])
        else:
            default_handler.handle(serialize_me[index])

        index += 1

    serialize_me.reverse()


def add_to_serialize_list(objs):
    for obj in objs:
        if obj is None:
            continue
        if not hasattr(obj, '_meta'):
            add_to_serialize_list(obj)
            continue

        # Proxy models don't serialize well in Django.
        if obj._meta.proxy:
            obj = obj._meta.proxy_for_model.objects.get(pk=obj.pk)
        model_name = getattr(obj._meta, 'model_name',
                             getattr(obj._meta, 'module_name', None))
        key = "%s:%s:%s" % (obj._meta.app_label, model_name, obj.pk)

        if key not in seen:
            serialize_me.append(obj)
            seen[key] = 1


def get_instance_model_full_name(instance):
    return "{}.{}".format(
        instance._meta.app_label,
        instance._meta.model_name
    )
