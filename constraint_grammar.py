
from nltk import *
import itertools

constraintString = """S [] -> N []
N [] -> N [] N []
N  [] -> i1 [-24:24]
Neighbor [i1 + i2] -> i1 [-2:-1, -1:2] i2 [-2:2] {i1 == (i2 * -1)}
Passing [i1 + i2] -> i1 [-2:2] i2 [-2:2] {abs(i1 + i2) >= 3 }
Appoggiatura [i1 + i2] -> i1 [3:24, -3:-24] i2 [-2:2] {(i1 * i2 < 0)}
Escape [i1 + i2] -> i1 [-2:2] i2 [3:24, -3:-24] {(i1 * i2 < 0)}"""

make_chord_dependent = True

def create_var_string_from_number(num):
	ret_string = str(num)
	ret_string = ret_string.replace('-', 'm')
	return ret_string


class RHSVariable:
	def __init__(self, var_name, var_ranges, append_before='', append_after='', is_literal=False, use_name=False):
		self.var_name = var_name
		self.var_ranges = var_ranges
		self.append_before = append_before
		self.append_after = append_after
		self.is_literal = is_literal
		self.use_name = use_name

	def is_in_range(self, number):
		return any(number in var_range for var_range in self.var_ranges)

	def to_string(self, number):
		ret_string = ''
		if self.use_name is True:
			ret_string = self.var_name
		else:
			# first verify that number is in range
			if not self.is_in_range(number):
				ret_string = ''
			if self.is_literal == False:
				ret_string = create_var_string_from_number(number)
				ret_string = self.append_before + ret_string + self.append_after
			else:
				ret_string = "'" + ret_string + "'"
		return ret_string

# sometimes the left-hand side val is just a string, other times it's a function
class LHSVariable:
	def __init__(self, math_function, name='', use_name=False, append_before='', append_after=''):
		self.math_func = math_function
		self.name = name
		self.append_before = append_before
		self.append_after = append_after
		self.use_name = use_name

	def result_string(self, variables):
		ret_string = ''
		if self.use_name is True:
			ret_string = self.name
		else:
			if self.math_func != None:
				new_lambda = self.math_func
				math_result = new_lambda(*variables)

				# we have to make sure the numbers create valid variable names,
				# which means we can't start with a minus sign
				ret_string = create_var_string_from_number(math_result)

				ret_string = self.append_before + ret_string + self.append_after
			else:
				ret_string = self.name

		return ret_string


class RHSCondition:
	def __init__(self, condition):
		self.condition = condition

	def result(self, *vars):
		return self.condition(*vars)


class ConstraintRule:
	def __init__(self, lhs_var, rhs_vars, rhs_conditions):
		self.lhs_var = lhs_var
		self.rhs_vars = rhs_vars
		self.rhs_conditions = rhs_conditions

	def generate_rule_string(self):
		rhs_ranges = []
		# get a flattened list of the range for each variable
		for rhs in self.rhs_vars:
			rhs_ranges.append([i for var_range in rhs.var_ranges for i in var_range])

		# get all the cartesian products of the numbers in each range
		rhs_combos = [i for i in itertools.product(*rhs_ranges)]
		rhs_conditions_satisfied = [True] * len(rhs_combos)
		valid_combos = rhs_combos
		# apply all the conditions
		for condition in self.rhs_conditions:
			valid_combos = [(x, y) for x,y in valid_combos if condition(x,y)]

		print(valid_combos)

		# now create the rule string for each valid right-hand side
		rule_strings = []
		for combo in valid_combos:
			lhs_string = self.lhs_var.result_string(combo)
			rhs_string = ''
			for idx, val in enumerate(combo):
				rhs_string += self.rhs_vars[idx].to_string(val) + ' '
			rule_strings.append(lhs_string + ' -> ' + rhs_string)
		return rule_strings

