from flask import Flask, render_template, request, flash, jsonify
from flask.helpers import send_from_directory
from openai import OpenAI
import random
from flask_cors import CORS, cross_origin
import boto3
import requests
import os
from PIL import Image
from io import BytesIO
from threading import Thread
import json

app = Flask(__name__, static_folder='dist', static_url_path='/')
CORS(app, support_credentials=True)

@app.route('/')
@cross_origin(supports_credentials=True)
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/generate_data_test', methods=['POST'])
@cross_origin(supports_credentials=True)
def generate_data_test():
    if request.method == 'POST':
        frontend_data = request.json

        num_of_images = frontend_data.get('num_of_images', '3')
        subject = frontend_data.get('subject', 'math')
        age_range = frontend_data.get('age_range', '4-6')
        image_entities = frontend_data.get('image_entities', 'white cats')

        print(num_of_images, subject, age_range, image_entities)

    data_to_front = [{'id': 1, 'url': 'https://storybookml.s3.amazonaws.com/image1.jpg', 'text': 'In a little town called Number Wheels, all the colorful cars were learning how to count. Beep-Beep, the small yellow car, had one big round steering wheel. Zoomy, the speedy red race car, had four shiny wheels that loved to roll fast. The friendly fire truck, named Flash, had six wheels that helped it rush to emergencies. Together, they counted their wheels, adding them all up to eleven, and had a fun parade around the town square, showing everyone that math is everywhere, even on cars!', 'question': 'How many wheels in total did Beep-Beep, Zoomy, and Flash count for their parade around Number Wheels town?', 'answer': 'Beep-Beep, Zoomy, and Flash counted together and found 12 wheels for their fun parade in Number Wheels town.'}, {'id': 2, 'url': 'https://storybookml.s3.amazonaws.com/image2.jpg', 'text': 'Once upon a time, two friendly trucks named Tippy and Zoomy had a fun counting game. Tippy had four big wheels, and Zoomy had four too. They decided to add their wheels together to see how many they had in total. They counted "1, 2, 3, 4," and then "5, 6, 7, 8," and discovered that together they had eight wheels! Tippy and Zoomy were so happy to learn about adding numbers and they drove off to tell their friends about their new math adventure.', 'question': 'How many wheels do Tippy and Zoomy have together after they add their wheels?', 'answer': 'Tippy and Zoomy have ten wheels together when they add them all up!'}, {'id': 3, 'url': 'https://storybookml.s3.amazonaws.com/image3.jpg', 'text': 'In a town called Number Wheels, there were 8 colorful race cars with cool patterns. One day, they decided to have a fun counting race. They zoomed around the track: 1, 2, 3, 4, 5, 6, 7, 8. Each time a car passed a number, it honked happily. At the end of the race, all the cars lined up and the little drivers cheered, "We love numbers and racing too!"', 'question': 'How many race cars zoomed around the track in our story, and what made them happy each time they passed a number?', 'answer': 'Three race cars zoomed around the track, and they felt happy each time they passed a number because they loved counting together.'}]
    return jsonify(data_to_front)

@app.route('/generate_data', methods=['POST'])
@cross_origin(supports_credentials=True)
def generate_data():
    if request.method == 'POST':
        # Parse JSON data sent from the frontend
        frontend_data = request.json

        num_of_images = 3
        subject = frontend_data.get('subject', 'math')
        age_range = frontend_data.get('age_range', '4-6')
        image_entities = frontend_data.get('image_entities', 'white cats')

    Thread(target=call_gpt, args=(num_of_images,subject,age_range,image_entities)).start()
    return Flask.response_class(status=200)

