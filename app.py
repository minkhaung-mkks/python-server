from flask import Flask, request, jsonify
from n_funs.n_func import apply_n_func
from flask_cors import CORS
import re

app = Flask(__name__)
allowed_origins = [
    "http://localhost:5174",
    "http://localhost:5173",
]

# Enable CORS for the specified origins
CORS(app, origins=allowed_origins)

def europenize(input_string):
    # Replace periods that are directly before commas, and then replace commas with periods
    input_string = re.sub(r'\.(?=,)', '', input_string)
    return input_string.replace(',', '.')

def americanize(input_string):
    # Remove all commas
    return input_string.replace(',', '')

@app.route('/checkUserAnswer', methods=['POST'])
def check_user_answer():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate the expected keys in the JSON payload
        if 'AI_JSON' not in data or 'userAnswer' not in data:
            return jsonify({"error": "Missing required fields 'AI_JSON' or 'userAnswer'"}), 400
        
        aiJSON = data['AI_JSON']
        user_answer = data['userAnswer']

        if 'n' not in aiJSON or 'ia' not in aiJSON or 'answer' not in aiJSON or 'correctSteps' not in aiJSON:
            return jsonify({"error": "AI_JSON missing required fields 'n', 'ia', 'answer', or 'correctSteps'"}), 400
        
        expected_n = int(aiJSON['n'])
        incorrectAnswers = aiJSON['ia']

        if not isinstance(expected_n, int) or not isinstance(incorrectAnswers, list):
            return jsonify({"error": "'n' should be an integer and 'ia' should be a list"}), 400

        # Generate nAnswers using apply_n_func based on the user's input
        max_nLevel = 4  # max number of available n funcs
        userAnswerEuFormat = europenize(user_answer)
        correctAnswerEuFormat = europenize(aiJSON["answer"])

        generated_answers = apply_n_func(max_nLevel, userAnswerEuFormat)
        nAnswers = apply_n_func(max_nLevel, correctAnswerEuFormat)
        # Initialize the result dictionary
        result = {"answer": "correct"}
        eq = False
        print(eq)
        print(generated_answers)
        print(nAnswers)

        # Compare each level's answer
        for i in range(1, max_nLevel + 1):
            key = f'N{i}'
            print(nAnswers.get(key))
            print(generated_answers.get(key))
            if nAnswers.get(key) == generated_answers.get(key):
                result[key] = "correct"
                print("---------")
                eq = True
            else:
                result[key] = "incorrect"
                if i == expected_n:
                    result["nStatus"] = "failed"
        sa = {
            "steps": aiJSON['correctSteps'],
            "value": user_answer,
            "mistakeStep": 0,
            "nStatus": {"n": expected_n, "status": result.get("nStatus", "correct")},
            "multiStep":True if len( aiJSON['correctSteps']) > 1 else False,
            "hint": ""
        }
        print(sa["hint"])

        if not eq:
            print('--------------')
            result['answer'] = "incorrect"
            for incorrect in incorrectAnswers:
                print(incorrect['hint'])
                if 'value' not in incorrect or 'steps' not in incorrect or 'mistakeStep' not in incorrect:
                    continue  # Skip this incorrect answer if required fields are missing
                result["ia"] ="correct"
                nIa = apply_n_func(max_nLevel, incorrect['value'])
                for i in range(1, max_nLevel + 1):
                    key = f'N{i}'
                    if nIa.get(key) == generated_answers.get(key):
                        result[key] = "correct"
                        eq = True
                    else:
                        result[key] = "incorrect"
                        if i == expected_n:
                            result["ia"] = "failed"
                if eq:
                    sa = {
                        "value": incorrect['value'],
                        "steps": incorrect['steps'],
                        "nStatus": {"n": expected_n, "status": result["ia"]},
                        "mistakeStep": incorrect['mistakeStep'],
                        "hint": incorrect['hint'] or "",
                        "multiStep":True if len( incorrect['steps']) > 1 else False,
                    }
                    break

        if not eq:
            userAnswerAmericanFormat = americanize(user_answer)
            correctAnswerAmericanFormat = americanize(aiJSON["answer"])
            generated_answers = apply_n_func(max_nLevel, userAnswerAmericanFormat)
            nAnswers = apply_n_func(max_nLevel, correctAnswerAmericanFormat)
            # Initialize the result dictionary
            result = {"answer": "correct"}
            eq = False
            print(eq)
            print(generated_answers)
            print(nAnswers)

            # Compare each level's answer
            for i in range(1, max_nLevel + 1):
                key = f'N{i}'
                print(nAnswers.get(key))
                print(generated_answers.get(key))
                if nAnswers.get(key) == generated_answers.get(key):
                    result[key] = "correct"
                    print("---------")
                    eq = True
                else:
                    result[key] = "incorrect"
                    if i == expected_n:
                        result["nStatus"] = "failed"
            sa = {
                "steps": aiJSON['correctSteps'],
                "value": user_answer,
                "mistakeStep": 0,
                "nStatus": {"n": expected_n, "status": result.get("nStatus", "correct")},
                "hint": "",
                "multiStep":True if len( aiJSON['correctSteps']) > 1 else False,
            }
            print(sa["hint"])

            if not eq:
                print('--------------')
                result['answer'] = "incorrect"
                for incorrect in incorrectAnswers:
                    print(incorrect['hint'])
                    if 'value' not in incorrect or 'steps' not in incorrect or 'mistakeStep' not in incorrect:
                        continue  # Skip this incorrect answer if required fields are missing
                    result["ia"] ="correct"
                    nIa = apply_n_func(max_nLevel, incorrect['value'])
                    for i in range(1, max_nLevel + 1):
                        key = f'N{i}'
                        if nIa.get(key) == generated_answers.get(key):
                            result[key] = "correct"
                            eq = True
                        else:
                            result[key] = "incorrect"
                            if i == expected_n:
                                result["ia"] = "failed"
                    if eq:
                        sa = {
                            "value": incorrect['value'],
                            "steps": incorrect['steps'],
                            "nStatus": {"n": expected_n, "status": result["ia"]},
                            "mistakeStep": incorrect['mistakeStep'],
                            "hint": incorrect['hint'] or "",
                            "multiStep":True if len( incorrect['steps']) > 1 else False,
                        }
                        break

        if not eq:
            sa = {
                "value": 'n/a',
                "steps": [{"step": 'none', "explanation": 'none'}],
                "nStatus": {"status": 'failed', "n": 0},
                "mistakeStep": 0,
                "multiStep":False,
                "hint":""
            }
        # print(result)
        # print(sa['nStatus'])
        # print(sa['value'])
        # print(sa['steps'])
        # print(sa['mistakeStep'])
        # print(aiJSON['correctSteps'])
        # print(aiJSON['answer'])
        # print(result['answer'])
        # print(user_answer)
        # print(result)
        print(sa["hint"])
        returnData = {
            "status": result["answer"],
            "nStatus": sa["nStatus"],
            "isShowButton": False if result["answer"] == "correct" and sa['nStatus']['status'] == "failed" or len(aiJSON['correctSteps']) <= 2 else True,
            "correctAnswer": aiJSON['answer'],
            "correctSteps": aiJSON['correctSteps'],
            "selectedAnswer": sa["value"],
            "selectedAnswerSteps": sa["steps"],
            "mistakeStep": sa["mistakeStep"],
            "userAnswer": user_answer,
            "multiStep": sa['multiStep'],
            "stepCount": len(sa['steps']),
            "hint": sa['hint']
        }
        print(returnData)

        return jsonify(returnData), 200

    except KeyError as e:
        print("Key - EXpection")
        print(e)
        dread = {
                
            "status": "incorrect",
            "isShowButton":True,
            "nStatus": {
                    "status":"failed",
                    "n" : expected_n
                },
            "correctAnswer": aiJSON['answer'],
            "correctSteps": aiJSON['correctSteps'],
            "selectedAnswer": "n/a",
            "selectedAnswerSteps": [{"step": 'none', "explanation": 'none'}],
            "mistakeStep": 0,
            "userAnswer": user_answer,
              "multiStep":False,
            "hint":"",
            "stepCount": 0,
        }
        
        return jsonify(dread), 500
    except TypeError as e:
        print("T-EXpection")
        print(e)
        dread = {
                
            "status": "incorrect",
            "nStatus": {
                    "status":"failed",
                    "n" : expected_n
                },
             "isShowButton":True,
            "correctAnswer": aiJSON['answer'],
            "correctSteps": aiJSON['correctSteps'],
            "selectedAnswer": "n/a",
            "selectedAnswerSteps": [{"step": 'none', "explanation": 'none'}],
            "mistakeStep": 0,
            "userAnswer": user_answer,
              "multiStep":False,
            "hint":"",
            "stepCount": 0,
        }
        
        return jsonify(dread), 500
    except Exception as e:
        print("EXpection")
        print(e)
        
        dread = {
                 "isShowButton":True,
            "status": "incorrect",
            "nStatus": {
                    "status":"failed",
                    "n" : expected_n
                },
            "correctAnswer": aiJSON['answer'],
            "correctSteps": aiJSON['correctSteps'],
            "selectedAnswer": "n/a",
            "selectedAnswerSteps": [{"step": 'none', "explanation": 'none'}],
            "mistakeStep": 0,
            "userAnswer": user_answer,
              "multiStep":False,
            "hint":"",
            "stepCount": 0,
        }
        
        return jsonify(dread), 500
    
