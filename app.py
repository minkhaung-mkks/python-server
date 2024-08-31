from flask import Flask, request, jsonify
from n_funs.n_func import apply_n_func
from flask_cors import CORS

app = Flask(__name__)
allowed_origins = [
    "http://localhost:5174",
    "http://localhost:5173",
]

# Enable CORS for the specified origins
CORS(app, origins=allowed_origins)


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

        generated_answers = apply_n_func(max_nLevel, user_answer)
        nAnswers = apply_n_func(max_nLevel, aiJSON["answer"])
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
                    result["nStatus"] = "incorrect"
        sa = {
            "steps": aiJSON['correctSteps'],
            "value": user_answer,
            "mistakeStep": 0,
            "nStatus": {"n": expected_n, "status": result.get("nStatus", "correct")}
        }
        print(eq)

        if not eq:
            print('--------------')
            result['answer'] = "incorrect"
            for incorrect in incorrectAnswers:
                if 'value' not in incorrect or 'steps' not in incorrect or 'mistakeStep' not in incorrect:
                    continue  # Skip this incorrect answer if required fields are missing
                result["ia"] ="correct"
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
        print(result)
        print(sa['nStatus'])
        print(sa['value'])
        print(sa['steps'])
        print(sa['mistakeStep'])
        print(aiJSON['correctSteps'])
        print(aiJSON['answer'])
        print(result['answer'])
        print(user_answer)
        print(result)
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
        print(returnData)

        return jsonify(returnData), 200

    except KeyError as e:
        return jsonify({"error": f"Missing key: {str(e)}"}), 400
    except TypeError as e:
        return jsonify({"error": f"Type error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == '__main__':
	  app.run(host='0.0.0.0', port=8000)
