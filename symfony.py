import re
import sublime, sublime_plugin
import os.path, time
import sys

VAR_PLAIN = 0
VAR_ENTITY = 1
TYPE_DEFAULT = [VAR_PLAIN,"unknown"]

CLASS_DEFAULT = "unknown"

RETURN_DEFAULT = [VAR_PLAIN,"void"]

class SymfonyCommand(sublime_plugin.TextCommand):
	def __init__(self, view):
		with open(os.path.dirname(os.path.realpath(__file__)) + '\\Symfony\\data\\test.txt', 'r') as f:
			self.read_data = f.read()
		self.view = view

	def run(self, edit):
		last_modified_time = time.ctime(os.path.getmtime(self.view.file_name()))
		methods_mask = re.compile(r'(public|private|protected) function (\w+)')
		attributes_mask = re.compile(r'(public|private|protected) \$(\w+);')
		type_var_mask = re.compile(r'^\* @var \\?(\w+)')
		type_var_2_mask = re.compile(r'^\* @ORM\\(OneToOne|OneToMany|ManyToOne|ManyToMany)\(targetEntity\="([\\|\w]+)"\,?(.*)\)')
		class_mask = re.compile(r'^class (\w+)')
		return_mask = re.compile(r'^\* @return ([\\|\w]+)')
		methods = []
		attributes = []
		classes = [CLASS_DEFAULT]
		methods.append([])
		attributes.append([])
		current_return = RETURN_DEFAULT
		current_class = CLASS_DEFAULT
		current_type = TYPE_DEFAULT

		for line in open(self.view.file_name(),'r'):
			line = line.strip()
			results_methods = methods_mask.match(line)
			results_class = class_mask.match(line)
			results_attributes = attributes_mask.match(line)
			results_types = type_var_mask.match(line)
			results_types_2 = type_var_2_mask.match(line)
			results_returns = return_mask.match(line)
			if results_class:
				current_class = results_class.group(1).lower()
				classes.append(current_class)
				methods.append([])
				attributes.append([])
			elif results_methods:
				methods[len(classes)-1].append([current_return[0],current_return[1],results_methods.group(2)])
				current_return = RETURN_DEFAULT
			elif results_attributes:
				attributes[len(classes)-1].append([current_type[0],current_type[1],results_attributes.group(2)])
				current_type = TYPE_DEFAULT
			elif results_types:
				current_type = VAR_PLAIN,results_types.group(1).lower()
			elif results_types_2:
				current_type = VAR_ENTITY,results_types_2.group(2).lower().split('\\')[-1]
			elif results_returns:
				r = results_returns.group(1).lower()
				if "\\" in r or r == current_class:
					current_return = VAR_ENTITY,results_returns.group(1).lower().split('\\')[-1]
				else:
					current_return = VAR_PLAIN,results_returns.group(1).lower()
		print(methods)
		print(classes)
		print(attributes)