class ConstraintGrammar:
	def __init__(self, constraint_rules):
		self.rules = constraint_rules

	def generate_grammar_string(self):
		grammar_string = ''
		for rule in self.rules:
			rule_strings = rule.generate_rule_string()
			for rule_string in rule_strings:
				grammar_string += rule_string
				grammar_string += '\n'
		return grammar_string


def createFunctionStringFromFormula(formula, functionName):
	if len(formula) == 0 or formula == None:
		return None, None
	# print(formula)
	vars = re.findall('([a-zA-Z_][a-zA-Z0-9_]*)', formula)
	# get unique variable names
	varSet = set(vars)
	# this is hacky. I should instead create a more sophisticated regex that makes sure
	# that the variable names aren't actually function names by ensuring they're not followed by a parenthesis
	for var in varSet:
		if var == 'abs':
			varSet.remove('abs')
			break
	functionString = 'def ' + functionName + '('
	for var in varSet:
		functionString += var + ','
	if len(varSet) > 0:
		# remove trailing comma, add rest of line
		functionString = functionString[0:-1]
	functionString += '): return (' + formula + ')'
	functionString = 'conditionResult = ' + formula
	# print(functionString)
	return functionString, varSet

def processLHS(lhsString):
	functionName = 'lhsResult'
	formula = re.findall('\[(.*)\]', lhsString)
	print ('found formula:')
	print (formula)
	return createFunctionStringFromFormula(formula[0], functionName)

def parseRange(rangeString):
	# rangeString = re.strip(' ', rangeString)
	nums = re.split(':', rangeString)
	if len(nums) < 2:
		return None
	return int(nums[0]), int(nums[1])

def processRHS(rhsString):
	functionName = 'rhsResult'
	varsAndRanges = re.findall('(\w+) \[(.*?)\]', rhsString)
	rangeMap = {}
	for varAndRange in varsAndRanges:
		# print(varAndRange)
		if len(varAndRange) < 2:
			print ('Error')
			return None
		ranges = re.split(',', varAndRange[1])
		rangeNums = []
		# print(ranges)
		for range in ranges:
			parsedRange = parseRange(range)
			# print ('parsed range is ')
			# print(parsedRange)
			rangeNums.append(parseRange(range))
		rangeMap[varAndRange[0]] = rangeNums

	conditionFunctionStrings = []
	conditionCommas = re.findall('\{(.*)\}', rhsString)

	if conditionCommas != None and len(conditionCommas) > 0:
		# print(conditionCommas)
		conditions = re.split(',', conditionCommas[0])
		for condition in conditions:
			conditionFunctionStrings.append(createFunctionStringFromFormula(condition, 'rhsCondition'))
	# print(conditionFunctionStrings)
	return rangeMap, conditionFunctionStrings



	# return createFunctionStringFromFormula(formula, functionName)

