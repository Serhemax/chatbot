from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import worker as worker 
import logging
import os

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
    try:
        file.save(file_path)
        conversation_id = request.form.get('conversationId', 'default')
        worker.process_document(file_path, conversation_id)
    except Exception as e:
        app.logger.error(f"Error processing file: {e}")
        return jsonify({
            "botResponse": "An error occurred while processing the document. Please ensure the file is a valid PDF."
        }), 500

    return jsonify({
        "botResponse": f"File '{file.filename}' uploaded successfully and analyzed. You can now ask questions about it."
    }), 200

    
    
@app.route('/delete-file', methods=['POST'])
def delete_file_route():
    file_name = request.json.get('fileName')
    conversation_id = request.json.get('conversationId', 'default')
    file_path = os.path.join('.', file_name)

    if os.path.exists(file_path):
        os.remove(file_path)
        worker.delete_file(file_name, conversation_id)
        return jsonify({"status": "success", "message": f"File '{file_name}' deleted successfully."}), 200
    else:
        return jsonify({"status": "error", "message": f"File '{file_name}' not found."}), 404

if __name__ == "__main__":
    app.run(debug=True, port=8000, host='0.0.0.0')
