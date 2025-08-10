import streamlit as st
import pandas as pd
import json
import speech_recognition as sr
from pathlib import Path
import random
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment import SentimentIntensityAnalyzer
import google.generativeai as genai
from dotenv import load_dotenv
import os


# Ensure necessary NLTK data is available
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

# Load environment variables from .env file
load_dotenv()

# Initialize Sentiment Analyzer
sia = SentimentIntensityAnalyzer()

# Set up Google Gemini API key
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

class AI_Project_Functions:
    @staticmethod
    def get_crm_data(file_path='crm.json'):
        """Load CRM data from a JSON file."""
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            # Create an empty JSON file if it doesn't exist
            with open(file_path, 'w') as file:
                json.dump({}, file)
            return {}
        except json.JSONDecodeError:
            st.error("Error: Failed to decode JSON. The file might be corrupted.")
            return {}
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            return {}

    @staticmethod
    def get_all_users(crm_data):
        """Get a list of all users in the CRM data."""
        return list(crm_data.keys())

    @staticmethod
    def get_user_info(crm_data, name):
        """Get user information from the CRM data."""
        return crm_data.get(name, {})

    @staticmethod
    def add_entry_to_crm(name, part_purchase_list, interests_list, file_path='crm.json'):
        """Add a new entry to the CRM data."""
        try:
            data = AI_Project_Functions.get_crm_data(file_path)
            data[name] = {
                "past_purchases": part_purchase_list,
                "interests": interests_list,
                "recommendations": []  # Initialize recommendations as empty
            }
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
            return f"Successfully added {name}'s information to the database."
        except Exception as e:
            return f"Error in adding {name}'s information: {e}"

    @staticmethod
    def update_interests(name, new_interests, file_path='crm.json'):
        """Update a user's interests in the CRM data."""
        try:
            data = AI_Project_Functions.get_crm_data(file_path)
            if name not in data:
                return f"Error: {name} not found in the database."
            
            if isinstance(new_interests, str):
                if "interests" not in data[name]:
                    data[name]["interests"] = []
                if new_interests not in data[name]["interests"]:
                    data[name]["interests"].append(new_interests)
            elif isinstance(new_interests, list):
                data[name]["interests"] = new_interests
            else:
                return "Error: new_interests must be a string or a list."

            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
            return f"Successfully updated {name}'s interests."
        except Exception as e:
            return f"Error in updating {name}'s interests: {e}"
        
    @staticmethod
    def analyze_sentiment(user_input):
        """Analyze user sentiment using VADER and convert the compound score into a range of 1-10."""
        sentiment_score = sia.polarity_scores(user_input)['compound']  # VADER's compound score

        # Convert VADER score (-1 to +1) to 1-10 scale
        emotional_state = int((sentiment_score + 1) * 4.5 + 1)  # Normalize to 1-10 range

        return max(1, min(10, emotional_state))

    @staticmethod
    def query_gemini(prompt):
        """Queries Google Gemini API for AI-generated responses."""
        try:
            model = genai.GenerativeModel("gemini-2.5-pro")
            response = model.generate_content(prompt)
            return response.text.strip()  # Extract response text
        except Exception as e:
            return f"⚠️ API Error: {str(e)}"

    @staticmethod
    def recommend_product(customer_name, interests, emotion_score):
        """Recommend products based on user interests and emotional state using Gemini API."""
        interest_list = ", ".join(interests)
        prompt = f"Suggest 3 personalized products for someone interested in {interest_list}. The customer has an emotional satisfaction score of {emotion_score}/10."
        recommendations = AI_Project_Functions.query_gemini(prompt)
        return recommendations

    @staticmethod
    def generate_prompt(objection):
        """Generate an AI-based response to customer objections."""
        prompt = f"A customer has an objection: {objection}. How should a salesperson respond professionally?"
        response = AI_Project_Functions.query_gemini(prompt)
        return response

    @staticmethod
    def generate_summary(customer_name, speech_transcript, emotion_score):
        """Generate a professional sales call summary."""
        prompt = f"A customer named {customer_name} said: '{speech_transcript}'. The customer's emotional satisfaction score is {emotion_score}/10. Generate a professional sales call summary, highlighting concerns and providing a persuasive response."
        summary = AI_Project_Functions.query_gemini(prompt)
        return summary

    @staticmethod
    def queryToSentiment(name, query):
        """Analyze the query and generate sentiment-based response."""
        crm_data = AI_Project_Functions.get_crm_data()
        user_Data = AI_Project_Functions.get_user_info(name=str(name), crm_data=crm_data)
        
        interests = user_Data["interests"]
        past_purchases = user_Data["past_purchases"]
        
        # Analyze sentiment
        state_of_mind = AI_Project_Functions.analyze_sentiment(query)
        emotion = "happy" if state_of_mind > 5 else "neutral" if state_of_mind == 5 else "disappointed"
        
        # Generate recommendations
        recommendations = AI_Project_Functions.recommend_product(name, interests, state_of_mind)
        
        # Prepare data to return
        data_to_return = {
            "state_of_mind": state_of_mind,
            "emotion": emotion,
            "suggestions": recommendations,
        }
        
        return data_to_return

    @staticmethod
    def visual_state_of_mind(state_of_mind):
        """Create a progress bar that visually represents the state_of_mind (0 to 10)."""
        progress = state_of_mind / 10  # Normalize it to be between 0 and 1 (for the progress bar)
        st.write(f"State of Mind: {state_of_mind}")
        st.progress(progress)

    @staticmethod
    def process_query(query):
        """Dummy function to simulate backend processing."""
        query = query.lower()  # Convert query to lowercase for easier matching

        # Define keyword-response pairs
        responses = {
            "demo": "Sure! Let me schedule a product demo for you. Please provide your availability.",
            "pricing": "Here are our customized pricing plans: Basic ($50/month), Pro ($100/month), Enterprise ($200/month).",
            "support": "Please contact our technical support team at support@example.com or call +1-800-123-4567.",
            "interest": "Based on your interests, I recommend checking out our latest AI tools and solutions.",
            "purchase": "Thank you for your purchase! Let me know if you need assistance with setup or usage.",
            "hello": "Hello! How can I assist you today?",
            "bye": "Goodbye! Have a great day!",
        }

        # Check for keywords in the query
        for keyword, response in responses.items():
            if keyword in query:
                return response

        # Default response if no keywords are found
        return "I'm sorry, I didn't understand your query. How can I assist you further?"

