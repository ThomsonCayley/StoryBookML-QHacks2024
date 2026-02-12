from openai import OpenAI
import random
import boto3
import requests
import os
from PIL import Image
from io import BytesIO

API_KEY = "REDACTED_OPENAI_API_KEY"
client = OpenAI(api_key=API_KEY)

num_of_images = 3
subject = "math"
age_range = "4-6"
image_entities = ['cats', 'dogs', 'birds', 'fish', 'butterflies', 'flowers', 'trees', 'cars', 'trains', 'boats', 'planes', 'bikes', 'buses', 'trucks', 'buildings', 'houses', 'children']
colors = ['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink', 'brown', 'black', 'white', 'grey']
image_prompt = "Create {num_of_images} unique and visually distinct illustrations of {image_entity}, designed specifically for children aged {age_range}. Each image should present the {image_entity} in different contexts or settings that are engaging and appropriate for the specified age group. Ensure that the illustrations are free from any textual elements or recognizable characters. DO NOT INCLUDE ANY CHARACTERS OR TEXT IN IMAGE.".format(num_of_images=num_of_images, color=random.choice(colors), image_entity=random.choice(image_entities), age_range=age_range)

print(image_prompt)
print(subject)

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

  # Continue the conversation to generate a short story
  conversation = [
      {
      "role": "system",
      "content": "As a {subject} teacher, your students have been diagnosed with ADHD and autism. You're tasked with delivering an engaging {subject} lesson tailored to a classroom of students aged {age_range}. The curriculum and teaching methods should be adapted to meet the unique learning needs and preferences of these neurodivergent students, promoting an inclusive and supportive educational environment.".format(subject=subject, age_range=age_range)
    },
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Craft a new short story, spanning 4-5 sentences, specifically designed for children aged {age_range}. The narrative should be based on the provided image, making clear connections to the subject of {subject}. Use simple, age-appropriate language that resonates with this age group, ensuring the story enriches their understanding of {subject} in a fun and engaging way.".format(age_range=age_range, subject=subject)},
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
      max_tokens=250,  # Adjust max_tokens as needed
  )

  # Extract the short story from the response
  story = story_response.choices[0].message.content
  
  # Continue a new conversation to generate a question based on the story
  question_conversation = [
      {
        "role": "user",
        "content": "Create a concluding question, framed in one sentence, designed specifically for students aged {age_range} with autism and ADHD. This question should directly pertain to the short story's content and the classs subject:{subject}, encouraging critical thinking and reflection. Ensure the language is clear, concise, and tailored to accommodate the learning styles of neurodivergent students in this age group, fostering their engagement and understanding. The short story is: {story}".format(age_range=age_range, subject=subject, story=story)
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
      max_tokens=250,  # Adjust max_tokens as needed
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

#export data_to_front to json file
import json
with open('data_to_front.json', 'w') as f:
  print(data_to_front, file=f)