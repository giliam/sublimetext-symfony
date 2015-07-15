import re
import sublime, sublime_plugin
import os.path, time
from os import name as osname
import sys
import threading
import json

if osname == 'nt':
    PATH_SLASH = '\\'
else:
    PATH_SLASH = '/'

VOLATILE = True

BENCHMARK_IT = 1
VAL_UNKNOWN = "unknown"
VAR_PLAIN = 0
VAR_ENTITY = 1
TYPE_DEFAULT = [VAR_PLAIN,VAL_UNKNOWN]

CLASS_DEFAULT = VAL_UNKNOWN

RETURN_DEFAULT = [VAR_PLAIN,"void"]

CONTROLLER_FOLDERS = ["Controller"]
ENTITY_FOLDERS = ["Entity"]

ANALYSE_ENTITY = 1
ANALYSE_CONTROLLER = 2
ANALYSE_DEFAULT = ANALYSE_CONTROLLER

class SymfonyscanCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.data = {}
        with open(os.path.dirname(os.path.realpath(__file__)) + PATH_SLASH + 'Symfony' + PATH_SLASH + 'data' + PATH_SLASH + 'last_scan.txt', 'r') as f:
            self.last_scan = json.loads(f.read())
        self.view = view

    def run(self, edit):
        l = []
        for i in range(BENCHMARK_IT):
            start = time.time()
            self.save_file(self.view.file_name())
            end = time.time()
            l.append(end-start)  
        self.save_last_scan_info() 
        if BENCHMARK_IT > 1:         
            print("Moyenne de " + str(sum(l)/len(l)) + " s")

    def save_last_scan_info(self):
        if not VOLATILE:
            with open(os.path.dirname(os.path.realpath(__file__)) + PATH_SLASH + 'Symfony' + PATH_SLASH + 'data' + PATH_SLASH + 'last_scan.txt', 'w') as f:
                json.dump(self.last_scan,f)
        else:
            self.last_scan = {}

    def shorten_filename(self,filename):
        for i in range(10000):
            for f in sublime.active_window().folders():
                nf = f.replace(PATH_SLASH+PATH_SLASH,PATH_SLASH)
                if nf in filename:
                    filename = filename.replace(nf,"")
        return filename.strip(PATH_SLASH).split(".",1)[0]
        # Takes the main part without the \\ at each end
        # Then split it to remove the extension

    def analyse(self,filename,analyse_type):
        if analyse_type == ANALYSE_ENTITY:
            return self.analyse_entity_file(filename)
        elif analyse_type == ANALYSE_CONTROLLER:
            return self.analyse_controller_file(filename)

    def save_file(self,filename):
        last_modified_time = time.ctime(os.path.getmtime(filename))
        filenameShort = self.shorten_filename(filename)
        try:
            parent_folder = filenameShort.split(PATH_SLASH)[-2]
        except:
            parent_folder = ""
        filenameShort = filenameShort.replace(PATH_SLASH,"-")
        
        if parent_folder in ENTITY_FOLDERS:
            analyse_type = ANALYSE_ENTITY
        elif parent_folder in CONTROLLER_FOLDERS:
            analyse_type = ANALYSE_CONTROLLER
        else:
            analyse_type = ANALYSE_DEFAULT

        filenameKey = filenameShort
        project_name = sublime.active_window().project_file_name().split(PATH_SLASH)[-1].split(".")[0]
        dir_project_scans = os.path.dirname(os.path.realpath(__file__)) + PATH_SLASH + 'Symfony' + PATH_SLASH + 'data' + PATH_SLASH + project_name
        if not project_name in self.last_scan.keys():
            self.last_scan[project_name] = {}
        if not project_name in self.data.keys():
            self.data[project_name] = {}
        if not os.path.isdir(dir_project_scans):
            os.mkdir(dir_project_scans)
        if filenameKey in self.data[project_name].keys():
            return True
        elif filenameKey in self.last_scan[project_name].keys() and self.last_scan[project_name][filenameKey] >= float(os.path.getmtime(filename)):
            print("Exists and was scanned on the " + time.ctime(self.last_scan[project_name][filenameKey]) + " whereas last modification time of the file is " + time.ctime(os.path.getmtime(filename)))
            return True
        else:
            if not VOLATILE:
                with open(dir_project_scans + PATH_SLASH + filenameKey + '.txt', 'w') as f:
                    self.data[project_name][filenameKey] = self.analyse(filename,analyse_type)
                    json.dump(self.data[project_name][filenameKey],f)
            else:
                print(self.analyse(filename,analyse_type))
            self.last_scan[project_name][filenameKey] = time.time()
            print("Has never been scanned but it's now done !")
            return True

    def analyse_entity_file(self, filename):
        methods_mask = re.compile(r'(public|private|protected) function (\w+)\(([\\|\w|\$|,| ]*)\)')
        attributes_mask = re.compile(r'(public|private|protected) \$(\w+);')
        type_var_mask = re.compile(r'^\* @var \\?(\w+)')
        type_var_2_mask = re.compile(r'^\* @ORM\\(OneToOne|OneToMany|ManyToOne|ManyToMany)\(targetEntity\="([\\|\w]+)"\,?(.*)\)')
        class_mask = re.compile(r'^class (\w+)')
        return_mask = re.compile(r'^\* @return ([\\|\w]+)')
        param_mask = re.compile(r'^\* @param ([\\|\w]+) \$(\w+)')
        functions_return_mask = re.compile(r'^return \$this->(\w+);')
        methods = []
        attributes = []
        classes = [CLASS_DEFAULT]
        methods.append([])
        attributes.append([])
        current_return = RETURN_DEFAULT
        current_class = CLASS_DEFAULT
        current_type = TYPE_DEFAULT
        they_need_a_guess = []
        needs_a_guess = False

        for line in open(filename,'r'):
            n = len(classes)-1
            line = line.strip()
            results_methods = methods_mask.match(line)
            results_class = class_mask.match(line)
            results_attributes = attributes_mask.match(line)
            results_types = type_var_mask.match(line)
            results_types_2 = type_var_2_mask.match(line)
            results_returns = return_mask.match(line)
            results_functions_returns = functions_return_mask.match(line)
            if False:
                results_params = param_mask.match(line)

            if results_class:
                current_class = results_class.group(1).lower()
                classes.append(current_class)
                n += 1
                methods.append({})
                attributes.append({})
            
            elif results_methods:
                needs_a_guess=False
                current_function = results_methods.group(2).lower()
                if current_return[1] == "collection":
                    they_need_a_guess.append([len(methods[n]),current_function])
                    needs_a_guess=True
                methods[n][current_function] = [current_return[0],current_return[1],current_function,self.parse_function_prototype(results_methods.group(3).lower())]
                current_return = RETURN_DEFAULT
            
            elif results_attributes:
                attribute = results_attributes.group(2).lower()
                attributes[n][attribute] = [current_type[0],current_type[1],attribute]
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

            elif False and results_params:
                r = results_params.group(1).lower()
                if "\\" in r or r == current_class:
                    current_return = VAR_ENTITY,results_returns.group(1).lower().split('\\')[-1]
                else:
                    current_return = VAR_PLAIN,results_returns.group(1).lower()
            
            elif results_functions_returns and needs_a_guess:
                attribute_name = results_functions_returns.group(1)
                if attribute_name in attributes[n].keys():
                    methods[n][current_function][1] = attributes[n][attribute_name][1]
                    needs_a_guess = False
                    they_need_a_guess.pop()
                else: # The param has not yet been registered
                    methods[n][current_function][0] = VAR_PLAIN
                    methods[n][current_function][1] = attribute_name
        for guess_need in they_need_a_guess:
            if methods[n][guess_need[1]][1] in attributes[n].keys():
                methods[n][guess_need[1]][0] = attributes[n][methods[n][guess_need[1]][1]][0]
                methods[n][guess_need[1]][1] = attributes[n][methods[n][guess_need[1]][1]][1]
        return {"classes":classes,"attributes":attributes,"methods":methods}

    def analyse_controller_file(self, filename):
        functions_mask = re.compile(r'(public|private|protected) function (\w+)\(([\\|\w|\$|,| ]*)\)')
        variables_mask = re.compile(r'^\$([\w|_]+) ?= ?\$(.+);$')
        methods = {}
        variables = {}
        current_function = VAL_UNKNOWN

        for line in open(filename,'r'):
            line = line.strip()
            results_functions = functions_mask.match(line)
            results_variables = variables_mask.match(line)
            if results_functions:
                current_function = results_functions.group(2).lower()
                methods[current_function] = [current_function,self.parse_function_prototype(results_functions.group(3).lower())]
                variables[current_function] = {}
            elif results_variables:
                variable_name = results_variables.group(1)
                variables[current_function][variable_name] = []
                definition = results_variables.group(2)
                if "->" in definition:
                    definition_informations = definition.split("->")
                    if definition_informations[0] == "manager":
                        entity_mask = re.match(r'^getRepository\(\'(\w+):(\w+)\'\)$',definition_informations[1])
                        if entity_mask:
                            variables[current_function][variable_name].append([entity_mask.group(2)])
                    elif definition_informations[0] == "this":
                        if "getUser" in definition_informations[1]:
                            variables[current_function][variable_name].append(["utilisateur"])

        #return {"methods":methods}

    def parse_function_prototype(self,prototype_raw):
        parameters = prototype_raw.split(",")
        prototype_out = []
        for parameter in parameters:
            l = parameter.split(" ")
            if len(l) == 2:
                prototype_out.append([VAR_ENTITY,l[0].split("\\")[-1],l[1]])
            else:
                prototype_out.append([VAR_PLAIN,VAL_UNKNOWN,l[-1]])
        return prototype_out


class SymfonyAutoComplete(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        current_file = view.file_name()
        completions = self.get_autocomplete_list(prefix)
        completions = list(set(completions))
        completions.sort()
        return (completions,sublime.INHIBIT_EXPLICIT_COMPLETIONS)

    def get_autocomplete_list(self, word):
        autocomplete_list = []
        with open(os.path.dirname(os.path.realpath(__file__)) + '\\Symfony\\data\\test.txt', 'r') as f:
            data = json.loads(f.read())
        return autocomplete_list
#class SymfonyCollectorThread(threading.Thread):