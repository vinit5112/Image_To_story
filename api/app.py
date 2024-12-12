# app.py
import os
import tempfile
from flask import Flask, request, jsonify, render_template, url_for
from pathlib import Path
import dotenv
dotenv.load_dotenv()
import google.generativeai as genai  # Correct import statement
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)

gemini_api_key = os.getenv('GEMINI_API_KEY')

# Configure genai with the API key
genai.configure(api_key=gemini_api_key)

# Define genres and their prompts
genres = {
    "emotional_drama": """Create a compelling emotional drama centered on: [USER_PROMPT]. Focus on:

    Developing multi-dimensional characters with clear motivations and flaws
    Crafting realistic dialogue that reveals character and advances the plot
    Describing pivotal scenes with sensory details to immerse the reader
    Using internal monologues to explore characters' deepest thoughts and feelings
    Building tension through interpersonal conflicts and internal struggles
    Showing character growth and change over time
    Concluding with a resolution that feels earned and emotionally satisfying""",

    "thriller": """Craft a gripping thriller revolving around: [USER_PROMPT]. Key elements:
    Hook the reader with an intriguing opening scene or premise
    Establish a ticking clock or high stakes to create urgency
    Develop a smart, resourceful protagonist and a formidable antagonist
    Use short, punchy sentences and cliffhanger chapter endings to maintain pace
    Incorporate plot twists and red herrings to keep readers guessing
    Build tension through near-misses and escalating danger
    Climax with a shocking revelation or confrontation
    Resolve the main conflict while potentially leaving a hook for future stories""",

    "psychological_thriller": """Develop a mind-bending psychological thriller exploring: [USER_PROMPT]. Focus on:
    Creating an unreliable narrator or protagonist with a skewed perception of reality
    Blurring the lines between reality and delusion through vivid descriptions
    Using dream sequences or hallucinations to delve into the character's psyche
    Slowly revealing information that makes the reader question earlier assumptions
    Building paranoia and suspicion among characters
    Incorporating psychological themes or concepts relevant to the story
    Culminating in a revelation that forces a reevaluation of the entire narrative""",

    "tragedy": """Compose a poignant tragedy centered on: [USER_PROMPT]. Key aspects:
    Introduce a protagonist with admirable qualities but a fatal flaw
    Create a sense of impending doom through foreshadowing and dramatic irony
    Develop supporting characters whose actions contribute to the tragic outcome
    Show the protagonist making choices that inadvertently lead to their downfall
    Explore themes of fate, choice, and human nature
    Build to a climactic moment where the tragedy becomes inevitable
    Conclude with the fallout of the tragic events and their impact on survivors""",

    "adventure_thriller": """Craft an exhilarating adventure thriller beginning with: [USER_PROMPT]. Elements to include:
    Establish a vivid, exotic setting with its own dangers and wonders
    Create a protagonist forced out of their comfort zone by circumstances
    Introduce a clear goal or quest that drives the story forward
    Balance intense action sequences with quieter moments of character development
    Present moral dilemmas that challenge the protagonist's beliefs and values
    Incorporate unexpected allies and betrayals to keep the story unpredictable
    Show how the adventure transforms the protagonist
    Conclude with a climactic confrontation that ties together the physical and emotional journeys""",

    "romantic_tragedy": """Write a heart-wrenching romantic tragedy focusing on: [USER_PROMPT]. Key components:
    Introduce two lovers with a powerful, immediate connection
    Develop their relationship through tender moments and shared experiences
    Create external obstacles or internal flaws that threaten their love
    Use dramatic irony to build tension as the audience sees the impending heartbreak
    Explore themes of sacrifice, timing, and the nature of love
    Build to a climactic moment where the relationship reaches a point of no return
    Conclude with the bittersweet aftermath and lasting impact of the love story""",

    "suspense_drama": """Develop a taut suspense drama arising from: [USER_PROMPT]. Focus on:
    Establish multiple storylines or character arcs that gradually intertwine
    Use foreshadowing and subtle clues to create a sense of unease
    Slowly reveal secrets that change character dynamics and raise the stakes
    Create morally complex situations with no easy solutions
    Build tension through near-misses and close calls
    Develop a ticking clock element to add urgency
    Culminate in a confrontation that brings all storylines together
    Resolve the main conflict while exploring its lasting consequences""",

    "gothic_thriller": """Create an atmospheric gothic thriller revolving around: [USER_PROMPT]. Key elements:
    Describe a foreboding setting (e.g., crumbling mansion, isolated village) in rich detail
    Establish a brooding atmosphere with vivid sensory descriptions
    Introduce characters haunted by past events or dark secrets
    Incorporate elements of mystery, the supernatural, or psychological horror
    Explore themes of decay, isolation, and the weight of history
    Build tension through unexplained events and growing unease
    Climax with a revelation that ties together the past and present
    Conclude with a resolution that may leave some ambiguity or lingering dread""",

    "action_thriller": """Compose a high-octane action thriller kicking off when: [USER_PROMPT]. Focus on:
    Open with an explosive inciting incident that thrusts the protagonist into action
    Create a clear, high-stakes goal for the protagonist to pursue
    Develop intense, detailed action sequences that advance the plot
    Balance external conflicts with the protagonist's internal struggles
    Introduce unexpected allies and formidable adversaries
    Incorporate betrayals or plot twists to keep the story unpredictable
    Build to a climactic confrontation that tests the protagonist's skills and resolve
    Conclude with a resolution that ties up loose ends while hinting at potential future challenges""",

    "mystery_thriller": """Craft an intriguing mystery thriller centered on: [USER_PROMPT]. Key aspects:
    Open with the discovery of the central mystery or crime
    Introduce a clever protagonist determined to uncover the truth
    Present a cast of suspects, each with potential motives and secrets
    Plant clues and red herrings throughout the narrative
    Use misdirection to keep readers guessing
    Gradually reveal information that forces reevaluation of earlier assumptions
    Build tension as the protagonist gets closer to the truth and faces increasing danger
    Conclude with a surprising yet logical resolution that ties together all the clues""",

    "science_fiction": """Create a captivating science fiction story exploring: [USER_PROMPT]. Key elements:
    Develop a unique, scientifically plausible concept or technology
    Build a detailed and consistent future world or alternate reality
    Create characters whose lives are impacted by the sci-fi elements
    Explore the ethical and societal implications of the central sci-fi concept
    Balance exposition of the sci-fi elements with character development and plot
    Use the sci-fi concept to comment on current social or technological issues
    Build to a climax that fully utilizes the story's sci-fi elements
    Resolve the plot while leaving room for thought about the story's implications""",

    "fantasy": """Craft an enchanting fantasy tale centered on: [USER_PROMPT]. Focus on:
    Create a rich, internally consistent fantasy world with its own rules and logic
    Develop unique magical systems or fantastical elements
    Introduce diverse and interesting non-human characters or creatures
    Balance world-building with character development and plot progression
    Create a quest or conflict that is deeply tied to the fantasy elements
    Explore themes of power, destiny, or the nature of good and evil
    Build to an epic climax that fully utilizes the fantasy elements
    Resolve the main conflict while leaving room for future adventures""",

    "historical_fiction": """Compose a vivid historical fiction story set in: [USER_PROMPT]. Key aspects:
    Research and accurately portray the chosen historical period and setting
    Create characters that embody the values and conflicts of the era
    Weave historical events and figures into the narrative
    Balance historical accuracy with engaging storytelling
    Use period-appropriate dialogue and descriptions
    Explore how historical events impact the characters' lives and decisions
    Build tension through both personal and historical conflicts
    Conclude with a resolution that reflects the historical realities of the time"""
}

