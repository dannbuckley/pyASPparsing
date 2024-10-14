# https://learn.microsoft.com/en-us/previous-versions/iis/6.0-sdk/ms524741(v=vs.90)#example-4
codeblock = """<%@ Language= "VBScript" %> 

  <html> 
  <head> 
  <title>Example 4</title> 
  </head> 
  <body> 
  <font face="MS Gothic"> 

  <H3>Changing a Customer's Street Address</H3> 
  <% 
   'Create some variables. 
   dim strString 
   dim strSearchFor     ' as a string 
   dim reSearchFor     ' as a regular expression 
   dim strReplaceWith 

   'Set the variables. 
   strString = "Jane Doe<BR>100 Orange Road<BR>Orangeville, WA<BR>98100<BR>800.555.1212<BR>" 
   '   Using a string object 
   strSearchFor = "100 Orange Road<BR>Orangeville, WA<BR>98100" 
   '   Using a regular expression object 
   Set reSearchFor = New RegExp 
   reSearchFor.Pattern = "100 Orange Road<BR>Orangeville, WA<BR>98100" 
   reSearchFor.IgnoreCase = False 

   strReplaceWith = "200 Bluebell Court<BR>Blueville, WA<BR>98200" 

   'Verify that strSearchFor exists... 
   '   using a string object. 
   If Instr(strString, strSearchFor) Then 
     Response.Write "strSearchFor was found in strString<BR>" 
   Else 
     Response.Write "Fail" 
   End If 
   '   using a regular expression object. 
   If reSearchFor.Test(strString) Then 
     Response.Write "reSearchFor.Pattern was found in strString<BR>" 
   Else 
     Response.Write "Fail" 
   End If 

   'Replace the string... 
   Response.Write "<BR>Original String:<BR>" & strString & "<BR>" 
   '   using a string object. 
   Response.Write "String where strSearchFor is replaced:<BR>" 
   Response.Write Replace(strString, strSearchFor, strReplaceWith) & "<BR>" 
   '   using a regular expression object. 
   Response.Write "String where reSearchFor is replaced:<BR>" 
   Response.Write reSearchFor.Replace(strString, strReplaceWith) & "<BR>" 
  %> 

  </font> 
  </body> 
  </html>
"""