# ConstraintRule = collections.namedtuple('ConstraintRule', ['label', 'resultFunctionName', 'resultFunctionParamOrder', 'var1', 'var2', 'constraintFunctionStrings', 'constraintFunctionVars'])
# All constraint grammar strings must have the following format
# Rule Label [result formula] -> val1 [range1] val2 [range2] ...  {comma-separated constraints on RHS variables}
def generateCFGFromString(constraintGrammarString):
	CFGString = 'S -> N\nN -> N N'
	rules = re.split('\n', constraintGrammarString)
	print(rules)
	terminals = set()
	for rule in rules:
		print('processing rule ' + rule)
		if rule == '':
			continue
		if len(re.split('->', rule)) > 2:
			print('Error')
		[lhs, rhs] = re.split('->', rule)
		# print(rhs)
		print(lhs)
		function, args = processLHS(lhs)
		rangeMap, conditions = processRHS(rhs)
		print('function returned')
		print(function)
		print('rangeMap returned')
		print(rangeMap)
		# create all combinations in the ranges given
		for index, varName in enumerate(rangeMap):
			for index2, otherVar in enumerate(rangeMap):
				if varName == otherVar or index2 < index:
					continue
				firstRange = rangeMap[varName]
				secondRange = rangeMap[otherVar]

				print ('firstrange is')
				print (firstRange)
				print ('secondrange is')
				print (secondRange)
				if firstRange == None:
					print('my error')
				for numRange in firstRange:
					for numRange2 in secondRange:
						if (numRange[1] <  numRange[0]):
							range1 = range(numRange[1], numRange[0] + 1)
						else:
							range1 = range(numRange[0], numRange[1] + 1)
						for i in range1:
							if (numRange2[1] <  numRange2[0]):
								range2 = range(numRange2[1], numRange2[0] + 1)
							else:
								range2 = range(numRange2[0], numRange2[1] + 1)
							print(range2)
							for j in range2:
								meetsAllConditions = False
								for condition in conditions:
									params = {varName : i, otherVar : j}
									print('params are')
									exec(varName + ' = ' + "{:.0f}".format(i))
									exec(otherVar + ' = ' + "{:.0f}".format(j))
									print(params)
									conditionResult = None
									namespace = {}
									exec(condition[0], params)
									meetsThisCondition = params['conditionResult']
									# ideally we would pass the function name back as well, but in this case we've
									# hard-coded it to rhsCondition
									# meetsThisCondition = rhsCondition(**params)

									print ('checking condition')
									print (condition[0])
									print (meetsThisCondition)
									meetsAllConditions = meetsAllConditions or meetsThisCondition
								if meetsAllConditions:
									params = {varName : i, otherVar : j}
									print("exec'ing function: ")
									print(function)

									exec(function, params)
									leftHandResult =  params['conditionResult']
									print ('result was')
									print(leftHandResult)
									varNameSpans = [(varNameMatch.start(0), varNameMatch.end(0)) for varNameMatch in re.finditer(varName, rhs)]
									varNameStart = varNameSpans[0][0]
									print(varNameStart)
									otherVarSpans = [(otherVarMatch.start(0), otherVarMatch.end(0)) for otherVarMatch in re.finditer(otherVar, rhs)]
									otherVarStart = otherVarSpans[0][0]

									leftHandResultIntString = "{:.0f}".format(leftHandResult)
									if leftHandResult < 0:
										leftHandResultIntString = leftHandResultIntString.replace('-', 'm')
									thisRuleString = '\n' + leftHandResultIntString + ' -> '
									varNameIntString = "{:.0f}".format(params[varName])
									if params[varName] < 0:
										varNameIntString = varNameIntString.replace('-', 'm')
									otherVarIntString = "{:.0f}".format(params[otherVar])
									if params[otherVar] < 0:
										otherVarIntString = otherVarIntString.replace('-', 'm')

									if varNameStart < otherVarStart:
										thisRuleString += varNameIntString
										thisRuleString += ' '
										thisRuleString += otherVarIntString
									else:
										thisRuleString += otherVarIntString
										thisRuleString += ' '
										thisRuleString += varNameIntString
									terminals.add(params[varName])
									terminals.add(params[otherVar])
									CFGString += thisRuleString
									print(thisRuleString)
			if function == None:
				firstRange = rangeMap[varName]
				for numRange in firstRange:
					if numRange == None:
						break
					if (numRange[1] <  numRange[0]):
						range1 = range(numRange[1], numRange[0] + 1)
					else:
						range1 = range(numRange[0], numRange[1] + 1)
					for i in range1:
						params = {varName : i}
						varNameIntString = "{:.0f}".format(params[varName])
						if params[varName] < 0:
							varNameIntString = varNameIntString.replace('-', 'm')
						lhsVar = re.findall('([a-zA-Z_][a-zA-Z0-9_]*)', lhs)
						thisRuleString = '\n' + lhsVar[0] + ' -> ' +  varNameIntString
						CFGString += thisRuleString
	print(terminals)
	for terminal in terminals:
		terminalIntString = "\n{:.0f}".format(terminal)
		if terminal < 0:
			terminalIntString = terminalIntString.replace('-', 'm')

		thisRuleString = terminalIntString + " -> '" + "{:.0f}".format(terminal) + "'"
		CFGString += thisRuleString
	print(CFGString)


	parens = re.findall('(\([^()]*\))', constraintGrammarString)