# Add this dictionary after your genres dictionary
# genre_icons = {
#     "emotional_drama": "heart",
#     "thriller": "mask",
#     "psychological_thriller": "brain",
#     "tragedy": "theater-masks",
#     "adventure_thriller": "mountain",
#     "romantic_tragedy": "heartbreak",
#     "suspense_drama": "hourglass",
#     "gothic_thriller": "ghost",
#     "action_thriller": "running",
#     "mystery_thriller": "magnifying-glass"
# }

genre_icons = {
"emotional_drama": "heart",
"thriller": "mask",
"psychological_thriller": "brain",
"tragedy": "theater-masks",
"adventure_thriller": "mountain",
"romantic_tragedy": "heartbreak",
"suspense_drama": "hourglass",
"gothic_thriller": "ghost",
"action_thriller": "running",
"mystery_thriller": "magnifying-glass",
"science_fiction": "rocket",
"fantasy": "wand-magic-sparkles",
"historical_fiction": "landmark"
} 
def use_gemini(image_path, genre, user_prompt, story_length):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            media = Path(image_path)
            myfile = genai.upload_file(media)
            
            genre_prompt = genres.get(genre, "Write a story about:")
            full_prompt = genre_prompt.replace("[USER_PROMPT]", user_prompt)
            
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

            Adapt these guidelines to fit your specific genre, prompt, and storytelling goals. Create a cohesive, engaging narrative that brings your unique vision to life.
            """
            
            if story_length == "short":
                additional_instructions += "\nAim for a word count between 500-800 words."
                max_tokens = 2048
            else:  # long story
                additional_instructions += "\nAim for a word count between 1000-1500 words."
                max_tokens = 4096
            
            full_prompt += "\n\n" + additional_instructions
            
            model = genai.GenerativeModel("gemini-1.5-flash")
            start_time = time.time()
            response = model.generate_content(
                [myfile, full_prompt],
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": 0.7,
                    "top_p": 1,
                    "top_k": 32
                }
            )
            duration = time.time() - start_time
            print(f"API call duration: {duration} seconds")
            return True, response.text
        except Exception as e:
            if "504" in str(e):  # Check for timeout error
                print(f"Timeout error. Attempt {attempt + 1} of {max_retries}. Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Error in use_gemini: {str(e)}")
                return False, f'Error with Gemini API: {str(e)}'
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

    success, story = use_gemini(temp_file_path, genre, user_prompt, story_length)
    
    if not success:
        return jsonify({'error': story}), 429

    # Clean up the temporary file if needed (optional, depending on your use case)
    os.remove(temp_file_path)  # Remove the temporary file after use

    return jsonify({'story': story})

if __name__ == '__main__':
    app.run(debug=True)
