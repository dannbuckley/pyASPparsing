from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer


# https://learn.microsoft.com/en-us/previous-versions/iis/6.0-sdk/ms524741(v=vs.90)#example-1
codeblock = """<%@ Language= "VBScript" %> 

<html> 
<head> 
<title>Example 1</title> 
</head> 
<body> 
<font face="MS Gothic"> 

<H1>Welcome to my Home Page</H1> 
<% 
'Create some variables. 
dim strDynamicDate 
dim strDynamicTime 

'Get the date and time. 
strDynamicDate = Date() 
strDynamicTime = Time() 

'Print out a greeting, depending on the time, by comparing the last 2 characters in strDymamicTime to "PM". 
If "PM" = Right(strDynamicTime, 2) Then 
    Response.Write "<H3>Good Afternoon!</H3>" 
Else 
    Response.Write "<H3>Good Morning!</H3>" 
End If 
%> 
Today's date is <%=strDynamicDate%> and the time is <%=strDynamicTime%>  

</font> 
</body> 
</html>
"""


def test_program_ex1():
    with Tokenizer(codeblock, False) as tkzr:
        prog = Program.from_tokenizer(tkzr)
        for act_st, exp_st in zip(
            prog.global_stmt_list,
            [
                ProcessingDirective,
                OutputText,
                VarDecl,
                VarDecl,
                AssignStmt,
                AssignStmt,
                IfStmt,
                OutputText,
            ],
        ):
            assert isinstance(act_st, exp_st)