def range_inclusive(start, end):
	return range(start, end+1)

# this function will generate all the necessary rules of a triad
# it will name the rules based on which of the three notes the interval is currently on,
# or has visited. For example, a rule which specifies that the root and third
# has been visited will be named ROOT_THIRD
# The representation chosen notates chord-tones by having a 'c' either before or after
# the interval representation. By default they are added
def generate_triadic_rules(triad_interval_set, append_before='c', append_after='c', consider_two_chord_tones_a_triad=False):
	if len(triad_interval_set) != 3:
		return
	rule_strings = ['S -> ROOT | THIRD | FIFTH']
	interval_names = ['ROOT', 'THIRD', 'FIFTH']


	for idx1, interval1 in enumerate(triad_interval_set):
		cur_name = interval_names[idx1]
		for idx2, interval2 in enumerate(triad_interval_set):
			if interval2 != interval1:
				dest_name = interval_names[idx2]
				positive_jump = ((interval2 + 12) - interval1) % 12
				negative_jump = positive_jump - 12
				pos_jump_str  = create_var_string_from_number(positive_jump)
				neg_jump_str  = create_var_string_from_number(negative_jump)

				#these first set of rule_strings specify that a chord can be created from only a single interval going from any
				#one chord tone to any other chord tone in the chord.
				if consider_two_chord_tones_a_triad is True:
					rule_strings.append(cur_name + ' -> ' + append_before + pos_jump_str + append_after)
					rule_strings.append(cur_name + ' -> ' + append_before + neg_jump_str + append_after)

				rule_strings.append(cur_name + ' -> ' + append_before + pos_jump_str + append_after + ' ' + cur_name + '_' + dest_name)
				rule_strings.append(cur_name + ' -> ' + append_before + neg_jump_str + append_after + ' ' + cur_name + '_' + dest_name)


				prev_visited_note_idx = [triad_interval_set.index(interval) for interval in triad_interval_set if interval != interval1 and interval != interval2]
				prev_name = interval_names[prev_visited_note_idx[0]]
				# these intervals we've computed will also be used for the case where
				# we've visited a certain note in the triad, and need to continue
				rule_strings.append(prev_name + '_' + cur_name + ' -> ' + append_before + pos_jump_str + append_after)
				rule_strings.append(prev_name + '_' + cur_name + ' -> ' + append_before + neg_jump_str + append_after)

				rule_strings.append(prev_name + '_' + cur_name + ' -> ' + append_before + pos_jump_str + append_after + ' ' + dest_name + 'X')
				rule_strings.append(prev_name + '_' + cur_name + ' -> ' + append_before + neg_jump_str + append_after + ' ' + dest_name + 'X')

				rule_strings.append(cur_name + 'X' + ' -> ' + append_before + pos_jump_str + append_after + ' ' + dest_name + 'X')
				rule_strings.append(cur_name + 'X' + ' -> ' + append_before + neg_jump_str + append_after + ' ' + dest_name + 'X')

	for rule_string in rule_strings:
		print(rule_string)
	return rule_strings


