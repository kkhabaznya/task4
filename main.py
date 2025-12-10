from lark import Lark, Transformer, UnexpectedToken, UnexpectedCharacters, UnexpectedEOF
import yaml
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('-f','--file_path',default='data',type=str)
args = parser.parse_args()

grammar = '''
start: _NL? (variable|COMMENT)*

variable: "global" name "=" value _NL?
value   : operation
        | string
        | array
        | number
    
name    : /[_a-zA-Z][_a-zA-Z0-9]*/
number  : /[+-]?\d+\.?\d*[eE][+-]?\d+/
array   : "[" [value ("," value)*] "]"
string  : /[\'].[^']*[\']/
COMMENT : "*" /.+/ _NL?

operation   : "@{" oper_type "}"
oper_type   : "+" name number   -> oper_add
            | "-" name number   -> oper_sub
            | "*" name number   -> oper_mul
            | "/" name number   -> oper_div
            | "min" name number -> oper_min
            
%import common.NEWLINE -> _NL
%import common.WS_INLINE
%ignore WS_INLINE
%ignore COMMENT
'''
#"{:e}".format(test)

class TreeToJson(Transformer):
    def start(self, token):
        return token
    def variable(self, token):
        return token
    def value(self, token):
        return token[0]
    def name(self, token):
        return {"name":token[0].value}
    def number(self, token):
        return {"number":token[0].value}
    def string(self, token):
        return {"string":token[0].value[:-1][1:]}
    def array(self, token):
        return {"array":token}
    def operation(self, token):
        return token[0]
    def oper_add(self, token):
        return {"operation":token,"type":"+"}
    def oper_sub(self, token):
        return {"operation":token,"type":"-"}
    def oper_mul(self, token):
        return {"operation":token,"type":"*"}
    def oper_div(self, token):
        return {"operation":token,"type":"/"}
    def oper_min(self, token):
        return {"operation":token,"type":"min"}
    
def ignore_errors(e):
    print(e)
    return True

grammar_parser = Lark(grammar,parser='lalr',transformer=TreeToJson())

variable_list = []

def tryParse(user_input):
    try:
        parsed = grammar_parser.parse(user_input)
    except UnexpectedToken as e:
        print(f"Unexpected token at line {e.line}, column {e.column}. Expected one of: {e.expected}")
        return 0
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 0
    else:
        if user_input != '' and parsed != []:
            parse(parsed[0])

def parse(parsing):
    if recurse(variable_list,"name",parsing[0].get("name")):
        print("error var name already used")
        return 0
    for item in parsing:
        if item.get("operation"):
            result = processFunction(item)
            if result == 0:
                print("error while processing function")
                return 0
            temp_parse = parsing[0]
            parsing = []
            parsing.append(temp_parse)
            parsing.append(result)
    variable_list.append(parsing)
    
def recurse(where,what,exact):
    for item in where:
        if item[0].get(what)==exact:
            return True
    return False

def processFunction(item):
    number_1 = item.get("operation")[0].get("name")
    for thing in variable_list:
        if thing[0].get("name")==number_1:
            if not(thing[1].get("number")):
                print("Error, NaN")
                return 0
            number_1 = float(thing[1].get("number"))
    if type(number_1) != float:
        print("Error, var not found")
        return 0
    number_2 = float(item.get("operation")[1].get("number"))
    match item.get("type"):
        case '+':
            return {"number":"{:e}".format(number_1+number_2)}
        case '-':
            return {"number":"{:e}".format(number_1-number_2)}
        case '/':
            return {"number":"{:e}".format(number_1/number_2)}
        case '*':
            return {"number":"{:e}".format(number_1*number_2)}
        case 'min':
            return "{:e}".format(min(number_1,number_2))
    return {'number':f'result'}

user_input = -1;
while user_input != '':
    print(f"Current variables: {variable_list}")
    user_input = str(input())
    tryParse(user_input)

with open(f'{args.file_path}.yaml', 'w') as file:
    yaml.dump(variable_list, file, default_flow_style=False, indent=4)
