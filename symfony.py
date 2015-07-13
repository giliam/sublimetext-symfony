import re
import sublime, sublime_plugin

class SymfonyCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		methods_mask = re.compile(r'(public|private|protected) function (\w+)')
		attributes_mask = re.compile(r'(public|private|protected) \$(\w+);')
		class_mask = re.compile(r'^class (\w+)')
		methods = []
		attributes = []
		classes = ["_"]
		methods.append([])
		attributes.append([])
		current_class = "_"

		for line in open(self.view.file_name(),'r'):
			line = line.strip()
			results_methods = methods_mask.match(line)
			results_class = class_mask.match(line)
			results_attributes = attributes_mask.match(line)
			if results_class:
				classes.append(results_class.group(1))
				methods.append([])
				attributes.append([])
			if results_methods:
				methods[len(classes)-1].append(results_methods.group(2))
			if results_attributes:
				attributes[len(classes)-1].append(results_attributes.group(2))
		print(methods)
		print(classes)
		print(attributes)
