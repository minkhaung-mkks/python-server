from flask import Flask, request, jsonify
from n_funs.n_func import apply_n_func
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
allowed_origins = [
    "http://localhost:5174",
    "http://localhost:5173",
    "https://@test.com"
]

# Enable CORS for the specified origins
CORS(app, origins=allowed_origins)


@app.route('/checkUserAnswer', methods=['POST'])
def check_user_answer():
    data = request.json

    aiJSON = data['AI_JSON']
    user_answer = data['userAnswer']
    expected_n = aiJSON['n']
    incorrectAnswers = aiJSON['ia']

    # Generate nAnswers using apply_n_func based on the user's input
    max_nLevel = 4  # max number of available n funcs

    generated_answers = apply_n_func(max_nLevel, user_answer)
    nAnswers = apply_n_func(max_nLevel, aiJSON["answer"])

    # Initialize the result dictionary
    result = {"answer": "correct"}
    eq = False

    # Compare each level's answer
    for i in range(1, expected_n + 1):
        key = f'N{i}'
        if nAnswers.get(key) == generated_answers.get(key):
            result[key] = "correct"
            eq = True
        else:
            result[key] = "incorrect"
            if i == expected_n:
                result["nStatus"] = "incorrect"

    sa = {
        "steps": aiJSON['correctSteps'],
        "value": user_answer,
        "ms": 0,
        "nStatus": {"n": expected_n, "status": result.get("nStatus", "correct")}
    }

    if not eq:
        result['answer'] = "incorrect"
        for incorrect in incorrectAnswers:
            result = {"ia": "correct"}
            nIa = apply_n_func(max_nLevel, incorrect['value'])
            for i in range(1, expected_n + 1):
                key = f'N{i}'
                if nIa.get(key) == generated_answers.get(key):
                    result[key] = "correct"
                    eq = True
                else:
                    result[key] = "incorrect"
                    if i == expected_n:
                        result["ia"] = "incorrect"
            if eq:
                sa = {
                    "value": incorrect['value'],
                    "steps": incorrect['steps'],
                    "nStatus": {"n": expected_n, "status": result["ia"]},
                    "mistakeStep": incorrect['mistakeStep']
                }
                break

    if not eq:
        sa = {
            "value": 'n/a',
            "steps": [{"step": 'none', "explanation": 'none'}],
            "nStatus": {"status": 'failed', "n": 0},
            "mistakeStep": 0
        }

    returnData = {
        "status": result["answer"],
        "nStatus": sa["nStatus"],
        "correctAnswer": aiJSON['answer'],
        "correctSteps": aiJSON['correctSteps'],
        "selectedAnswer": sa["value"],
        "selectedAnswerSteps": sa["steps"],
        "mistakeStep": sa["mistakeStep"],
        "userAnswer": user_answer,
    }
    

    # both status and nStatus.status need be correct for a student to be correct.
    # if only status is correct they have the correct answer but wrong format
    # if only nStatus is correct that means they have made a logical mistake but in correct format
    # if both are incorrect but are returning valid data that means they made a logical mistake but wrong format
    # if data is like this
    # "value": 'n/a',
    # "steps": [{"step": 'none', "explanation": 'none'}],
    # "nStatus": {"status": 'failed', "n": 0},
    # "mistakeStep": 0
    #  The student has made an illogical or uncaught misake
    #  on the last case, I believe the intention is to not even show the solution panel 
    #  instead just tell them they are wrong and move on
    return jsonify(returnData), 200


if __name__ == '__main__':
    app.run()
