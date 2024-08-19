from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from n_funs.n_func import apply_n_func
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Replace with your actual MongoDB connection string
DATABASE_URI = "mongodb+srv://SSN:LO4uCW9mK8OpBQAp@atlascluster.bnamshy.mongodb.net/Bijlex?retryWrites=true&w=majority"

client = MongoClient(DATABASE_URI)
db = client['Bijlex']
collection = db['ai_answers']

# Utility function to convert MongoDB documents to JSON
def serialize_doc(doc):
    doc['_id'] = str(doc['_id'])
    return doc

@app.route('/entries', methods=['POST'])
def create_entry():
    data = request.json
    if 'id' not in data or 'answer' not in data or 'inputString' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    # Determine the maximum nLevel by the number of n_funcs available
    max_nLevel = 4  # Assuming N1, N2, N3, and N4 are available

    # Call apply_n_func with the maximum nLevel
    nAnswers = apply_n_func(max_nLevel, data['inputString'])

    entry = {
        "id": data['id'],
        "answer": data['answer'],
        "nAnswers": nAnswers
    }

    result = collection.insert_one(entry)
    return jsonify({"_id": str(result.inserted_id)}), 201

@app.route('/entries/<id>', methods=['GET'])
def get_entry(id):
    entry = collection.find_one({"id": id})
    if entry:
        return jsonify(serialize_doc(entry)), 200
    else:
        return jsonify({"error": "Entry not found"}), 404

@app.route('/entries', methods=['GET'])
def get_all_entries():
    entries = collection.find()
    return jsonify([serialize_doc(entry) for entry in entries]), 200

@app.route('/entries/<id>', methods=['PUT'])
def update_entry(id):
    data = request.json
    update_data = {}

    if 'answer' in data:
        update_data['answer'] = data['answer']
    if 'nAnswers' in data:
        update_data['nAnswers'] = data['nAnswers']

    result = collection.update_one({"id": id}, {"$set": update_data})

    if result.matched_count > 0:
        return jsonify({"message": "Entry updated"}), 200
    else:
        return jsonify({"error": "Entry not found"}), 404

@app.route('/entries/<id>', methods=['DELETE'])
def delete_entry(id):
    result = collection.delete_one({"id": id})

    if result.deleted_count > 0:
        return jsonify({"message": "Entry deleted"}), 200
    else:
        return jsonify({"error": "Entry not found"}), 404
    
@app.route('/checkUserAnswer', methods=['POST'])
def check_user_answer():
    data = request.json
    if 'id' not in data or 'userAnswer' not in data or 'expectedN' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    entry_id = data['id']
    user_answer = data['userAnswer']
    expected_n = data['expectedN']

    # Find the entry by ID in the database
    entry = collection.find_one({"id": entry_id})
    if not entry:
        return jsonify({"error": "Entry not found"}), 404

    # Get the stored nAnswers from the entry
    stored_nAnswers = entry.get('nAnswers', {})

    # Generate nAnswers using apply_n_func based on the user's input
    generated_answers = apply_n_func(expected_n, user_answer)

    # Initialize the result dictionary
    result = {"answer": "correct"}

    # Compare each level's answer
    for i in range(1, expected_n + 1):
        key = f'N{i}'
        if stored_nAnswers.get(key) == generated_answers.get(key):
            result[key] = "correct"
        else:
            result[key] = "incorrect"
            if i == expected_n:
                result["answer"] = "incorrect"

    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True)
