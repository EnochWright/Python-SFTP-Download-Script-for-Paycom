This python script can be ran to download files from a Paycom SFTP connection. 
It includes the ability to download multiple files (using file name string) and it automatically pulls only the most recent file. 
It then compares the file contents and only if there is a change does it then move the file to a directory (where then you can use other programs or scripts to process the data).
It sends an email when complete to update you on the status of the process.
I have it setup to run daily using Task Scheduler in Microsoft Windows, but it can be ran manually or included in other scripts.
If directories don't exist or if there are problems, the script includes error checking.

This is my first attempt at sharing code I've written, so please let me know if you find it useful or have any ideas for improvements.
Currently I have it download the employee PTO requests daily as well as any employee changes. Both of these files, when updated, are moved to a directory that is digested by our ERP.
I know the use case is limited with this code, but it could be adapted for use with other STFP options.

Thank you!
