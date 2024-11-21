"""Helper module to import codegen objects in the correct order"""

# pylint: disable=W0401,W0614
#         ~~~~~~~~^^^^^~^^^^^
#         __all__ is specified in the handler modules, so ignore these

# import code generation functions BEFORE everything else
# so that reg_stmt_cg is updated properly
from .handlers import *

# codegen_global_stmt should now use an updated reg_stmt_cg
from .codegen_reg import codegen_global_stmt

__all__ = ["codegen_global_stmt"]
