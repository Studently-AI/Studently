from flask import Flask, request, jsonify
import google.generativeai as genai
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allows frontend to communicate with backend

# Configure Gemini API
API_KEY = "AIzaSyALw7gclIWE-j_eQG4qDl7EPfDJT4v2adA"  # Replace with your actual API key
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("message")+" Make your response seem like a study guide and make it easy to understand and concise. Use a few emojis in your response as well."

    if not prompt:
        return jsonify({"error": "Empty message"}), 400

    try:
        response = model.generate_content(prompt)
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)