import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
from PIL import Image
import base64
from quiz_generator import generate_quiz
from datetime import datetime
import json

# Page config
st.set_page_config(page_title="EduTutor AI", layout="wide")

# Dummy course data
courses_list = [
    {"title": "Introduction to AI", "description": "Basics of Artificial Intelligence"},
    {"title": "Python Programming", "description": "Learn the fundamentals of Python"},
    {"title": "Data Structures", "description": "Understand how data is organized"},
    {"title": "Machine Learning", "description": "Learn algorithms that improve from data"},
    {"title": "Web Development", "description": "Frontend & backend web technologies"},
    {"title": "Database Systems", "description": "Design and manage data storage systems"},
    {"title": "Cloud Computing", "description": "Explore scalable cloud-based infrastructure"},
    {"title": "Cybersecurity", "description": "Protect systems and data from cyber threats"},
    {"title": "Mobile App Development", "description": "Create apps for Android and iOS"},
    {"title": "Data Science", "description": "Extract insights from data using analytics"}
]

course_details = {
    "Introduction to AI": "Artificial Intelligence (AI) is the simulation of human intelligence in machines...",
    "Python Programming": "Python is a versatile, high-level programming language widely used in various domains.",
    "Data Structures": "Data structures help efficiently store and retrieve data, like arrays, trees, and graphs.",
    "Machine Learning": "Machine Learning uses data to train models that make predictions or decisions.",
    "Web Development": "It involves HTML, CSS, JS for frontend, and frameworks like Django/Node.js for backend.",
    "Database Systems": "Focuses on SQL, relational models, NoSQL, and data design principles.",
    "Cloud Computing": "Delivers computing services over the internet with providers like AWS, Azure, GCP.",
    "Cybersecurity": "Includes threat detection, encryption, secure programming, and network protection.",
    "Mobile App Development": "Covers UI/UX, Android Studio, Flutter, React Native, and app deployment.",
    "Data Science": "Involves data cleaning, analysis, visualization, and predictive modeling."
}


# Background image base64 function
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Session state init
if "get_started" not in st.session_state:
    st.session_state.get_started = False
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.quiz_history = []
    st.session_state.registered_users = {}
    st.session_state.students = {}
    st.session_state.user_profile = {"name": "", "bio": "", "profile_pic": None}
if "expanded_course" not in st.session_state:
    st.session_state.expanded_course = None
if "model" not in st.session_state:
    st.session_state.model = None
if "tokenizer" not in st.session_state:
    st.session_state.tokenizer = None
if "device" not in st.session_state:
    st.session_state.device = None

