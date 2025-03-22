import streamlit as st
import google.generativeai as genai
import os
import json
import uuid
import re

MODEL_ID = "gemini-1.5-flash"  # Verified working model
USER_DATA_FILE = "users.json"
CHAT_HISTORY_FILE = "chat_history.json"

def configure_api():
    try:
        api_key = "AIzaSyALw7gclIWE-j_eQG4qDl7EPfDJT4v2adA"
        genai.configure(api_key=api_key)
        
        # Verify model availability
        available_models = [m.name for m in genai.list_models()]
        if f"models/{MODEL_ID}" not in available_models:
            st.error(f"Error: Model {MODEL_ID} not available.")
            st.stop()
            
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(users, file)

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as file:
            data = json.load(file)
            for user in data:
                for session_id in data[user]:
                    if isinstance(data[user][session_id], list):
                        data[user][session_id] = {
                            "history": data[user][session_id],
                            "quiz": None
                        }
            return data
    return {}

def save_chat_history(history):
    with open(CHAT_HISTORY_FILE, "w") as file:
        json.dump(history, file)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "users" not in st.session_state:
    st.session_state.users = load_users()
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = load_chat_history()
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "chat_model" not in st.session_state:
    st.session_state.chat_model = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

def login_signup():
    st.title("Studently Tutor 🤖✨")
    page_choice = st.radio("", ["Login", "Sign Up"], horizontal=True)
    
    if page_choice == "Login":
        username = st.text_input("👤 Username:")
        password = st.text_input("🔒 Password:", type="password")
        if st.button("🚀 Login"):
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                if not st.session_state.chat_sessions.get(username):
                    st.session_state.chat_sessions[username] = {}
                st.rerun()
            else:
                st.error("❌ Invalid login credentials.")
    else:
        new_username = st.text_input("🆕 Choose a Username:")
        new_password = st.text_input("🔑 Choose a Password:", type="password")
        if st.button("✅ Sign Up"):
            if new_username and new_password:
                if new_username in st.session_state.users:
                    st.error("⚠️ Username already exists. Choose another.")
                else:
                    st.session_state.users[new_username] = new_password
                    save_users(st.session_state.users)
                    st.session_state.authenticated = True
                    st.session_state.username = new_username
                    st.session_state.chat_sessions[new_username] = {}
                    st.rerun()
            else:
                st.error("⚠️ Please enter a valid username and password.")

def generate_quiz(history):
    try:
        st.toast("Starting quiz generation...")
        conversation = []
        for msg in history:
            role = "Student" if msg["role"] == "user" else "Tutor"
            text = msg["parts"][0]
            conversation.append(f"{role}: {text}")
        conversation_text = "\n".join(conversation)
        
        prompt = f"""Generate a 5-question multiple choice quiz based on this conversation. Follow these rules STRICTLY:
1. Output ONLY valid JSON with no additional text
2. Questions should test key concepts discussed
3. Each question must have 4 options
4. Use this exact JSON structure:
{{
  "questions": [
    {{
      "question": "Your question here",
      "options": ["a", "b", "c", "d"],
      "correct_index": 0
    }}
  ]
}}

Conversation:
{conversation_text}"""

        model = genai.GenerativeModel(MODEL_ID)
        response = model.generate_content(prompt)
        
        # Clean response text
        response_text = re.sub(r'^```json\s*|\s*```$', '', response.text, flags=re.IGNORECASE).strip()
        
        quiz_data = json.loads(response_text)
        
        # Validate quiz structure
        if not isinstance(quiz_data.get("questions", None), list):
            raise ValueError("Invalid quiz format - missing questions list")
            
        for question in quiz_data["questions"]:
            if not all(key in question for key in ["question", "options", "correct_index"]):
                raise ValueError("Invalid question format")
            if len(question["options"]) != 4:
                raise ValueError("Each question must have exactly 4 options")
            if not 0 <= question["correct_index"] < 4:
                raise ValueError("Invalid correct index")

        # Store quiz
        username = st.session_state.username
        session_id = st.session_state.current_session_id
        st.session_state.chat_sessions[username][session_id]["quiz"] = quiz_data
        save_chat_history(st.session_state.chat_sessions)
        st.success("✅ Quiz generated successfully!")
        st.balloons()
        return True
        
    except json.JSONDecodeError:
        st.error("Failed to parse quiz response. Please try again.")
        if 'response' in locals():
            with st.expander("Technical Details"):
                st.write("Raw response:", response.text)
    except Exception as e:
        st.error(f"Quiz generation failed: {str(e)}")
        if 'response' in locals():
            with st.expander("Technical Details"):
                st.write("Raw response:", response.text)
    return False

