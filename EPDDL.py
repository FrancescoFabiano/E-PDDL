#!/usr/bin/env python
# Four spaces as indentation [no tabs]

import re
import itertools
from pathlib import Path

from action import Action

class PDDL_Parser:

    SUPPORTED_REQUIREMENTS = [':strips', ':negative-preconditions', ':typing', ':no-duplicates', ':mep']

    #-----------------------------------------------
    # Tokens
    #-----------------------------------------------

    def scan_tokens(self, filename):
        with open(filename,'r') as f:
            # Remove single line comments
            str = re.sub(r';.*$', '', f.read(), flags=re.MULTILINE).lower()
            str = re.sub(r'\[([^[]+)-agent(\s+|)\]', r'[\1]',str,flags=re.MULTILINE)

            nb_rep = 1

            while (nb_rep):
                    (str, nb_rep) = re.subn(r'\((\s|)+\(([^()]+)\)(\s|)+\)', r'\2',str,flags=re.MULTILINE)

            nb_rep = 1

            while (nb_rep):
                (str, nb_rep) = re.subn(r'(\[[^[]+\])\(([^(]+)\)', r'\1\2',str,flags=re.MULTILINE)

        # Tokenize
        stack = []
        list = []
        isBF = 0
        insideBF = 0
        firstAg = 1
        countSqPa = 0
        multi_ag = 0
        Bf_string = ''
        for t in re.findall(r'[()\[\]]|[^\s()\[\]]+', str):
            if t == '(':
                stack.append(list)
                list = []
            elif t == ')':
                if stack:
                    l = list
                    list = stack.pop()
                    list.append(l)
                else:
                    raise Exception('Missing open parentheses')
            elif t == '[':
                firstAg = 1
                insideBF = 1
                Bf_string = 'B('
            elif t == ']':
                insideBF = 0
                Bf_string += ','
                if multi_ag == 1:
                    Bf_string = Bf_string.replace('B(', 'C(')
                list.append(Bf_string)
                multi_ag = 0
            elif insideBF == 1:
                if firstAg == 0:
                    multi_ag = 1
                    Bf_string +=','
                Bf_string +=t
                firstAg = 0
            else:
                list.append(t)
        if stack:
            raise Exception('Missing close parentheses')
        if len(list) != 1:
            raise Exception('Malformed expression')
        return list[0]

    #-----------------------------------------------
    # Parse domain
    #-----------------------------------------------

    def parse_domain(self, domain_filename):
        tokens = self.scan_tokens(domain_filename)
        if type(tokens) is list and tokens.pop(0) == 'define':
            self.domain_name = 'unknown'
            self.requirements = []
            self.types = {}
            self.objects = {}
            self.actions = []
            self.predicates = {}
            while tokens:
                group = tokens.pop(0)
                t = group.pop(0)
                if t == 'domain':
                    self.domain_name = group[0]
                elif t == ':requirements':
                    for req in group:
                        if not req in self.SUPPORTED_REQUIREMENTS:
                            raise Exception('Requirement ' + req + ' not supported')
                    self.requirements = group
                elif t == ':constants':
                    self.parse_objects(group, t)
                elif t == ':predicates':
                    self.parse_predicates(group)
                elif t == ':types':
                    self.parse_types(group)
                elif t == ':action':
                    self.parse_action(group)
                else: self.parse_domain_extended(t, group)
        else:
            raise Exception('File ' + domain_filename + ' does not match domain pattern')

    def parse_domain_extended(self, t, group):
        print(str(t) + ' is not recognized in domain')

    #-----------------------------------------------
    # Parse hierarchy
    #-----------------------------------------------

    def parse_hierarchy(self, group, structure, name, redefine):
        list = []
        while group:
            if redefine and group[0] in structure:
                raise Exception('Redefined supertype of ' + group[0])
            elif group[0] == '-':
                if not list:
                    raise Exception('Unexpected hyphen in ' + name)
                group.pop(0)
                type = group.pop(0)
                if not type in structure:
                    structure[type] = []
                structure[type] += list
                list = []
            else:
                list.append(group.pop(0))
        if list:
            if not 'object' in structure:
                structure['object'] = []
            structure['object'] += list

    def parse_hierarchy_ag(self, group, structure, name, redefine):
        list = []
        while group:
            if redefine and group[0] in structure:
                raise Exception('Redefined supertype of ' + group[0])
            elif group[0] == '-':
                raise Exception('Unexpected hyphen in ' + name)
            else:
                list.append(group.pop(0))
        if list:
            if not 'agent' in structure:
                structure['agent'] = []
            structure['agent'] += list

    #-----------------------------------------------
    # Parse objects
    #-----------------------------------------------

    def parse_objects(self, group, name):
        self.parse_hierarchy(group, self.objects, name, False)

    def parse_agents(self, group, name):
        self.parse_hierarchy_ag(group, self.objects, name, False)

    # -----------------------------------------------
    # Parse types
    # -----------------------------------------------

    def parse_types(self, group):
        self.parse_hierarchy(group, self.types, 'types', True)

    #-----------------------------------------------
    # Parse predicates
    #-----------------------------------------------

    def parse_predicates(self, group):
        for pred in group:
            predicate_name = pred.pop(0)
            if predicate_name in self.predicates:
                raise Exception('Predicate ' + predicate_name + ' redefined')
            arguments = {}
            untyped_variables = []
            while pred:
                t = pred.pop(0)
                if t == '-':
                    if not untyped_variables:
                        raise Exception('Unexpected hyphen in predicates')
                    type = pred.pop(0)
                    while untyped_variables:
                        arguments[untyped_variables.pop(0)] = type
                else:
                    untyped_variables.append(t)
            while untyped_variables:
                arguments[untyped_variables.pop(0)] = 'object'
            self.predicates[predicate_name] = arguments



    #-----------------------------------------------
    # Parse action
    #-----------------------------------------------

    def parse_action(self, group):
        name = group.pop(0)
        if not type(name) is str:
            raise Exception('Action without name definition')
        for act in self.actions:
            if act.name == name:
                raise Exception('Action ' + name + ' redefined')
        parameters = []
        act_type = 'ontic'
        positive_preconditions = []
        negative_preconditions = []
        add_effects = []
        del_effects = []
        f_obs = []
        p_obs = []
        extensions = None
        while group:
            t = group.pop(0)
            if t == ':parameters':
                if not type(group) is list:
                    raise Exception('Error with ' + name + ' parameters')
                parameters = []
                untyped_parameters = []
                p = group.pop(0)
                while p:
                    t = p.pop(0)
                    if t == '-':
                        if not untyped_parameters:
                            raise Exception('Unexpected hyphen in ' + name + ' parameters')
                        ptype = p.pop(0)
                        while untyped_parameters:
                            parameters.append([untyped_parameters.pop(0), ptype])
                    else:
                        untyped_parameters.append(t)
                while untyped_parameters:
                    parameters.append([untyped_parameters.pop(0), 'object'])
            elif t == ':act_type':
                act_type = self.assign_act_type(group.pop(0))
            elif t == ':precondition':
                self.split_predicates(group.pop(0), positive_preconditions, negative_preconditions, name, ' preconditions')
            elif t == ':effect':
                #self.split_effects(group.pop(0), add_effects, del_effects, name, ' effects')
                self.recoursive_reading(group.pop(0), [['']], [['']], 0, add_effects, del_effects, name, ' effects')

            #    print(str([list(i) for i in add_effects]))
            #    print(str([list(i) for i in del_effects]))
            elif t == ':observers':
                #self.read_observer(group.pop(0), f_obs, name, ' agents')
                self.recoursive_reading(group.pop(0), [['']], [['']], 0, f_obs, [], name, ' agents')

            elif t == ':p_observers':
                self.recoursive_reading(group.pop(0), [['']], [['']], 0, p_obs, [], name, ' agents')
            else: extensions = self.parse_action_extended(t, group)
        self.actions.append(Action(name, act_type, parameters, positive_preconditions, negative_preconditions, add_effects, del_effects, f_obs, p_obs, extensions))

    def parse_action_extended(self, t, group):
        print(str(t) + ' is not recognized in action')

    #-----------------------------------------------
    # Parse problem
    #-----------------------------------------------

    def parse_problem(self, problem_filename):
        def frozenset_of_tuples(data):
            return frozenset([tuple(t) for t in data])
        tokens = self.scan_tokens(problem_filename)
        if type(tokens) is list and tokens.pop(0) == 'define':
            self.problem_name = 'unknown'
            self.state = frozenset()
            self.positive_goals = frozenset()
            self.negative_goals = frozenset()
            while tokens:
                group = tokens.pop(0)
                t = group.pop(0)
                if t == 'problem':
                    self.problem_name = group[0]
                elif t == ':domain':
                    if self.domain_name != group[0]:
                        raise Exception('Different domain specified in problem file')
                elif t == ':requirements':
                    pass # Ignore requirements in problem, parse them in the domain
                elif t == ':objects':
                    self.parse_objects(group, t)
                elif t == ':agents':
                    self.parse_agents(group, t)
                elif t == ':init':
                    init = []
                #    tmp_group = []
                #    tmp_group.insert(0, 'and')
                #    tmp_group.insert(1, group)
                    group.insert(0,'and')
                    self.split_predicates(group, init, [], '', 'init')
                    self.state = init
                elif t == ':goal':
                    positive_goals = []
                    negative_goals = []
                    group.insert(0,'and')
                    self.split_predicates(group, positive_goals, negative_goals, '', 'goals')
                    self.positive_goals = positive_goals
                    self.negative_goals = negative_goals
                else: self.parse_problem_extended(t, group)
        else:
            raise Exception('File ' + problem_filename + ' does not match problem pattern')

    def parse_problem_extended(self, t, group):
        print(str(t) + ' is not recognized in problem')

    #-----------------------------------------------
    # Split predicates
    #-----------------------------------------------

    def split_predicates(self, group, positive, negative, name, part):
        if not type(group) is list:
            raise Exception('Error with ' + name + part)
        if group[0] == 'and':
            group.pop(0)
        else:
            group = [group]
        for predicate in group:
            if 'B(' in predicate[0] or 'C(' in predicate[0]:
                if type(predicate[1]) is list:
                    if predicate[1][0] == 'not':
                        if len(predicate[1][1]) > 0:
                            i = 0
                            tmp_predicate=[]
                            tmp_predicate.insert(0,predicate[0])
                            while i < len(predicate[1][1]):
                                if (i == 0):
                                    tmp_predicate.insert(i+1,'!'+predicate[1][1][0])
                                else:
                                    tmp_predicate.insert(i+1,predicate[1][1][i])
                                i = i+1
                            predicate = tmp_predicate
                        else:
                            raise Exception('Expected predicate after a \'not\'')

            if predicate[0] == 'not':
                if len(predicate) != 2:
                    raise Exception('Unexpected not in ' + name + part)
                negative.append(predicate[-1])
            else:
                positive.append(predicate)

    def recoursive_reading(self, body, head_positive, head_negative, subProcedure, positive, negative, name, part):
        if not type(body) is list:
            raise Exception('Error with ' + name + part)

        if body[0] == 'and':
            body.pop(0)
            and_count = 0
            total_body = []
            while and_count < len(body):
                total_body.append(self.recoursive_reading(body[and_count], head_positive, head_negative, subProcedure, positive, negative, name, part))
                and_count = and_count + 1

            #print("Total body: " + str(total_body))
            ret = ([],[])
            for elem in total_body:
                if elem:
                #    print("Elem: " + str(elem))
                    if elem[1] == 0:
                        ret[0].append(elem[0])
                    else:
                        ret[1].append(elem[0])

            return ret


        elif body[0] == 'when':
            body.pop(0)
            condition = body[0]
            body.pop(0)
            #if type(condition) is list:
            if (condition[0] == 'when' or condition[0] == 'forall'):
                raise Exception('Error with ' + name + part + ' you cannot embed other keywords, other than \'and\', in the \'when\' condition')
            elif condition[0] == 'and':
                condition = self.recoursive_reading(condition, [['']], [['']], 1, positive, negative, name, part)
                pos_condition = condition[0]
                neg_condition = condition[1]

            elif condition[0] == 'not':
                condition.pop(0)
                neg_condition = condition
                pos_condition = [['']]

            else:
                pos_condition = [condition]
                neg_condition = [['']]

            rule = body[0]
            body.pop(0)
            if (rule[0] == 'when' or rule[0] == 'forall'):
                raise Exception('Error with ' + name + part + ' you cannot embed other keywords, other than \'and\', in the \'when\' body')

            self.recoursive_reading(rule,pos_condition,neg_condition,subProcedure, positive, negative, name, part)
            return(rule,pos_condition,neg_condition)

        elif body[0] == 'forall':
            if part != ' agents':
                raise Exception('\'Forall\' keyword only implemented for agents')
            else:
                body.pop(0)
                head = body[0]
                body.pop(0)
                #if type(condition) is list:
                if (head[0] == 'when' or head[0] == 'forall' or head[0] == 'and' or head[0] == 'not'):
                    raise Exception('Error with ' + name + part + ' you cannot embed other keywords in the \'forall\' condition')
                else:
                    fa_start = "FASTART"
                    fa_stop = "FASTOP"
                    rule = body[0]
                    body.pop(0)
                    for v in head:
                        if '?' in v:
                            if v in rule:
                                rule[rule.index(v)] =  fa_start + rule[rule.index(v)] + fa_stop
                            elif rule[0] == 'when':
                                parsed_rule = self.recoursive_reading(rule,[['']], [['']], 1, positive, negative, name, part)

                                i = 0
                                while i < 3:
                                    if i > 0:
                                        j = 0
                                        while j < len(parsed_rule[i]):
                                            if v in parsed_rule[i][j]:
                                                parsed_rule[i][j][parsed_rule[i][j].index(v)] =  fa_start + parsed_rule[i][j][parsed_rule[i][j].index(v)] + fa_stop
                                            j = j+1
                                    else:
                                        if v in parsed_rule[i]:
                                            parsed_rule[i][parsed_rule[i].index(v)] =  fa_start + parsed_rule[i][parsed_rule[i].index(v)] + fa_stop
                                    i = i+1
                            else:
                                raise Exception('To many nested command in the agents\' observability')
                            self.recoursive_reading(parsed_rule[0],parsed_rule[1],parsed_rule[2],subProcedure, positive, negative, name, part)

        elif body[0] == 'not':
            if len(body) != 2:
                raise Exception('Unexpected not in ' + name + part)
            if subProcedure == 0:
                negative.append((body[-1], head_positive, head_negative))
            return (body[-1], 1)

        else:
            if subProcedure == 0:
                positive.append((body, head_positive, head_negative))
            return (body, 0)



    def assign_act_type(self, name):
        name = name.lower()
        if name == 'ontic' or name == 'announcement' or name == 'sensing':
            return name.lower()
        else:
            raise Exception('Error with the action type definition. Please select one of the following: \'ontic\', \'sensing\', \'announcement\'')


    #-----------------------------------------------
    # Print EFP
    #-----------------------------------------------
    def print_EFP(self):
        #########File NAME
        output_folder = "out"
        Path(output_folder).mkdir(exist_ok=True)




        file_name = self.domain_name + '_' + self.problem_name
        out = open(output_folder + "/" + file_name+".txt", "w")
        out.write("%This file is automatically generated from an E-PDDL specification and follows the mAp syntax.\n\n")

        #Generate grounded actions and add grounded fluents
        fluents = set()
        ground_actions = []
        for action in parser.actions:
            for act in action.groundify(parser.objects, parser.types,  self.requirements, fluents):
                act_name = act.name
                for parameter in act.parameters:
                    act_name += '_'+parameter
                act.name = act_name
                ground_actions.append(act)
        #########FLuents
        self.generate_fluents_EFP(fluents)
        if '' in fluents:
            fluents.remove('')
        out.write('%%%%%%%%%%%%%%%%%%%%%%%%%    FLUENTS    %%%%%%%%%%%%%%%%%%%%%%%%\n')
        out.write('%Fluents generated from EPDDL by grounding each predicate (and cheking in :init, :goal and actions for extra predicates)\n')
        out.write('%The fluents are lexicographically sorted and printed in sets of 10\n\n')
        out.write('fluent: ')
        fl_count = 0
        for fluent in sorted(fluents):
            out.write(str(fluent))
            if (fl_count != len(fluents)-1):
                if((fl_count+1)%10 == 0):
                    out.write(';\nfluent ')
                else:
                    out.write(', ')
                fl_count +=1

        out.write(';\n\n')
        out.write('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n\n')

        #########Actions Names
        out.write('%%%%%%%%%%%%%%%%%%%%%    ACTIONS\' NAMES    %%%%%%%%%%%%%%%%%%%%%\n')
        out.write('%Actions\' names generated from EPDDL by adding to each action names its grounded predicates\n\n')
        out.write('action: ')
        act_count = 0
        for action in ground_actions:
            out.write(action.name)
            if (act_count != len(ground_actions)-1):
                if((act_count+1)%10 == 0):
                    out.write(';\naction ')
                else:
                    out.write(', ')
                act_count +=1
        out.write(';\n\n')
        out.write('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n\n')

        #########Actions Specifications
        out.write('%%%%%%%%%%%%%%%%%    ACTIONS\' SPECIFICATIONS    %%%%%%%%%%%%%%%%\n')
        out.write('%Actions\' specifications generated from EPDDL by grounding each action\'s definition\n\n')
        for action in ground_actions:
            out.write('%%%Action ' + action.name + '\n\n')
            out.write('executable ' + action.name)
            self.print_precondition_EFP(action, out)
            self.print_effects_EFP(action, out)
            self.print_observers_EFP(action, 1, out)
            self.print_observers_EFP(action, 0, out)
            out.write('\n%%%\n\n')
        out.write('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n\n')

        #########Actions Specifications
        out.write('%%%%%%%%%%%%%%%%%%    INITIAL FLUENTS TRUTH   %%%%%%%%%%%%%%%%%%\n')
        out.write('%Fluents are considered true when are inserted in :init; otherwise are considered false\n\n')
        out.write('%%%True fluents\n')
        out.write('initially ')
        ini_count = 0
        true_fluents = set()
        belief_ini= set()
        temp_ini = list(self.state)
        for index, ini_f in enumerate(temp_ini):
            ini_fs = self.unify_fluent(ini_f)
            if 'B(' in ini_fs or 'C(' in ini_fs:
                belief_ini.add(ini_fs)
            else:
                out.write(ini_fs)
                true_fluents.add(ini_fs)
                if ( (index+1 < len(temp_ini)) and ('B(' not in temp_ini[index+1][0]  and 'C(' not in temp_ini[index+1][0])):
                    out.write(', ')
        out.write(';\n')
        neg_fluents = fluents - true_fluents

        out.write('%%%False fluents\n')
        out.write('initially ')
        ini_count = 0
        for ini_f in neg_fluents:
            out.write('!'+ini_f)
            if (ini_count != len(neg_fluents)-1):
                out.write(', ')
                ini_count+=1
        out.write(';\n')
        out.write('\n')
        out.write('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n\n')


        out.write('%%%%%%%%%%%%%%%%%%    INITIAL BELIEFS TRUTH   %%%%%%%%%%%%%%%%%%\n')
        out.write('%Extracted from the :init field\n\n')
        ini_count = 0
        for ini_bf in belief_ini:
            out.write('initially ')
            out.write(ini_bf)
            if (ini_count != len(belief_ini)-1):
                out.write(';\n')
                ini_count+=1
        out.write(';\n')
        out.write('\n')
        out.write('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n\n')

        out.write('%%%%%%%%%%%%%%%%%%%%%%%%%%    GOALS   %%%%%%%%%%%%%%%%%%%%%%%%%%\n')
        out.write('%The goals of the plan. Each goal is presented separately to ease the reading\n\n')
        for goal_f in self.positive_goals:
            out.write('goal ')
            goal_fs = self.unify_fluent(goal_f)
            out.write(goal_fs + ';\n')

        for goal_f in self.negative_goals:
            out.write('goal ')
            goal_fs = self.unify_fluent(goal_f)
            out.write(goal_fs + ';\n')

        out.write('\n')
        out.write('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n')
        out.close()

    def unify_fluent(self,list):
        fluent = ''
        l = 0
        parCount = 0
        for i in list:
            if 'C(' in i:
                i = i.replace('C(','C([')
                i = i[:-1]
                i = i + '],'

            fluent += (str(i))
            if 'B(' in i or  'C(' in i:
                parCount +=1
                l +=1
            elif l != len(list) -1:
                fluent += '_'
                l +=1
        while parCount != 0:
            fluent +=')'
            parCount -=1
        return fluent

    def generate_fluents_EFP(self, fluents_set):

        for ini_f in self.state:
            fluent = self.unify_fluent(ini_f)
            if 'B(' not in fluent and 'C(' not in fluent:
                fluents_set.add(fluent)

        for goal_f in self.positive_goals:
            fluent = self.unify_fluent(goal_f)
            if 'B(' not in fluent and 'C(' not in fluent:
                fluents_set.add(fluent)

        for goal_f in self.negative_goals:
            fluent = self.unify_fluent(goal_f)
            if 'B(' not in fluent and 'C(' not in fluent:
                fluents_set.add(fluent)

        duplicates = True
        if ':no-duplicates' in self.requirements:
            duplicates = False
        for predicate in self.predicates.items():
            #print('original:' + str(predicate))
            type_map = []
            variables = []
            pred_ini=[]
            pred_ini.append(predicate[0])
            for var in self.predicates[predicate[0]]:
                type = self.predicates[predicate[0]][var]
                #print ('Type: ' + str(type) + ' var: ' + var + ' predicate: ' + predicate[0])
                pred_ini.append(var)
                type_stack = [type]
                items = []
                while type_stack:
                    t = type_stack.pop()
                    if t in parser.objects:
                        items += parser.objects[t]
                    elif t in parser.types:
                        type_stack += parser.types[t]
                    else:
                        raise Exception('Unrecognized type ' + t)
                type_map.append(items)
                variables.append(var)
            for assignment in itertools.product(*type_map):
                if (not duplicates and len(assignment) == len(set(assignment))) or duplicates:
                    #pred = predicate
                    pred = list(pred_ini)
                    iv = 0
                #    print(str(variables))
                #    print(str(assignment))
                    for v in variables:
                        while v in pred:
                            pred[pred.index(v)] = assignment[iv]
                        iv += 1
                    fluent = self.unify_fluent(pred)
                    if 'B(' not in fluent and 'C(' not in fluent:
                        fluents_set.add(fluent)

    def print_precondition_EFP(self,action,out):
        if (len(action.positive_preconditions)+len(action.negative_preconditions) > 0):
            out.write(' if ' )
            #+ str([list(i) for i in action.positive_preconditions]) +  str([list(i) for i in action.negative_preconditions]))
            self.subprint_precondition_EFP(action, 1, out)
            self.subprint_precondition_EFP(action, 0, out)
            out.write(';\n')

    def subprint_precondition_EFP(self,action,is_postive,out):
        positive_pre = True
        if (is_postive == 1):
            preconditions = action.positive_preconditions
        else:
            positive_pre = False
            preconditions = action.negative_preconditions
        count = 0
        for i in preconditions:
            fluent = self.unify_fluent(i)
            if (positive_pre):
                out.write(fluent)
            else:
                out.write('not('+ fluent + ')')
            if (count < len(preconditions)-1) or (positive_pre and len(action.negative_preconditions) > 0):
                out.write(', ')
                count +=1

    def print_effects_EFP(self,action,out):
        if (action.act_type == 'sensing'):
            act_type = ' determines '
        elif (action.act_type == 'announcement'):
            act_type = ' announces '
        else:
            act_type = ' causes '

        if (len(action.add_effects) > 0):
            for i in action.add_effects:
                out.write(action.name + act_type)
                fluent = self.unify_fluent(i[0])
                out.write(fluent)

                self.print_conditions(i[1],i[2],out)

                out.write(';\n')

        if (len(action.del_effects) > 0):
            for i in action.del_effects:
                out.write(action.name + act_type)
                fluent = self.unify_fluent(i[0])
                out.write('not('+ fluent + ')')

                self.print_conditions(i[1],i[2],out)

                out.write(';\n')

    def print_observers_EFP(self,action,fully,out):
        if fully == 1:
            obs_type = ' observes '
            observers = action.observers
        else:
            obs_type = ' aware_of '
            observers = action.p_observers

        if (len(observers) > 0):
            for ags in observers:
                for ag in ags[0]:
                    if 'FASTART' in ag:
                        for agent in self.objects['agent']:
                            tmp_cond = [[]]
                            self.copy_cond_list(ags,tmp_cond)

                            out.write(agent + obs_type + action.name)
                            self.substitute_ag(tmp_cond[1],agent)
                            self.substitute_ag(tmp_cond[2],agent)

                            self.print_conditions(tmp_cond[1],tmp_cond[2],out)
                            out.write(';\n')
                    else:
                        out.write(str(ag) + obs_type + action.name)
                        self.print_conditions(ags[1],ags[2],out)
                        out.write(';\n')

    def copy_cond_list(self, agents, temp):
        i = 0
        while i < len(agents):
            sub_temp = []
            j = 0
            while j < len(agents[i]):
                if i > 0:
                    k = 0
                    sub_sub_temp = []
                    while k < len(agents[i][j]):
                        sub_sub_temp.insert(k,agents[i][j][k])
                        k = k+1
                else:
                    sub_sub_temp = agents[i][j]
                sub_temp.insert(j, sub_sub_temp)
                j = j+1
            temp.insert(i, sub_temp)
            i = i+1

    def substitute_ag(self, conds, agent):
        for cond in conds:
            for elem in cond:
                if 'FASTART' in elem:
                    conds[conds.index(cond)][cond.index(elem)] = re.sub(r'(FASTART\S+FASTOP)', agent ,elem)

    def print_conditions(self,pos_cond,neg_cond,out):
        yet_to_print = 1
        if self.subprint_cond(pos_cond,1,out, yet_to_print) == 1:
            yet_to_print = 0;
        self.subprint_cond(neg_cond,0,out, yet_to_print);

    def subprint_cond(self,conditions,isPos,out, yet_to_print):
        printed = 0
        for condition in conditions:
            if '' in condition:
                condition.remove('')

        for condition in conditions:
            if not condition:
                conditions.remove(condition)

        if conditions:
            count_cond = 0
            if (yet_to_print == 1):
                out.write( ' if ' )
                printed = 1
            else:
                out.write(', ')
            for condition in conditions:
                cond = self.unify_fluent(condition)
                if not isPos:
                    out.write('!')
                out.write(cond)
                if count_cond < len(conditions)-1:
                    out.write(', ')
                    count_cond = count_cond +1

        return printed

#-----------------------------------------------
# Main
#-----------------------------------------------
if __name__ == '__main__':
    import sys, pprint
    domain = sys.argv[1]
    problem = sys.argv[2]
    parser = PDDL_Parser()
#    print('----------------------------')
#    pprint.pprint(parser.scan_tokens(domain))
#    print('----------------------------')
#    pprint.pprint(parser.scan_tokens(problem))
#    print('----------------------------')
    parser.parse_domain(domain)
    parser.parse_problem(problem)
    parser.print_EFP()
    fluents = set()
    print("\nThe file has been correctly converted.")
    print("The resulting file is in the \'out\' folder.\n")
#    print('State: ' + str(parser.state))
#    for act in parser.actions:
#        print(act)
#    for action in parser.actions:
#        for act in action.groundify(parser.objects, parser.types, parser.requirements, fluents):
#            print(act)
#    print('----------------------------')
#    print('Problem name: ' + parser.problem_name)
#    print('Objects: ' + str(parser.objects))
    #print('Predicates: ' + str(parser.predicates)
#    print('State: ' + str(parser.state))
#    print('Positive goals: ' + str(parser.positive_goals))
#    print('Negative goals: ' + str(parser.negative_goals))
