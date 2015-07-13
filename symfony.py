import re
import sublime, sublime_plugin

class SymfonyCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		functions_mask = re.compile(r'(public|private|protected) function (\w+)')
		attributes_mask = re.compile(r'(public|private|protected) \$(\w+);')
		class_mask = re.compile(r'^class (\w+)')
		functions = []
		classes = []
		attributes = []
		display = ""

		for line in open(self.view.file_name(),'r'):
			line = line.strip()
			results_functions = functions_mask.match(line)
			results_class = class_mask.match(line)
			results_attributes = attributes_mask.match(line)
			if results_functions:
				functions.append(results_functions.group(2))
			if results_class:
				classes.append(results_class.group(1))
			if results_attributes:
				attributes.append(results_attributes.group(2))
		print(functions)
		print(classes)
		print(attributes)