def display_quiz(quiz_data):
    st.subheader("📝 Session Quiz")
    score = 0
    total = len(quiz_data["questions"])
    
    for i, question in enumerate(quiz_data["questions"]):
        st.markdown(f"**Q{i+1}:** {question['question']}")
        answer = st.radio(
            "Options:",
            question["options"],
            key=f"quiz_{st.session_state.current_session_id}_{i}",
            index=None
        )
        
        if answer is not None:
            if answer == question["options"][question["correct_index"]]:
                score += 1
                st.success("✅ Correct!")
            else:
                correct = question["options"][question["correct_index"]]
                st.error(f"❌ Incorrect. Correct answer: {correct}")
        st.divider()
    
    st.subheader(f"🎯 Score: {score}/{total}")
    if st.button("🔄 Retake Quiz"):
        st.session_state.user_answers = {}
        st.rerun()

def chatbot():
    st.sidebar.title("📜 Chat Sessions")
    username = st.session_state.username
    
    if username not in st.session_state.chat_sessions:
        st.session_state.chat_sessions[username] = {}
    
    # New session button
    if st.sidebar.button("🆕 New Session"):
        new_session_id = str(uuid.uuid4())
        st.session_state.chat_sessions[username][new_session_id] = {
            "history": [],
            "quiz": None
        }
        st.session_state.current_session_id = new_session_id
        st.session_state.chat_model = genai.GenerativeModel(MODEL_ID).start_chat(history=[])
        save_chat_history(st.session_state.chat_sessions)
        st.rerun()
    
    # Session list
    user_sessions = st.session_state.chat_sessions[username]
    non_empty_sessions = {k: v for k, v in user_sessions.items() if len(v["history"]) > 0}
    
    for i, session_id in enumerate(non_empty_sessions):
        session = user_sessions[session_id]
        msg_count = len(session["history"]) // 2
        btn_label = f"Session {i+1} ({msg_count} messages)"
        
        cols = st.sidebar.columns([3,1])
        cols[0].button(
            btn_label,
            key=f"btn_{session_id}",
            on_click=lambda sid=session_id: [
                st.session_state.__setitem__("current_session_id", sid),
                st.session_state.__setitem__(
                    "chat_model", 
                    genai.GenerativeModel(MODEL_ID).start_chat(
                        history=user_sessions[sid]["history"]
                    )
                ),
                st.rerun()
            ]
        )
        cols[1].button(
            "✖️",
            key=f"del_{session_id}",
            on_click=lambda sid=session_id: [
                user_sessions.pop(sid),
                save_chat_history(st.session_state.chat_sessions),
                st.rerun()
            ]
        )
    
    # Main chat interface
    st.title("💡 Studently Tutor ✨")
    
    if not st.session_state.current_session_id:
        new_session_id = str(uuid.uuid4())
        st.session_state.chat_sessions[username][new_session_id] = {
            "history": [],
            "quiz": None
        }
        st.session_state.current_session_id = new_session_id
        st.session_state.chat_model = genai.GenerativeModel(MODEL_ID).start_chat(history=[])
    
    current_session = user_sessions[st.session_state.current_session_id]
    
    # Display chat history
    for msg in current_session["history"]:
        if msg["role"] == "user":
            st.markdown(f"🧑🎓 **You:** {msg['parts'][0]}")
        else:
            st.markdown(f"🤖 **Tutor:** {msg['parts'][0]}")
        st.divider()
    
    # Chat input
    with st.form(key="chat_form", clear_on_submit=True):
        prompt = st.text_input("✍️ Ask your question:")
        submitted = st.form_submit_button("Send")
        
        if submitted and prompt:
            with st.spinner("🤖 Thinking..."):
                response = st.session_state.chat_model.send_message(prompt+ " Use emojis in responses but dont talk about using them. (dont use too many)")
                current_session["history"].extend([
                    {"role": "user", "parts": [prompt]},
                    {"role": "model", "parts": [response.text]}
                ])
                save_chat_history(st.session_state.chat_sessions)
                st.rerun()
    
    # Quiz section
    st.divider()
    st.subheader("🎓 Quiz Generator")
    
    if current_session["quiz"]:
        display_quiz(current_session["quiz"])
    else:
        st.info("No quiz generated yet for this session")
    
    if st.button("📝 Generate Quiz from This Session"):
        if len(current_session["history"]) < 4:
            st.warning("Need at least 2 pairs of Q&A to generate a quiz")
        else:
            with st.spinner("✨ Creating quiz... (This may take 10-15 seconds)"):
                if generate_quiz(current_session["history"]):
                    st.rerun()
                else:
                    st.error("Failed to generate quiz - see errors above")

    # Account management
    st.divider()
    st.write(f"🔐 Logged in as: {username}")
    if st.button("🔓 Logout"):
        save_chat_history(st.session_state.chat_sessions)
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.current_session_id = None
        st.rerun()

def main():
    configure_api()
    
    if not st.session_state.authenticated:
        login_signup()
        return
    
    chatbot()

if __name__ == "__main__":
    main()
