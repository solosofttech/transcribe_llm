
from flask import Flask, request, jsonify
import openpyxl
import os
import pandas as pd
import openai

app = Flask(__name__)

# Load the transcription data from Excel on application start
file_path = "transcriptions_metadata.xlsx"  # Replace with your Excel file path
df = pd.read_excel(file_path)

# OpenAI API key
openai.api_key = ""  # Replace with your OpenAI API key

# Function to query ChatGPT for information retrieval
def query_chatgpt(query, df, model="GPT-3.5 Turbo"):
    # Combine all transcription chunks into a single text corpus for retrieval
    corpus = []
    for index, row in df.iterrows():
        entry = {
            "transcription": row["transcription"],
            "video_link": row["video_link"],
            "time_stamp": row["time_stamp"]
        }
        corpus.append(entry)
    
    # Prepare the prompt for the ChatGPT API
    prompt = f"You are given the following transcriptions of instructional YouTube videos. A user is looking for an answer to the query: '{query}'. Please provide the most relevant instructional text along with the video link and time stamp.\n\n"
    
    for entry in corpus:
        prompt += f"Transcription Chunk: {entry['transcription']}\nVideo Link: {entry['video_link']}\nTime Stamp: {entry['time_stamp']}\n\n"
    
    # Call OpenAI ChatGPT API
    response = openai.Completion.create(
        engine=model,
        prompt=prompt,
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.5
    )
    
    # Extract and return the response
    return response.choices[0].text.strip()

# Function to create or open an existing Excel file
def save_to_excel(data):
    file_name = "user_data.xlsx"

    # Check if file exists, if not, create it and add headers
    if not os.path.exists(file_name):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.append(["Name", "Email", "Phone", "Message"])  # Adding headers
    else:
        workbook = openpyxl.load_workbook(file_name)
        sheet = workbook.active

    # Append the new data
    sheet.append([data['name'], data['email'], data['phone'], data['message']])

    # Save the Excel file
    workbook.save(file_name)

@app.route('/')
def home():
    try:
        print ('Generative AI Project')
        return jsonify(status=200) 
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for collecting user data and saving it to Excel
@app.route('/submit', methods=['POST'])
def submit_data():
    try:
        # Collecting data from the request
        name = request.json.get('name')
        email = request.json.get('email')
        phone = request.json.get('phone')
        message = request.json.get('message')

        # Validate the input data
        if not name or not email or not phone or not message:
            return jsonify({"error": "All fields are required"}), 400

        # Save data to Excel
        save_to_excel({
            "name": name,
            "email": email,
            "phone": phone,
            "message": message
        })

        return jsonify({"message": "Data saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to handle user queries
@app.route('/retrieve_info', methods=['POST'])
def retrieve_info():
    # Get the user query from the POST request JSON payload
    data = request.get_json()
    user_query = data.get('query')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    # Retrieve information using ChatGPT and the transcription metadata
    result = query_chatgpt(user_query, df)
    
    # Return the result as a JSON response
    return jsonify({"response": result})

if __name__ == '__main__': 
    app.run(host='127.0.0.1', port='8080')
    
