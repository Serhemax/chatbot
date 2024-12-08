from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import worker as worker 
import logging

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.logger.setLevel(logging.DEBUG)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process-message', methods=['POST'])
def process_message_route():
    user_message = request.json['userMessage']
    conversation_id = request.json.get('conversationId', 'default')  # Get conversation ID
    bot_response = worker.process_prompt(user_message, conversation_id)
    return jsonify({"botResponse": bot_response}), 200

@app.route('/process-document', methods=['POST'])
def process_document_route():
    if 'file' not in request.files:
        return jsonify({
            "botResponse": "No file uploaded. Please try again."
        }), 400

    file = request.files['file']
    file_path = file.filename
    file.save(file_path)

    conversation_id = request.form.get('conversationId', 'default')  # Get conversation ID
    worker.process_document(file_path, conversation_id)

    return jsonify({
        "botResponse": f"File '{file.filename}' uploaded successfully and analyzed. You can now ask questions about it."
    }), 200

if __name__ == "__main__":
    app.run(debug=True, port=8000, host='0.0.0.0')
