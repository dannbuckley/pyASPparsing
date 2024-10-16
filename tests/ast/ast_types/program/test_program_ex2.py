from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer


# https://learn.microsoft.com/en-us/previous-versions/iis/6.0-sdk/ms524741(v=vs.90)#example-2
codeblock = """<%@ Language= "VBScript" %>  
<html> 
<head> 
<title>Example 2</title> 
</head> 
<body> 
<font face="MS Gothic"> 

<% 
 'Create a variable. 
 dim strTemp 
 dim font1, font2, font3, font, size 

 'Set the variable. 
 strTemp= "BUY MY PRODUCT!" 
 fontsize = 0 

 'Print out the string 5 times using the For...Next loop. 
 For i = 1 to 5 

   'Close the script delimiters to allow the use of HTML code and <%=... 
   %> 
   <table align=center><font size= <%=fontsize%>> <%=strTemp%> </font></table> 
   <% 
   fontsize = fontsize + i 

 Next 

%> 
<table align=center><font size=6><B> IT ROCKS! <B></font></table>
<BR> 

</font> 
</body> 
</html>
"""


def test_program_ex2():
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
                ForStmt,
                OutputText,
            ],
        ):
            assert isinstance(act_st, exp_st)
