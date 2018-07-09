from django import template

def with_plan_repeat(value):
    if value.repeat is not None:
        return '{}_{}'.format(value.tid, value.repeat)
    else:
        return '{}'.format(value.tid)

def with_plan_id_and_repeat(value):
    if value.plan is not None:
        return '{}_{}_{}'.format(value.tid, value.plan.plan_id, value.repeat)
    else:
        return '{}'.format(value.tid)

register = template.Library()
register.filter('with_plan_repeat', with_plan_repeat)
register.filter('with_plan_id_and_repeat', with_plan_id_and_repeat)