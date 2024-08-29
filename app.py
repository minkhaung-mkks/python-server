from flask import Flask, request, jsonify
from n_funs.n_func import apply_n_func
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
allowed_origins = [
    "http://localhost:5174",
    "http://localhost:5173",
]

# Enable CORS for the specified origins
CORS(app, origins=allowed_origins)


@app.route('/checkUserAnswer', methods=['POST'])
def check_user_answer():
    data = request.json

    aiJSON = data['AI_JSON']
    print(aiJSON)
    user_answer = data['userAnswer']
    expected_n = aiJSON['n']
    # Generate nAnswers using apply_n_func based on the user's input
    max_nLevel = 4  # Assuming N1, N2, N3, and N4 are available
    generated_answers = apply_n_func(expected_n, user_answer)
    nAnswers = apply_n_func(max_nLevel, aiJSON["answer"])
    print(generated_answers)
    print(nAnswers)
    # Initialize the result dictionary
    result = {"answer": "correct"}
    # Compare each level's answer
    for i in range(1, expected_n + 1):
        key = f'N{i}'
        if nAnswers.get(key) == generated_answers.get(key):
            result[key] = "correct"
        else:
            result[key] = "incorrect"
            if i == expected_n:
                result["answer"] = "incorrect"
    
    return jsonify(result), 200


if __name__ == '__main__':
    app.run()