# Set up the page configuration
st.set_page_config(page_title="AI Sales Call Assistant", layout="wide", page_icon="📞")

# Title of the application
st.title("📞 AI Sales Call Assistant")
st.markdown("---")

def speech_to_text():
    """Convert speech to text using the microphone."""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.write("🎤 Recording... Speak now!")
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            return text
    except sr.UnknownValueError:
        return "Sorry, I could not understand the audio."
    except sr.RequestError:
        return "Sorry, there was an issue with the speech recognition service."
    except Exception as e:
        return f"Error accessing the microphone: {e}"

# Navigation sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Sales Call Assistant", "Admin Panel"])

# Sales Call Assistant Page
if page == "Sales Call Assistant":
    st.header("Customer Interaction")

    crm_data = AI_Project_Functions.get_crm_data()
    customer_names = AI_Project_Functions.get_all_users(crm_data)
    selected_customer = st.selectbox("Select Customer", customer_names, index=0)

    # Fetch customer details
    selected_customer_data = AI_Project_Functions.get_user_info(crm_data, selected_customer)

    # Display selected customer details
    if selected_customer_data:
        st.subheader(f"Selected Customer: *{selected_customer}*")
        st.write("*Interests:*")
        for interest in selected_customer_data.get('interests', []):
            st.write(f"- {interest}")
        st.write("*Past Purchases:*")
        for purchase in selected_customer_data.get('past_purchases', []):
            st.write(f"- {purchase}")

        # Real-time voice recording for user queries
        st.subheader("Voice Query")
        if st.button("🎤 Start Recording"):
            user_query = speech_to_text()
            st.write("You said:", user_query)

            # Backend processing placeholder
            if user_query:
                st.subheader("AI Response")
                response = AI_Project_Functions.process_query(user_query)  # Call the dummy function
                st.write(response)

                # Generate sentiment-based response
                sentiment_data = AI_Project_Functions.queryToSentiment(selected_customer, user_query)
                st.write(f"State of Mind: (0 Being Extremely Unhappy/Sad to 10 Being Extremely Happy/Satisfied)")
                state_of_mind_score = int(sentiment_data["state_of_mind"])
                AI_Project_Functions.visual_state_of_mind(state_of_mind_score)
                st.write(f"Emotion Category: {sentiment_data['emotion']}")
                st.write("Suggestions:")
                st.write(f"{sentiment_data['suggestions']}")
            else:
                st.warning("Please speak loudly.")
    

        # Manual text input as an alternative to voice
        st.subheader("Or Type Your Query")
        manual_query = st.text_area("Enter your query here", placeholder="Type your question or concern...")
        if st.button("Submit Query"):
            if manual_query:
                st.subheader("AI Response")
                sentiment_data = AI_Project_Functions.queryToSentiment(selected_customer, manual_query)
                st.write(f"State of Mind: (0 Being Extremely Unhappy/Sad to 10 Being Extremely Happy/Satisfied)")
                state_of_mind_score = int(sentiment_data["state_of_mind"])
                AI_Project_Functions.visual_state_of_mind(state_of_mind_score)
                st.write(f"Emotion Category: {sentiment_data['emotion']}")
                st.write("Suggestions:")
                st.write(f"{sentiment_data['suggestions']}")
            else:
                st.warning("Please enter a query before submitting.")

