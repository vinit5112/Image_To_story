import os
import tempfile
from flask import Flask, request, jsonify, render_template, url_for
from pathlib import Path
import dotenv
dotenv.load_dotenv()
from groq import Groq
from werkzeug.utils import secure_filename
import time
import base64

app = Flask(__name__)

# Get Groq API key from environment
groq_api_key = os.getenv('GROQ_API_KEY')

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Keep the existing genres dictionary
genres = {
    # ... (keep the existing genres dictionary from the previous script)
}

genre_icons = {
    # ... (keep the existing genre_icons dictionary)
}

def encode_image(image_path):
    """Encode image to base64 for Vision API"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def use_groq(image_path, genre, user_prompt, story_length):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Encode the image
            base64_image = encode_image(image_path)
            
            # Get the genre-specific prompt
            genre_prompt = genres.get(genre, "Write a story about:")
            full_prompt = genre_prompt.replace("[USER_PROMPT]", user_prompt)
            
            # Additional storytelling guidelines
            additional_instructions = f"""
            Based on the image provided and the story prompt, create a compelling narrative following these guidelines:

            1. Visual Integration:
            • Analyze the image for key elements, colors, mood, and symbols.
            • Incorporate visual details to enhance setting, atmosphere, and character descriptions.
            • Use the image to inspire unique plot elements or twists.

            2. Character Development:
            • Create 3-4 main characters with distinct personalities, backgrounds, and motivations.
            • Ensure each character has a clear arc or journey.
            • Develop complex, evolving relationships between characters.
            • Reveal character traits through description, dialogue, and actions.

            3. Story Structure:
            • Craft a compelling opening hook.
            • Establish setting, introduce key characters, and present the central conflict.
            • Build rising action, incrementally raising stakes and tension.
            • Create a climactic moment that brings the central conflict to a head.
            • Conclude with a satisfying resolution, possibly leaving room for reflection.

            4. Sensory Storytelling:
            • Engage all five senses in descriptions for an immersive experience.
            • Use sensory details to establish mood and enhance characterization.
            • Balance sensory descriptions with action and dialogue.

            5. Dialogue and Interaction:
            • Craft natural, character-specific dialogue that reveals personality and advances the plot.
            • Use dialogue to create tension, provide exposition, and deepen relationships.
            • Balance dialogue with narrative description and internal monologue.

            6. Thematic Development:
            • Identify and explore central themes relevant to your genre and prompt.
            • Weave thematic elements throughout the story organically.

            7. Genre-Specific Elements:
            • Incorporate key elements of the chosen genre (refer to genre descriptions).
            • Use genre conventions creatively, potentially subverting or reimagining them.
            • Ensure genre elements serve the story and character development.

            8. Pacing and Tension:
            • Vary sentence and paragraph length to control pacing and emphasis.
            • Create moments of tension and release throughout the story.
            • Use foreshadowing and plant subtle clues for later payoff.

            9. World-Building (if applicable):
            • Develop a rich, internally consistent world that enhances the story.
            • Reveal world details gradually through character interactions and plot events.
            • Consider how the world's unique elements impact character motivations and plot.

            10. Emotional Resonance:
                • Evoke specific emotions in the reader that align with your genre and story goals.
                • Show characters' emotional journeys through thoughts, actions, and physical reactions.
                • Create emotionally impactful moments that resonate with universal human experiences.
            """
            
            # Adjust story length
            if story_length == "short":
                additional_instructions += "\nAim for a word count between 500-800 words."
                max_tokens = 1024
            else:  # long story
                additional_instructions += "\nAim for a word count between 1000-1500 words."
                max_tokens = 2048
            
            # Combine prompts
            full_prompt += "\n\n" + additional_instructions
            
            # Prepare messages for Groq API
            messages = [
                {
                    "role": "system",
                    "content": "You are a creative writing assistant who excels at generating compelling stories based on image and genre prompts."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": full_prompt
                        }
                    ]
                }
            ]
            
            # Start timing the API call
            start_time = time.time()
            
            # Generate story using Groq API
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens,
                top_p=1,
                stream=False
            )
            
            # Calculate and print duration
            duration = time.time() - start_time
            print(f"API call duration: {duration} seconds")
            
            # Return the generated story
            return True, response.choices[0].message.content
        
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error in use_groq: {str(e)}. Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Final error in use_groq: {str(e)}")
                return False, f'Error with Groq API: {str(e)}'
    
    return False, 'Max retries exceeded. Please try again later.'

@app.route('/')
def index():
    return render_template('index.html', genres=genres, genre_icons=genre_icons)

@app.route('/generate-story', methods=['POST'])
def generate_story():
    image = request.files.get('image')
    genre = request.form.get('genre')
    user_prompt = request.form.get('prompt')
    story_length = request.form.get('story_length')
    
    if not image or not genre or not user_prompt or not story_length:
        return jsonify({'error': 'Please provide all required fields: image, genre, prompt, and story length.'}), 400

    # Create a temporary file to store the uploaded image
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
        image.save(temp_file.name)  # Save the uploaded image to the temporary file
        temp_file_path = temp_file.name  # Get the path of the temporary file

    success, story = use_groq(temp_file_path, genre, user_prompt, story_length)
    
    if not success:
        return jsonify({'error': story}), 429

    # Clean up the temporary file
    os.remove(temp_file_path)  # Remove the temporary file after use

    return jsonify({'story': story})

if __name__ == '__main__':
    app.run(debug=True)
