# Storybook ML 📚

**Built at QHacks 2024 (Queen's University Hackathon)**

Storybook ML is a mobile application designed to assist teachers by generating customized stories and comprehension questions based on a student's specific interests. By leveraging Generative AI, it turns generic reading exercises into engaging, personalized learning experiences.

## Key Features

* **Custom Story Generation:** Takes student interests (e.g., "dinosaurs," "space," "soccer") to generate unique stories instantly.
* **Automated Comprehension:** Automatically generates relevant questions to test reading comprehension alongside the text.
* **Real-Time Streaming:** Features a high-concurrency Python backend to handle multiple requests and stream content without latency.
* **Teacher-Centric UI:** Designed for quick usage in a classroom setting.

## Tech Stack

* **Frontend:** React Native (Mobile iOS/Android)
* **Backend:** Python (Multithreaded Architecture)
* **AI Engine:** OpenAI API
* **Tools:** Git, GitHub Actions

## Architecture Highlights

* **High-Concurrency Backend:** Utilizes Python multithreading to handle simultaneous API requests, ensuring the app remains responsive under load.
* **Seamless Integration:** Direct integration with OpenAI APIs allows for dynamic, context-aware content generation.# StoryBookML-QHacks2024
