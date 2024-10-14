# https://learn.microsoft.com/en-us/previous-versions/iis/6.0-sdk/ms524741(v=vs.90)#example-3
codeblock = """<%@ Language= "VBScript" %> 

<html> 
  <head> 
  <title>Example 3</title> 
  </head> 
  <body> 
  <font face="MS Gothic"> 

  <H3>Thank you for your purchase.  Please print this page for your records.</H3> 
  <% 
   'Create some variable. 
   dim saveLocale 
   dim totalBill 

   'Set the variables. 
   saveLocale = GetLocale 
   totalBill = CCur(85.50) 

   'For each of the Locales, format the date and the currency 
   SetLocale("fr") 
   Response.Write"<B>Formatted for French:</B><BR>" 
   Response.Write FormatDateTime(Date, 1) & "<BR>" 
   Response.Write FormatCurrency(totalBill) & "<BR>" 
   SetLocale("de") 
   Response.Write"<B>Formatted for German:</B><BR>" 
   Response.Write FormatDateTime(Date, 1) & "<BR>" 
   Response.Write FormatCurrency(totalBill) & "<BR>" 
   SetLocale("en-au") 
   Response.Write"<B>Formatted for English - Australia:</B><BR>" 
   Response.Write FormatDateTime(Date, 1)& "<BR>" 
   Response.Write FormatCurrency(totalBill) & "<BR>" 

   'Restore the original Locale 
   SetLocale(saveLocale) 
  %> 

  </font> 
  </body> 
  </html>
"""
