import re
import sublime, sublime_plugin
import os.path, time
import sys

VAR_PLAIN = 0
VAR_ENTITY = 1
TYPE_INIT = [VAR_PLAIN,"unknown"]

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
		methods = []
		attributes = []
		classes = ["_"]
		methods.append([])
		attributes.append([])
		current_class = "_"
		current_type = TYPE_INIT

		for line in open(self.view.file_name(),'r'):
			line = line.strip()
			results_methods = methods_mask.match(line)
			results_class = class_mask.match(line)
			results_attributes = attributes_mask.match(line)
			results_types = type_var_mask.match(line)
			results_types_2 = type_var_2_mask.match(line)
			if results_class:
				classes.append(results_class.group(1))
				methods.append([])
				attributes.append([])
			elif results_methods:
				methods[len(classes)-1].append(results_methods.group(2))
			elif results_attributes:
				attributes[len(classes)-1].append([current_type[0],current_type[1],results_attributes.group(2)])
				current_type = TYPE_INIT
			elif results_types:
				current_type = VAR_PLAIN,results_types.group(1).lower()
			elif results_types_2:
				current_type = VAR_ENTITY,results_types_2.group(2).lower().split('\\')[-1]
		print(methods)
		print(classes)
		print(attributes)
