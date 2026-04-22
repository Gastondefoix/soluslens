from django import template

register = template.Library()


@register.filter
def gha_fmt(value):
    """Absolute value, no sign — 4 decimal places, Italian comma."""
    if value is None:
        return '—'
    try:
        v = abs(float(value))
        return f"{v:.4f}".replace('.', ',')
    except (TypeError, ValueError):
        return '—'


@register.filter
def saldo_fmt(value):
    """Explicit +/− sign — 4 decimal places, Italian comma. Use ONLY on gha_netto."""
    if value is None:
        return '—'
    try:
        v = float(value)
        return f"{v:+.4f}".replace('.', ',')
    except (TypeError, ValueError):
        return '—'


@register.filter
def co2_fmt(value):
    """Format a kgCO2 value to 2 decimal places."""
    if value is None:
        return '—'
    try:
        v = float(value)
        return f"{v:.2f}".replace('.', ',')
    except (TypeError, ValueError):
        return '—'


@register.filter
def abs_val(value):
    """Return absolute value."""
    try:
        return abs(float(value))
    except (TypeError, ValueError):
        return 0


@register.filter
def max_of(value, arg):
    """Return max of absolute values of value and arg."""
    try:
        return max(abs(float(value)), abs(float(arg)))
    except (TypeError, ValueError):
        return 1


@register.filter
def data_it(value):
    """Format date as DD/MM/YYYY."""
    if value is None:
        return '—'
    try:
        if hasattr(value, 'strftime'):
            return value.strftime('%d/%m/%Y')
        from datetime import datetime
        d = datetime.strptime(str(value), '%Y-%m-%d')
        return d.strftime('%d/%m/%Y')
    except (ValueError, AttributeError):
        return str(value)


@register.filter
def sub(value, arg):
    try:
        return int(value) - int(arg)
    except (TypeError, ValueError):
        return 0
