"""vCenter AlarmManager (SOAP).

REST doesn't expose alarm definition authoring — only consumption via VCF
Operations. This module wraps the SOAP AlarmManager so users can manage
vCenter alarms declaratively.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def list_(opts, entity=None, profile=None):
    """List alarms. Optionally scoped to *entity* (a managed object reference).

    Returns a list of dicts with ``key``, ``name``, ``description``,
    ``enabled``, ``info``.
    """
    am = soap.alarm_manager(opts, profile=profile)
    target = entity if entity is not None else soap.root_folder(opts, profile=profile)
    alarms = am.GetAlarm(entity=target)
    return [_alarm_to_dict(a) for a in alarms]


def get(opts, name, profile=None):
    """Return the alarm whose ``info.name`` matches *name*, or None."""
    for alarm in list_(opts, profile=profile):
        if alarm.get("name") == name:
            return alarm
    return None


def get_or_none(opts, name, profile=None):
    return get(opts, name, profile=profile)


def create(opts, name, description, expression, action=None, enabled=True, profile=None):
    """Create an alarm at the root folder.

    *expression* is a :class:`vim.alarm.AlarmExpression` instance (e.g.
    :class:`vim.alarm.EventAlarmExpression` or :class:`vim.alarm.MetricAlarmExpression`).
    *action* is an optional :class:`vim.alarm.AlarmAction` instance.
    """
    am = soap.alarm_manager(opts, profile=profile)
    spec = vim.alarm.AlarmSpec()
    spec.name = name
    spec.description = description
    spec.expression = expression
    spec.action = action
    spec.enabled = enabled
    root = soap.root_folder(opts, profile=profile)
    return am.CreateAlarm(entity=root, spec=spec)._moId


def update(
    opts,
    alarm_mo_id,
    name=None,
    description=None,
    expression=None,
    action=None,
    enabled=None,
    profile=None,
):
    """Reconfigure an alarm by its managed-object id."""
    si = soap.get_service_instance(opts, profile=profile)
    alarm = vim.alarm.Alarm(alarm_mo_id, si._stub)
    spec = vim.alarm.AlarmSpec()
    spec.name = name if name is not None else alarm.info.name
    spec.description = description if description is not None else alarm.info.description
    spec.expression = expression if expression is not None else alarm.info.expression
    spec.action = action if action is not None else alarm.info.action
    spec.enabled = enabled if enabled is not None else alarm.info.enabled
    alarm.ReconfigureAlarm(spec=spec)


def delete(opts, alarm_mo_id, profile=None):
    si = soap.get_service_instance(opts, profile=profile)
    alarm = vim.alarm.Alarm(alarm_mo_id, si._stub)
    alarm.RemoveAlarm()


def _alarm_to_dict(alarm):
    info = alarm.info
    entity = info.entity
    return {
        "key": alarm._moId,
        "name": info.name,
        "description": info.description,
        "enabled": info.enabled,
        "system_name": info.systemName,
        "entity_id": entity._moId if entity is not None else None,
    }
