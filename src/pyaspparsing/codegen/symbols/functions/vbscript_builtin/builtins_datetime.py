"""VBScript builtin date/time functions"""

from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_cdate(param_date, /):
    """"""
    print(f"date={repr(param_date)}")


@make_builtin_function
def builtin_date():
    """"""


@make_builtin_function
def builtin_dateadd(param_interval, param_number, param_date, /):
    """"""


@make_builtin_function
def builtin_datediff(
    param_interval,
    param_date1,
    param_date2,
    param_firstdayofweek=None,
    param_firstweekofyear=None,
    /,
):
    """"""


@make_builtin_function
def builtin_datepart(
    param_interval, param_date, param_firstdayofweek=None, param_firstweekofyear=None, /
):
    """"""


@make_builtin_function
def builtin_dateserial(param_year, param_month, param_day, /):
    """"""


@make_builtin_function
def builtin_datevalue(param_date, /):
    """"""


@make_builtin_function
def builtin_day(param_date, /):
    """"""


@make_builtin_function
def builtin_formatdatetime(param_date, param_format, /):
    """"""


@make_builtin_function
def builtin_hour(param_time, /):
    """"""


@make_builtin_function
def builtin_isdate(param_expression, /):
    """"""


@make_builtin_function
def builtin_minute(param_time, /):
    """"""


@make_builtin_function
def builtin_month(param_date, /):
    """"""


@make_builtin_function
def builtin_monthname(param_month, param_abbreviate=None, /):
    """"""


@make_builtin_function
def builtin_now():
    """"""


@make_builtin_function
def builtin_second(param_time, /):
    """"""


@make_builtin_function
def builtin_time():
    """"""


@make_builtin_function
def builtin_timer():
    """"""


@make_builtin_function
def builtin_timeserial(param_hour, param_minute, param_second, /):
    """"""


@make_builtin_function
def builtin_timevalue(param_time, /):
    """"""


@make_builtin_function
def builtin_weekday(param_date, param_firstdayofweek=None, /):
    """"""


@make_builtin_function
def builtin_weekdayname(
    param_weekday, param_abbreviate=None, param_firstdayofweek=None, /
):
    """"""


@make_builtin_function
def builtin_year(param_date, /):
    """"""
