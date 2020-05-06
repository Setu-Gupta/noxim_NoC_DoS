import os.path

def get_yes_no():
	'''
		Prompts user to enter yes or no
		Args:
			None
		Rets:
			bool (True if yes)
	'''
	yes_values = ['yes', 'y', 'true']
	no_values = ['no', 'n', 'false']
	while(1):

		ans = str(input('Enter > ')).casefold()
		if(ans not in yes_values and ans not in no_values):
			print("Answer yes or no!")	# The user entered invalid input
			continue
		if(ans in no_values):
			return False
		return True

def verify_value(choice, value):
	'''
		Verifies correctness of value w.r.t choice.
		Natural_number_choices will accept integer values >= 0
		Rest of the field will accept decimal values lying in [0,1]
		Args:
			choice and corresponding value
		Rets:
			True or False

	'''
	natural_number_choices = ['t_on', 't_off', 't_period']
	if(choice in natural_number_choices):
		if(not value.isnumeric() or int(value) < 0 ):
			print("Enter a valid value! (Natural number)")
			return False
		return True
	try:	# Control reaches here if choice was not in natural_number choices. Hence begin decimal analysis.
		float(value)
		if(0 <= float(value) <= 1):
			return True
		print("Enter a number between 0 and 1 (inclusive)")
		return False
	except ValueError:
		print("Enter a valid decimal number between 0 and 1")
		return False

def get_value(choice):
	'''
		Prompts user to enter value for the selected choice
		Args:
			choice
		Rets:
			Value (str)
	'''
	value = ''
	exit_codes = ['exit', 'clear']	# If user enters on of these as values, the value is not verified and the function exits
	while(True):
		print("Enter new value or clear to clear selected value or exit")
		value = input('Enter > ').casefold()
		if(value in exit_codes):
			return value
		if(verify_value(choice, value)):
			return value

def get_choice():
	'''
		Prompts user to choose a category
		Args:
			None
		Rets:
			choice (str)
	'''
	choice = ''
	valid_choices = ['pir', 'por', 't_on', 't_off', 't_period', 'exit']
	while(True):
		print("Enter parameter to change:\npir\npor\nt_on\nt_off\nt_period\nor exit")
		choice = str(input('Enter > ')).casefold()
		if choice not in valid_choices:
			print("Error! Incorrect input")
			choice = ''
		else:
			return choice

def print_new_values(value_dict):
	'''
		Prints out formated value of dictionary passed
		Output follows the following pattern
			key	->	Value
		Args:
			value_dict:	Dictionary to print
		Rets:
			Void
	'''
	if(len(value_dict) == 0):
		print("No changes yet!")
		return
	print("Changes to be made:")
	for key in value_dict:
		print(key + '\t->\t' + str(value_dict[key]))

def get_updated_values():
	'''
		Prompts user to enter choices and corresponding values to update
		Args:
			None
		Rets:
			dict with keys corresponding to choice and values corresponding to new value
	'''
	new_values = {}		# Dictionary for updated values

	while(True):
		print("Do you want to change value? Yes or No")
		if(not get_yes_no()):
			return new_values
		choice = get_choice()	# The user wants to modify some values if control reaches here
		if(choice != 'exit'):
			value = get_value(choice)
			if(value != 'exit'):
				if(value == 'clear'):
					if(choice in new_values):
						new_values.pop(choice)
				else:
					new_values[choice] = value
		print_new_values(new_values)

def get_input_file():
	'''
		Prompts user to enter input file path
		Args:
			None
		Rets:
			path (str) (Path is empty if user wants to exit)
	'''
	path = ''
	while(1):
		print("Enter input file path or exit:")
		path = input('Enter > ')
		if(path.casefold() == 'exit'):
			return ''
		if(os.path.isfile(path)):
			print("Found file!")
			return path
		print("Enter a valid path")

def get_output_file():
	'''
		Prompts user to enter output file path
		Args:
			None
		Ret:
			path (str) (Path is empty if user wants to exit)
	''' 
	path = ''
	while(1):
		print("Enter output file path or exit:")
		path = input('Enter > ')
		if(path.casefold() == 'exit'):
			return ''
		if(os.path.isfile(path)):
			print("A file already exists! Do you wanter to overwrite? Yes or No")
			if(get_yes_no()):
				return path
		else:
			os.makedirs(os.path.dirname(path), exist_ok=True)	# Create file directory if one does not exists yet
			return path

def update(ip_file, op_file, new_values):
	'''
		Creates/Modifies op_file with values of ip_file replaced with new_values
		Args:
			ip_file 	: (str)		Input file path
			op_file 	: (str) 	Output file path
			new_values 	: (Dict)	Key->Field, Value->New_Value
		Rets:
			Void
	'''
	indx_of_field = {	# stores the index format of input file
		'src'		: 0,
		'dst'		: 1,
		'pir'		: 2,
		'por'		: 3,
		't_on'		: 4,
		't_off'		: 5,
		't_period'	: 6
	}
	print("Updating from " + ip_file + " to " + op_file + " with:")
	print_new_values(new_values)
	with open(ip_file, 'r') as input_file:
		with open(op_file, 'w') as output_file:
			op_enteries = []	# Stores the lines to be written in output file
			ip_enteries = input_file.readlines()	# Stores the lines read from input file
			for entry in ip_enteries:	# Iterate over every entry in input file
				updated_values = entry.split()	# Stores the new values to be written. Starts by copying old value
				for key in new_values:
					updated_values[indx_of_field[key]] = new_values[key]	# Update entry
				op_enteries.append('\t'.join(updated_values) + '\n')	# Generate string entry for output file
			output_file.writelines(op_enteries)	# Write to output file

def update_values(new_values):
	if(len(new_values) == 0):
		print("Nothing to do. Exiting...")	# No changes are required
		return
	print("Updating files with new values!")
	ip_file = get_input_file()
	if(ip_file != ''):
		op_file = get_output_file()
		if(op_file != 'exit'):
			update(ip_file, op_file, new_values)
			print("Done! Exiting...")
			return
	print("Aborting!")

def main():
	new_values = get_updated_values()
	update_values(new_values)

if __name__ == '__main__':
	main()