@app.route('/checkUserAnswerDebug', methods=['POST'])
def check_user_answer_debug():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate the expected keys in the JSON payload
        user_answer = data['userAnswer']
        euNFunctions = []
        amercianFunctions = []
        max_nLevel = 4  # max number of available n funcs
        userAnswerEuFormat = europenize(user_answer)

        generated_answers = apply_n_func(max_nLevel, userAnswerEuFormat)
       
        euNFunctions = generated_answers
        userAnswerAmericanFormat = americanize(user_answer)
        correctAnswerAmericanFormat = americanize(aiJSON["answer"])
        generated_answers = apply_n_func(max_nLevel, userAnswerAmericanFormat)
        amercianFunctions = generated_answers
        print(sa["hint"])
        returnData = {
            "amercianFunctions":amercianFunctions,
            "euNFunctions":euNFunctions,
        }
        print(returnData)

        return jsonify(returnData), 200

    except KeyError as e:
        print("Key - EXpection")
        print(e)
        dread = {
            "amercianFunctions":amercianFunctions,
            "euNFunctions":euNFunctions,
        }
        
        return jsonify(dread), 500
    except TypeError as e:
        print("T-EXpection")
        print(e)
        dread = {
            "amercianFunctions":amercianFunctions,
            "euNFunctions":euNFunctions,
        }
        
        return jsonify(dread), 500
    except Exception as e:
        print("EXpection")
        print(e)
        
        dread = {
            "amercianFunctions":amercianFunctions,
            "euNFunctions":euNFunctions,
        }
        
        return jsonify(dread), 500

if __name__ == '__main__':
	  app.run(host='0.0.0.0', port=8000)
