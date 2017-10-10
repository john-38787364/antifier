import win32com.client, time
time.sleep(5)
shell = win32com.client.Dispatch("WScript.Shell")
shell.AppActivate("Zwift")
for a in range(1,9):
  shell.SendKeys(a) # CTRL+A may "select all" depending on which window's focused
  time.sleep(2)
#shell.SendKeys("{DELETE}") # Delete selected text?  Depends on context. :P
#shell.SendKeys("{TAB}") #Press tab... to change focus or whatever