@app.route('/get_data', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_data():
    #if file is empty
    if os.stat('data.json').st_size == 0:
        return Flask.response_class(status=204)
    else:
        with open('data.json', 'r+') as f:
            data_to_front = json.load(f)
        open('data.json', 'w').close()
        print(type(data_to_front))
        return data_to_front

def call_gpt(num_of_images, subject, age_range, image_entities):
    print("Starting GPT-3 API call")
    # API key removed from source for security — use environment variables instead
    API_KEY = "REDACTED_OPENAI_API_KEY"
    client = OpenAI(api_key=API_KEY)

    image_prompt = "Create 3 unique and visually distinct illustrations of {image_entity}, designed specifically for children aged {age_range}. Each image should present the {image_entity} in different contexts or settings that are engaging and appropriate for the specified age group. Ensure that the illustrations are free from any textual elements or recognizable characters. DO NOT INCLUDE ANY CHARACTERS OR TEXT IN IMAGE.".format(image_entity=image_entities, age_range=age_range)
    response = client.images.generate(
        model="dall-e-2",
        prompt=image_prompt,
        size="256x256",
        quality="standard",
        n=num_of_images,
    )

    data = {}

    for i in range(0, num_of_images):
        data[f'url{i+1}'] = response.data[i].url
        
        french_set=''
        french_question=''
        if subject == "French":
            french_set = "in french"
            french_question = "about french grammar"
        
        english_question=''
        if subject == "English":
            english_question = "about english grammar"

        if subject == 'Health':
            subject = 'health and wellness'

        # Continue the conversation to generate a short story
        conversation = [
            {
            "role": "system",
            "content": "As a {subject} teacher, your students have been diagnosed with ADHD and autism. You're tasked with delivering an engaging {subject} lesson tailored to a classroom of students aged {age_range}. The curriculum and teaching methods should be adapted to meet the unique learning needs and preferences of these neurodivergent students, promoting an inclusive and supportive educational environment.".format(subject=subject, age_range=age_range)
            },
            {
            "role": "user",
            "content": [
                {"type": "text", "text": "Craft a new {french} short story, spanning 4-5 sentences, specifically designed for children aged {age_range}. The narrative should be based on the provided image, making clear connections to the subject of {subject}. Use simple, age-appropriate language that resonates with this age group, ensuring the story enriches their understanding of {subject} in a fun and engaging way.".format(french=french_set,age_range=age_range, subject=subject)},
                {
                "type": "image_url",
                "image_url": {
                    "url": response.data[i].url,
                },
                },
            ],
            }
        ]
        # Continue the conversation to get the short story
        story_response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=conversation,
            max_tokens=175,  # Adjust max_tokens as needed
        )
        # Extract the short story from the response
        story = story_response.choices[0].message.content
        
        # Continue a new conversation to generate a question based on the story
        question_conversation = [
            {
                "role": "user",
                "content": "Create a concluding question, framed in one sentence, {fre_grammar}{eng_grammar} designed specifically for students aged {age_range} with autism and ADHD. This question should directly pertain to the short story's content and the classs subject:{subject}, encouraging critical thinking and reflection. Ensure the language is clear, concise, and tailored to accommodate the learning styles of neurodivergent students in this age group, fostering their engagement and understanding. The short story is: {story}".format(eng_grammar=english_question, fre_grammar=french_question, age_range=age_range, subject=subject, story=story)
            }
        ]
        # Continue the conversation to get the question
        question_response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=question_conversation,
            max_tokens=50,  # Adjust max_tokens as needed
        )
        # Extract the question from the response
        question = question_response.choices[0].message.content
        # Continue a new conversation to generate an answer based on the question
        answer_conversation = [
            {
            "role": "user",
            "content": "Compose a one-sentence answer tailored for students aged {age_range} with autism and ADHD. This response should directly address the previously posed question. Ensure the language is straightforward, supportive, and designed to resonate with the cognitive and communication styles typical of neurodivergent students in this age group, aiding their comprehension and engagement. The question to answer is: {question}".format(age_range=age_range, question=question)
            }
        ]
        # Continue the conversation to get the answer
        answer_response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=answer_conversation,
            max_tokens=50,  # Adjust max_tokens as needed
        )
        # Extract the answer from the response
        answer = answer_response.choices[0].message.content
        # Store the data
        data[f'text{i+1}'] = story
        data[f'question{i+1}'] = question
        data[f'answer{i+1}'] = answer
    #take the image from url and use s3 to store it
    for i in range(1, num_of_images+1):
        response = requests.get(data[f'url{i}'])
        img = Image.open(BytesIO(response.content))
        img_path = f"image{i}.jpg"
        img.save(img_path)
        # Initialize the S3 client (credentials redacted)
        s3 = boto3.client('s3', aws_access_key_id='REDACTED_AWS_ACCESS_KEY_ID', aws_secret_access_key='REDACTED_AWS_SECRET_ACCESS_KEY', region_name='us-east-2')
        # Upload the image to your S3 bucket
        bucket_name = 'storybookml'
        s3.upload_file(img_path, bucket_name, img_path, ExtraArgs={'ACL': 'public-read'})
        # Generate the public S3 URL
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{img_path}"
        # Update the data with the S3 URL
        data[f'url{i}'] = s3_url
        # Clean up - remove the local image file
        os.remove(img_path)
    data_to_front = []
    # Iterate over keys in the dictionary to extract data and format it
    for i in range(1, num_of_images+1):
        data_temp = {
            'id': i,
            'url': data[f'url{i}'],
            'text': data[f'text{i}'],
            'question': data[f'question{i}'],
            'answer': data[f'answer{i}']
        }
        data_to_front.append(data_temp)
    print("GPT-3 API call completed")   
    open('data.json', 'w').close()
    with open('data.json', 'a') as f:
        json.dump(data_to_front, f)

    return 

if __name__ == '__main__':
    app.run(debug=True)