# ------------------ GET STARTED PAGE ------------------
if not st.session_state.get_started:
    bg_image_base64 = get_base64_image("bg.png")
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bg_image_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        .getstarted-container {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}
        .getstarted-title {{
            font-size: 72px;
            color: white;
            text-shadow: 2px 2px #00000080;
            margin-bottom: 30px;
        }}
        </style>

        <div class='getstarted-container'>
            <div class='getstarted-title'>EduTutor AI</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""<div style='margin-top: 20px;'>""", unsafe_allow_html=True)
    centered = st.columns([4, 2, 4])
    with centered[1]:
        if st.button("Get Started"):
            st.session_state.get_started = True
    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

# ------------------ LOGIN / REGISTER ------------------
if not st.session_state.logged_in:
    st.title("EduTutor AI Login/Register")
    role = st.selectbox("Select Role", ["student", "educator"])
    action = st.radio("Action", ["Login", "Register"])
    name = st.text_input("Name")
    password = st.text_input("Password", type="password")

    if action == "Register" and st.button("Register"):
        if name and password:
            key = f"{role}:{name}"
            st.session_state.registered_users[key] = password
            st.success("Registered successfully!")
        else:
            st.warning("Fill both fields!")

    if action == "Login" and st.button("Login"):
        key = f"{role}:{name}"
        if st.session_state.registered_users.get(key) == password:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.session_state.user_id = name
            if role == "student" and name not in st.session_state.students:
                st.session_state.students[name] = []
        else:
            st.error("Invalid credentials.")
    st.stop()

# ------------------ LOGOUT BUTTON ------------------
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False, "get_started": False}))

# ------------------ STUDENT PANEL ------------------
if st.session_state.role == "student":
    st.sidebar.title("Student Panel")
    nav = st.sidebar.radio("Navigate", ["Dashboard", "Take Quiz", "Quiz History", "Courses"])

    if nav == "Dashboard":
        st.header(f"Welcome, {st.session_state.user_id}")
        st.subheader("Profile")
        uploaded_file = st.file_uploader("Upload Profile Picture", type=["jpg", "png"])
        if uploaded_file:
            st.session_state.user_profile["profile_pic"] = uploaded_file
        name = st.text_input("Full Name", value=st.session_state.user_profile.get("name", ""))
        bio = st.text_area("About You", value=st.session_state.user_profile.get("bio", ""))
        if st.button("Update Profile"):
            st.session_state.user_profile["name"] = name
            st.session_state.user_profile["bio"] = bio
            st.success("Profile updated!")
        if st.session_state.user_profile["profile_pic"]:
            st.image(st.session_state.user_profile["profile_pic"], width=150)

    elif nav == "Take Quiz":
        st.header("Take a Quiz")
        if st.session_state.model is None:
            from model_setup import load_model_and_tokenizer
            st.session_state.model, st.session_state.tokenizer, st.session_state.device = load_model_and_tokenizer()

        topic = st.text_input("Enter quiz topic")
        level = st.selectbox("Difficulty Level", ["easy", "medium", "hard"])
        count = st.slider("Number of questions", 1, 10, 5)

        if st.button("Generate Quiz") and topic:
            with st.spinner("Generating quiz..."):
                quiz = generate_quiz(topic, level, st.session_state.model, st.session_state.tokenizer, st.session_state.device)
                st.session_state.quiz = quiz
                st.session_state.answers = {}

        if "quiz" in st.session_state and st.session_state.quiz:
            with st.form("quiz_form"):
                for i, q in enumerate(st.session_state.quiz):
                    st.write(f"Q{i+1}: {q['question']}")
                    st.session_state.answers[str(i)] = st.radio("Select answer", q["options"], key=f"ans_{i}")
                submitted = st.form_submit_button("Submit")

            if submitted:
                score = 0
                for i, q in enumerate(st.session_state.quiz):
                    if st.session_state.answers.get(str(i)) == q['answer']:
                        score += 1

                result = {
                    "topic": topic,
                    "score": score,
                    "difficulty": level,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.quiz_history.append(result)
                st.session_state.students[st.session_state.user_id].append(result)
                st.success(f"Quiz completed. Score: {score}/{len(st.session_state.quiz)}")
                del st.session_state.quiz

    elif nav == "Quiz History":
        st.header("Quiz History")
        if st.session_state.quiz_history:
            for q in st.session_state.quiz_history:
                st.write(f"Topic: {q['topic']} | Score: {q['score']} | Difficulty: {q['difficulty']} | Time: {q['timestamp']}")
        else:
            st.write("No quizzes taken yet.")
    
    elif nav == "Courses":
        st.header("Available Courses")

        search_query = st.text_input("Search Courses", "")
        filtered_courses = [c for c in courses_list if search_query.lower() in c["title"].lower()]

        # Two-column layout
        col1, col2 = st.columns(2)
        columns = [col1, col2]

        for index, course in enumerate(filtered_courses):
            with columns[index % 2]:
                with st.container():
                    st.markdown(
                        f"""
                        <div style='background-color:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:20px; box-shadow:2px 2px 10px rgba(0,0,0,0.05);'>
                            <h4>{course['title']}</h4>
                            <p>{course['description']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.expander("See More"):
                        st.write(course_details.get(course["title"], "Details coming soon..."))
                        links = {
                            "Introduction to AI": "https://www.ibm.com/cloud/learn/what-is-artificial-intelligence",
                            "Python Programming": "https://docs.python.org/3/tutorial/",
                            "Data Structures": "https://www.geeksforgeeks.org/data-structures/",
                            "Machine Learning": "https://www.coursera.org/learn/machine-learning",
                            "Web Development": "https://developer.mozilla.org/en-US/docs/Learn",
                            "Database Systems": "https://www.w3schools.com/sql/",
                            "Cloud Computing": "https://cloud.google.com/learn/what-is-cloud-computing",
                            "Cybersecurity": "https://www.cybrary.it/",
                            "Mobile App Development": "https://developer.android.com/courses",
                            "Data Science": "https://www.datacamp.com/"
                        }
                        link = links.get(course["title"], None)
                        if link:
                            st.markdown(f"[📘 Learn More Here]({link})", unsafe_allow_html=True)

# ------------------ EDUCATOR PANEL ------------------
# ------------------ EDUCATOR PANEL ------------------
elif st.session_state.role == "educator":
    st.sidebar.title("Educator Panel")
    nav = st.sidebar.radio("Navigate", ["Dashboard", "Student Activity", "Export Data"])

    if nav == "Dashboard":
        st.markdown(f"<h1 style='margin-bottom:10px;'>Welcome, {st.session_state.user_id}</h1>", unsafe_allow_html=True)
        st.markdown("<h3>Platform Overview</h3>", unsafe_allow_html=True)

        # Metrics
        registered_students = len(st.session_state.students)
        total_quizzes = sum(len(qs) for qs in st.session_state.students.values())
        all_scores = [q["score"] for quizzes in st.session_state.students.values() for q in quizzes]
        average_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

        topic_counts = {}
        for quizzes in st.session_state.students.values():
            for q in quizzes:
                topic_counts[q["topic"]] = topic_counts.get(q["topic"], 0) + 1

        popular_topic_display = max(topic_counts.items(), key=lambda x: x[1])[0] if topic_counts else "No quizzes yet"

        st.markdown(f"""
        <div style='font-size:18px; line-height:2em;'>
            <b>Registered Students</b>: {registered_students}<br>
            <b>Total Quizzes Taken</b>: {total_quizzes}<br>
            <b>Average Score</b>: {average_score}<br>
            <b>Most Popular Topic</b>: {popular_topic_display}
        </div>
        """, unsafe_allow_html=True)

    elif nav == "Student Activity":
        st.header("📊 Student Quiz Submissions")

        if not st.session_state.students:
            st.info("No student data available yet.")
        else:
            filter_topic = st.text_input("Filter by Topic (optional)")
            for student, history in st.session_state.students.items():
                filtered_history = [q for q in history if filter_topic.lower() in q["topic"].lower()] if filter_topic else history

                if not filtered_history:
                    continue

                st.subheader(f"👤 Student: {student}")
                for q in filtered_history:
                    st.write(f"📘 Topic: {q['topic']} | 🎯 Score: {q['score']} | 🧠 Difficulty: {q['difficulty']} | 🕒 {q['timestamp']}")

                avg = round(sum(q['score'] for q in filtered_history) / len(filtered_history), 2)
                st.markdown(f"<span style='color:green;'><b>Average Score:</b> {avg}</span>", unsafe_allow_html=True)
                st.markdown("---")

    elif nav == "Export Data":
        import pandas as pd
        st.header("⬇️ Export Student Performance")

        all_data = []
        for student, quizzes in st.session_state.students.items():
            for q in quizzes:
                all_data.append({
                    "Student": student,
                    "Topic": q["topic"],
                    "Score": q["score"],
                    "Difficulty": q["difficulty"],
                    "Timestamp": q["timestamp"]
                })

        if all_data:
            df = pd.DataFrame(all_data)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV Report", data=csv, file_name="student_performance.csv", mime="text/csv")
        else:
            st.info("No quiz data to export.")


    elif nav == "Student Activity":
        st.header("Student Quiz Submissions")
        for student, history in st.session_state.students.items():
            st.subheader(f"Student: {student}")
            for q in history:
                st.write(f"Topic: {q['topic']} | Score: {q['score']} | Difficulty: {q['difficulty']} | Time: {q['timestamp']}")