# Admin Panel Page
elif page == "Admin Panel":
    st.header("Admin Panel")
    st.markdown("Manage customer data here.")

    crm_data = AI_Project_Functions.get_crm_data()

    # Add New Customer
    st.subheader("Add New Customer")
    with st.form(key="add_customer_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_name = st.text_input("Name", placeholder="Enter customer name")
        with col2:
            new_interests = st.text_input("Interests", placeholder="Enter customer interests (comma-separated)")
        with col3:
            new_past_purchases = st.text_input("Past Purchases", placeholder="Enter past purchases (comma-separated)")
        
        if st.form_submit_button("Add Customer"):
            if new_name and new_interests and new_past_purchases:
                interests_list = [interest.strip() for interest in new_interests.split(",")]
                past_purchases_list = [purchase.strip() for purchase in new_past_purchases.split(",")]
                result = AI_Project_Functions.add_entry_to_crm(
                    name=new_name,
                    part_purchase_list=past_purchases_list,
                    interests_list=interests_list
                )
                st.success(result)
            else:
                st.error("Please fill in all fields.")

    # Edit Existing Customer
    st.subheader("Edit Existing Customer")
    edit_customer_name = st.selectbox("Select Customer to Edit", AI_Project_Functions.get_all_users(crm_data))
    if edit_customer_name:
        st.write(f"### Editing Interests for {edit_customer_name}")
        current_interests = AI_Project_Functions.get_user_info(crm_data, edit_customer_name).get('interests', [])
        st.write(f"*Current Interests:* {', '.join(current_interests)}")
        with st.form(key="edit_customer_form"):
            add_interest = st.text_input("Add a New Interest (One at a Time)")
            replace_interests = st.text_input("Replace with New Set of Interests (Comma-Separated)")
            
            if st.form_submit_button("Update Interests"):
                if add_interest:
                    result = AI_Project_Functions.update_interests(edit_customer_name, add_interest)
                    st.success(result)
                elif replace_interests:
                    interests_list = [interest.strip() for interest in replace_interests.split(",")]
                    result = AI_Project_Functions.update_interests(edit_customer_name, interests_list)
                    st.success(result)
                else:
                    st.error("Please enter either a new interest or a new set of interests.")

    # View All Customers
    st.subheader("All Customers")
    st.write(pd.DataFrame(AI_Project_Functions.get_all_users(crm_data)))

# Footer
st.markdown("---")
st.write("© 2025 AI Sales Call Assistant. All rights reserved.")