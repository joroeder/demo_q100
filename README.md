# demo_q100

Description:\
The file "energy_system_model.py" contains the function for building up the oemof model. For running the optimazation model and doing all the post-processing stuff, check the run_model.py file.
\
\
Execution of model:
- copy the default.ini file into your home-directory in the following path: 'oemof/q100_ini'
	Example of path of .ini file: C:\Users\jroeder\oemof\q100_ini; (This is the place where the config file looks for .ini files)
- adapt the path in your personal .ini file (you just copied from the repository) with your personal data-path in the section [paths]:
	data = your/personal/path/starting/from/your/home/directory/
- store all the data (at the moment it is just the test-data_normiert.csv file) in your/personal/path/starting/from/your/home/directory/
- run the run_model.py file
