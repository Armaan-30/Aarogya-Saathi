from datetime import datetime, time, timezone, timedelta
from ..schemas import ReminderStatus

LOCAL_ZONE = timezone(timedelta(hours=5, minutes=30), 'Asia/Kolkata')

def reminder_status(item: dict, completed: bool, now: datetime | None = None) -> dict:
    if completed:
        return ReminderStatus(state='completed').model_dump()
    raw_date = (item.get('date') or '').strip()
    raw_time = (item.get('timing') or '').strip()
    if not raw_date:
        return ReminderStatus(state='unscheduled').model_dump()
    parsed_date = None
    for fmt in ('%Y-%m-%d', '%d %B %Y', '%d %b %Y'):
        try:
            parsed_date = datetime.strptime(raw_date, fmt).date()
            break
        except ValueError:
            continue
    if parsed_date is None:
        return ReminderStatus(state='date_only').model_dump()
    if not raw_time:
        return ReminderStatus(state='date_only').model_dump()
    try:
        parsed_time = time.fromisoformat(raw_time)
    except ValueError:
        return ReminderStatus(state='date_only').model_dump()
    scheduled = datetime.combine(parsed_date, parsed_time, tzinfo=LOCAL_ZONE)
    current = (now or datetime.now(timezone.utc)).astimezone(LOCAL_ZONE)
    state = 'overdue' if scheduled < current else 'today' if scheduled.date() == current.date() else 'upcoming'
    return ReminderStatus(state=state, scheduled_for=scheduled.isoformat()).model_dump()

def care_task_json(task, now: datetime | None = None):
    return {
        'id': task.id,
        'completed': task.completed,
        'item': task.item,
        'reminder': reminder_status(task.item, task.completed, now),
    }
