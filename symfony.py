import re
import sublime, sublime_plugin
import os.path, time
import sys

BENCHMARK_IT = 1
VAL_UNKNOWN = "unknown"
VAR_PLAIN = 0
VAR_ENTITY = 1
TYPE_DEFAULT = [VAR_PLAIN,VAL_UNKNOWN]

CLASS_DEFAULT = VAL_UNKNOWN

RETURN_DEFAULT = [VAR_PLAIN,"void"]

class SymfonyCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        with open(os.path.dirname(os.path.realpath(__file__)) + '\\Symfony\\data\\test.txt', 'r') as f:
            self.read_data = f.read()
        self.view = view

    def run(self, edit):
        last_modified_time = time.ctime(os.path.getmtime(self.view.file_name()))
        l = []
        for i in range(BENCHMARK_IT):
            start = time.time()
            self.analyse()
            end = time.time()
            l.append(end-start)   
        if BENCHMARK_IT > 1:         
            print("Moyenne de " + str(sum(l)/len(l)) + " s")

    def analyse(self):
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

        for line in open(self.view.file_name(),'r'):
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
        print(methods)
        print(classes)
        print(attributes)

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
