"""VBScript builtin date/time functions"""

from ....codegen_state import CodegenState
from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_cdate(cg_state: CodegenState, param_date, /):
    """"""
    print(f"date={repr(param_date)}")


@make_builtin_function
def builtin_date(cg_state: CodegenState, /):
    """"""


@make_builtin_function
def builtin_dateadd(
    cg_state: CodegenState, param_interval, param_number, param_date, /
):
    """"""


@make_builtin_function
def builtin_datediff(
    cg_state: CodegenState,
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
    cg_state: CodegenState,
    param_interval,
    param_date,
    param_firstdayofweek=None,
    param_firstweekofyear=None,
    /,
):
    """"""


@make_builtin_function
def builtin_dateserial(cg_state: CodegenState, param_year, param_month, param_day, /):
    """"""


@make_builtin_function
def builtin_datevalue(cg_state: CodegenState, param_date, /):
    """"""


@make_builtin_function
def builtin_day(cg_state: CodegenState, param_date, /):
    """"""


@make_builtin_function
def builtin_formatdatetime(cg_state: CodegenState, param_date, param_format, /):
    """"""


@make_builtin_function
def builtin_hour(cg_state: CodegenState, param_time, /):
    """"""


@make_builtin_function
def builtin_isdate(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_minute(cg_state: CodegenState, param_time, /):
    """"""


@make_builtin_function
def builtin_month(cg_state: CodegenState, param_date, /):
    """"""


@make_builtin_function
def builtin_monthname(cg_state: CodegenState, param_month, param_abbreviate=None, /):
    """"""


@make_builtin_function
def builtin_now(cg_state: CodegenState, /):
    """"""


@make_builtin_function
def builtin_second(cg_state: CodegenState, param_time, /):
    """"""


@make_builtin_function
def builtin_time(cg_state: CodegenState, /):
    """"""


@make_builtin_function
def builtin_timer(cg_state: CodegenState, /):
    """"""


@make_builtin_function
def builtin_timeserial(
    cg_state: CodegenState, param_hour, param_minute, param_second, /
):
    """"""


@make_builtin_function
def builtin_timevalue(cg_state: CodegenState, param_time, /):
    """"""


@make_builtin_function
def builtin_weekday(cg_state: CodegenState, param_date, param_firstdayofweek=None, /):
    """"""


@make_builtin_function
def builtin_weekdayname(
    cg_state: CodegenState,
    param_weekday,
    param_abbreviate=None,
    param_firstdayofweek=None,
    /,
):
    """"""


@make_builtin_function
def builtin_year(cg_state: CodegenState, param_date, /):
    """"""
