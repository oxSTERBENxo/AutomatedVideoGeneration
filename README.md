From inside your project folder:
cd "C:\Users\eva\Desktop\6th semester\Projects\AutomatedVideoGenerator"
Activate venv:
.\.venv\Scripts\activate
python queue_runner.py

To stop it:
New-Item stop.txt

To continue later:
Remove-Item stop.txt
python queue_runner.py