def create_grammar():
	rules = []
	# Generate a grammar from the following rules
	# Neighbor-tone rule
	rule_strings = generate_triadic_rules([0, 3, 7])
	left_side = LHSVariable(lambda x, y: x + y )
	right_side = []
	right_side.append(RHSVariable('i1', [list(range_inclusive(-2,-2)), list(range_inclusive(-1,2))], append_before, ''))
	right_side.append(RHSVariable('i2', [list(range_inclusive(-2,2))], '', append_after))
	conditions = [ lambda i1, i2: i1 == (i2 * -1), lambda i1, i2: i1 != 0  ]
	neighbor_rule = ConstraintRule(left_side, right_side, conditions)
	rules.append(neighbor_rule)


	# Escape-tone Rule
	left_side = LHSVariable(lambda x, y: x + y )
	right_side = []
	right_side.append(RHSVariable('i1', [list(range_inclusive(-2,2))], append_before, ''))
	right_side.append(RHSVariable('i2', [list(range_inclusive(-24,-3)), list(range_inclusive(3,24))], '', append_after))
	conditions = [ lambda i1, i2: (i1 * i2) < 0 ]
	escape_rule = ConstraintRule(left_side, right_side, conditions)
	rules.append(escape_rule)

	# Cambiata Rule
	left_side = LHSVariable(lambda x, y: x + y )
	right_side = []
	right_side.append(RHSVariable('i1', [list(range_inclusive(-24,3)), list(range_inclusive(3,24))], append_before, ''))
	right_side.append(RHSVariable('i2', [list(range_inclusive(-2,2))], '', append_after))
	conditions = [ lambda i1, i2: (i1 * i2) < 0 ]
	cambiata_rule = ConstraintRule(left_side, right_side, conditions)
	print ("cambiata_rule")
	rules.append(cambiata_rule)

	# Passing-tone Rule
	left_side = LHSVariable(lambda x, y: x + y )
	right_side = []
	right_side.append(RHSVariable('i1', [list(range_inclusive(-2,2))], append_before, ''))
	right_side.append(RHSVariable('i2', [list(range_inclusive(-2,2))], '', append_after))
	conditions = [ lambda i1, i2: abs(i1 + i2) >= 3]
	passing_rule = ConstraintRule(left_side, right_side, conditions)
	print ("passing_rule")
	rules.append(passing_rule)

	# Repeat Rules with chord_tones
	left_side = LHSVariable(lambda x, y: x + y, '', False, '', append_after)
	right_side = []
	right_side.append(RHSVariable('i1', [list(range_inclusive(0,0))], append_before, append_after))
	right_side.append(RHSVariable('i2', [list(range_inclusive(-24,24))], append_before, ''))
	conditions = []
	repeat_rule1 = ConstraintRule(left_side, right_side, conditions)
	print ("repeat_rule1")
	rules.append(repeat_rule1)

	left_side = LHSVariable(lambda x, y: x + y, '', False, '', append_after)
	right_side = []
	right_side.append(RHSVariable('i1', [list(range_inclusive(-24,24))], '', append_after))
	right_side.append(RHSVariable('i2', [list(range_inclusive(0,0))], append_before, append_after))
	# this condition just ensures that we don't add '0 -> 0 0' twice
	conditions = [ lambda i1, i2: i1 != 0  ]
	repeat_rule2 = ConstraintRule(left_side, right_side, conditions)
	print ("repeat_rule2")
	rules.append(repeat_rule2)

	left_side = LHSVariable(lambda x, y: x + y, '', False, append_before, append_after)
	right_side = []
	right_side.append(RHSVariable('i1', [list(range_inclusive(0,0))], append_before, append_after))
	right_side.append(RHSVariable('i2', [list(range_inclusive(-24,24))], append_before, append_after))
	conditions = []
	repeat_rule3 = ConstraintRule(left_side, right_side, conditions)
	print ("repeat_rule1")
	rules.append(repeat_rule3)

	left_side = LHSVariable(lambda x, y: x + y , '', False, append_before, append_after)
	right_side = []
	right_side.append(RHSVariable('i1', [list(range_inclusive(-24,24))], append_before, append_after))
	right_side.append(RHSVariable('i2', [list(range_inclusive(0,0))], append_before, append_after))
	# this condition just ensures that we don't add '0 -> 0 0' twice
	conditions = [ lambda i1, i2: i1 != 0  ]
	repeat_rule4 = ConstraintRule(left_side, right_side, conditions)
	print ("repeat_rule2")
	rules.append(repeat_rule4)

	harmonic_embellishment_grammar = ConstraintGrammar(rules)
	harmonic_embellishment_grammar.generate_grammar_string()

if __name__ == "__main__":
	append_before = ''
	append_after = ''
	if make_chord_dependent is True:
		append_before = 'c'
		append_after = 'c'

	create_grammar()