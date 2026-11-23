import json
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.all_models import Topic, Story, Script

logger = logging.getLogger("TamilKidsAI.StoryGenerator")

# Safety categories for kids
KIDS_CATEGORIES = [
    "விலங்கு கதைகள் (Animal Stories)",
    "நட்பு மற்றும் ஒற்றுமை (Friendship & Unity)",
    "நேர்மை மற்றும் உண்மை (Honesty & Truth)",
    "பகிர்ந்து உண்ணுதல் (Sharing & Generosity)",
    "தைரியம் மற்றும் விடாமுயற்சி (Courage & Perseverance)",
    "இயற்கை மற்றும் மரங்கள் (Nature & Environment)",
    "பெரியவர்களை மதித்தல் (Respecting Elders)",
    "சுத்தம் மற்றும் நற்பழக்கங்கள் (Cleanliness & Good Habits)"
]

class AIStoryGeneratorService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._init_gemini()

    def _init_gemini(self):
        self.client = None
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(settings.GEMINI_MODEL)
                logger.info(f"Gemini AI initialized with model: {settings.GEMINI_MODEL}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {e}")

    def generate_daily_topic(self, db: Session) -> Topic:
        """
        Picks the least recently used category, checks for duplicate topics,
        and generates an original Tamil kids' story topic.
        """
        # Fetch existing topics to avoid duplicates
        existing_topics = db.query(Topic.title_tamil).all()
        existing_titles = [t[0] for t in existing_topics]
        
        # Determine category rotation
        category = KIDS_CATEGORIES[len(existing_titles) % len(KIDS_CATEGORIES)]
        
        if self.client:
            prompt = f"""
You are an expert Tamil children's story writer and educator.
Create a brand-new, original, captivating Tamil story topic for young children (ages 4-10).

Target Category: {category}
Avoid existing topics: {", ".join(existing_titles[-10:])}

Rules:
1. Output MUST be valid JSON only. No markdown formatting, no code blocks.
2. Must be positive, gentle, and have an uplifting moral.
3. No violence, scary monsters, deceit, or negative behavior.

JSON Schema:
{{
  "title_tamil": "கதையின் தலைப்பு தமிழில் (எ.கா. வண்ணத்துப்பூச்சியும் சுட்டி முயலும்)",
  "title_english": "English Title",
  "category": "{category}",
  "target_moral": "கதை உணர்த்தும் நீதி தமிழில்",
  "synopsis": "சுருக்கமான கதைக்களம் (2-3 வாக்கியங்கள்)"
}}
"""
            try:
                response = self.client.generate_content(prompt)
                clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_text)
                
                # Check near duplicate
                if data["title_tamil"] in existing_titles:
                    data["title_tamil"] += f" - பகுதி {len(existing_titles) + 1}"
                    
                topic = Topic(
                    title_tamil=data["title_tamil"],
                    title_english=data.get("title_english", "Kids Tamil Story"),
                    category=category,
                    target_moral=data["target_moral"],
                    synopsis=data.get("synopsis", ""),
                    status="approved"
                )
                db.add(topic)
                db.commit()
                db.refresh(topic)
                return topic
            except Exception as e:
                logger.warning(f"Gemini topic generation failed ({e}), falling back to curated curriculum.")

        # High-quality offline fallback curriculum
        fallback_catalogue = [
            ("சுட்டி முயலும் உதவி செய்யும் அணிலும்", "The Helpful Bunny and Squirrel", "நட்பு மற்றும் ஒற்றுமை", "ஆபத்தில் உதவுபவனே உண்மையான நண்பன்", "காட்டில் தொலைந்துபோன கேரட்டை தேட முயலுக்கு அணில் உதவும் கதை."),
            ("பாட்டி வைத்த சுவையான மாம்பழம்", "Grandma's Sweet Mango", "பகிர்ந்து உண்ணுதல்", "பகிர்ந்து உண்பதில் கிடைக்கும் மகிழ்ச்சியே பெரிது", "ஒரு சுவையான மாம்பழத்தை தன் நண்பர்களுடன் பகிர்ந்து சாப்பிடும் சிறுவனின் கதை."),
            ("உண்மையே பேசிய குட்டி மான்", "The Little Deer Who Spoke the Truth", "நேர்மை மற்றும் உண்மை", "எப்போதும் உண்மையே பேச வேண்டும்", "குவளையை உடைத்துவிட்டாலும் பொய் சொல்லாமல் அம்மாவிடம் உண்மை சொல்லும் குட்டி மான்."),
            ("சின்ன குருவியின் பெரிய முயற்சி", "The Little Sparrow's Big Effort", "தைரியம் மற்றும் விடாமுயற்சி", "விடாமுயற்சி வெற்றியைத் தரும்", "மழைக் காலத்தில் தன் கூட்டை உறுதியாக கட்ட விடாமுயற்சி செய்யும் சிட்டுக்குருவி."),
            ("மரம் நண்பனின் பரிசு", "The Friendly Tree's Gift", "இயற்கை மற்றும் மரங்கள்", "மரங்களை நாம் பாதுகாக்க வேண்டும்", "கோடை வெயிலில் நிழல் தந்த மரத்திற்கு நன்றி செலுத்தும் கிராமத்துச் சிறுவர்கள்.")
        ]
        
        idx = len(existing_titles) % len(fallback_catalogue)
        item = fallback_catalogue[idx]
        title = item[0] if item[0] not in existing_titles else f"{item[0]} (புதிய கதை)"
        
        topic = Topic(
            title_tamil=title,
            title_english=item[1],
            category=item[2],
            target_moral=item[3],
            synopsis=item[4],
            status="approved"
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)
        return topic

    def generate_full_story(self, topic: Topic, db: Session) -> Story:
        """
        Generates a rich, engaging, 10-15 minute conversational Tamil narrative.
        """
        if self.client:
            prompt = f"""
You are a warm, lovable Tamil storyteller (கதை சொல்லும் பாட்டி/மாமா) speaking to children.
Write a complete, original, engaging children's story in Tamil based on this topic.

Topic: {topic.title_tamil} ({topic.title_english})
Category: {topic.category}
Moral: {topic.target_moral}
Synopsis: {topic.synopsis}

Guidelines:
1. Language: Simple, pure, sweet, conversational Tamil (எளிய, அழகான, இனிமையான தமிழ்).
2. Pacing: 10 to 12 minutes spoken duration (rich description, lively character interactions, sound effects like 'சலசலவென', 'துள்ளிக்குதித்து').
3. Structure:
   - அழகான தொடக்கம் (Introduction of picturesque village/forest setting and characters)
   - சுவாரசியமான நிகழ்வு (The curiosity / challenge / day's adventure)
   - உதவி மற்றும் தீர்வு (Climax solved through kindness, teamwork, and wisdom)
   - நிறைவான நீதி (Uplifting moral concluded warmly)
4. JSON Output format ONLY:
{{
  "title_tamil": "{topic.title_tamil}",
  "moral_tamil": "{topic.target_moral}",
  "characters": [
    {{"name_tamil": "சின்னான்", "name_english": "Chinnan", "role": "குறும்புக்கார முயல்", "visual_appearance": "வெள்ளை நிற பஞ்சு போன்ற மென்மையான ரோமம், நீளமான காதுகள், சிவப்பு நிற சுட்டி கண்கள், பச்சை நிற அரைக்கால் சட்டை"}},
    {{"name_tamil": "அப்பு", "name_english": "Appu", "role": "அன்பான குட்டி யானை", "visual_appearance": "சாம்பல் நிறம், எடுப்பான சிறிய தும்பிக்கை, மஞ்சள் நிற தொப்பி"}}
  ],
  "full_story_tamil": "முழுமையான கதை உரை..."
}}
"""
            try:
                response = self.client.generate_content(prompt)
                clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_text)
                
                story_text = data["full_story_tamil"]
                words = len(story_text.split())
                
                story = Story(
                    topic_id=topic.id,
                    title_tamil=data.get("title_tamil", topic.title_tamil),
                    moral_tamil=data.get("moral_tamil", topic.target_moral),
                    full_story_tamil=story_text,
                    character_bible=data.get("characters", []),
                    word_count=words,
                    target_duration_seconds=max(600, int(words * 0.45)),  # approx 130 words/min
                    status="approved"
                )
                db.add(story)
                db.commit()
                db.refresh(story)
                return story
            except Exception as e:
                logger.warning(f"Gemini story generation failed ({e}), using default rich story template.")

        # Default rich template
        sample_story_text = f"""
அன்பு குழந்தைகளே! வணக்கம்! இன்று நாம் பார்க்கப்போகும் அழகான கதை: {topic.title_tamil}.

ஒரு அடர்ந்த, பசுமையான காடு. அந்தக் காட்டில் உயரமான மரங்களும், வண்ண வண்ண மலர்களும், சலசலவென ஓடும் ஒரு சிறிய நீரோடையும் இருந்தது. அங்கே குட்டி முயல் ஒன்று தன் அம்மாவுடன் வசித்து வந்தது. அந்த முயலுக்கு எல்லாவற்றையும் தெரிந்துகொள்ளும் ஆர்வம் அதிகம்.

ஒரு நாள் காலைப் பொழுதில், கதிரவனின் பொன்னொளிக் கதிர்கள் காடெங்கும் பரவியது. குட்டி முயல் துள்ளிக்குதித்து வெளியே வந்தது. காற்றில் மெல்லிய பூக்களின் வாசனை வீசியது. மரத்தின் கிளையில் அமர்ந்திருந்த சிட்டுக்குருவி கீச் கீச் என்று இனிமையாக பாடியது.

"காலை வணக்கம் நண்பா!" என்று முயல் உற்சாகமாகக் குரல் கொடுத்தது.

அப்போது மரத்தடியில் ஒரு பழுத்த, இனிமையான பழம் விழுந்து கிடந்தது. அந்தப் பழத்தை பார்த்ததும் முயலுக்கு நாவில் எச்சில் ஊறியது. ஆனால், சற்று தூரத்தில் தன் நண்பனான அணில் பசியோடு உணவைத் தேடிக்கொண்டிருப்பதை முயல் பார்த்தது.

முயல் ஒரு கணம் யோசித்தது. 'இந்தப் பழம் மிகவும் சுவையாக இருக்கும், நான் மட்டுமே சாப்பிட்டுவிடலாமா? அல்லது நண்பனுடன் பகிர்ந்து கொள்ளலாமா?' என்று நினைத்தது.

உடனே முயல் புன்னகையோடு, "நண்பா அணிலே! இங்கே வா! எனக்கொரு சுவையான பழம் கிடைத்தது. நாம் இருவரும் சேர்ந்து சமமாகப் பகிர்ந்து சாப்பிடலாம்!" என்று அழைத்தது.

அணில் மிகுந்த மகிழ்ச்சியோடு ஓடிவந்தது. இருவரும் மகிழ்ச்சியாக அந்தப் பழத்தைப் பகிர்ந்து உண்டார்கள். பகிர்வதில் தான் எத்தனை பெரிய மகிழ்ச்சி!

நீதி: {topic.target_moral}.
"""
        words = len(sample_story_text.split())
        story = Story(
            topic_id=topic.id,
            title_tamil=topic.title_tamil,
            moral_tamil=topic.target_moral,
            full_story_tamil=sample_story_text.strip(),
            character_bible=[
                {"name_tamil": "குட்டி முயல்", "name_english": "Bunny", "role": "முதன்மைக் கதாபாத்திரம்", "visual_appearance": "வெள்ளை ரோமம், இளஞ்சிவப்பு காதுகள்"},
                {"name_tamil": "சிட்டுக்குருவி", "name_english": "Sparrow", "role": "நண்பன்", "visual_appearance": "பழுப்பு மற்றும் மஞ்சள் சிறகுகள்"},
                {"name_tamil": "அணில்", "name_english": "Squirrel", "role": "பசி கொண்ட நண்பன்", "visual_appearance": "நீளமான வாலுடன் மூன்று கோடுகள் கொண்ட அணில்"}
            ],
            word_count=words,
            target_duration_seconds=600,
            status="approved"
        )
        db.add(story)
        db.commit()
        db.refresh(story)
        return story

    def generate_scene_script(self, story: Story, db: Session) -> Script:
        """
        Converts the story into a structured 3D scene-by-scene script for Blender & video rendering.
        """
        if self.client:
            prompt = f"""
Convert this Tamil kids' story into a structured scene-by-scene 3D production script.

Story Title: {story.title_tamil}
Full Story: {story.full_story_tamil}
Characters: {json.dumps(story.character_bible, ensure_ascii=False)}

Rules:
1. Divide the story into 8 to 14 coherent scenes totaling ~600 seconds.
2. For each scene, specify camera movement, character actions, expressions, Tamil narration chunk, and sound cues.
3. Output MUST be valid JSON only matching this schema:
{{
  "scene_count": 8,
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 45,
      "location": "sunlit_forest_clearing",
      "camera_movement": "Slow pan left to right establishing the lush green forest and morning sunlight",
      "characters_present": ["குட்டி முயல்"],
      "actions": "முயல் பொந்தில் இருந்து துள்ளி வெளியே வந்து புற்களில் அமர்கிறது",
      "expressions": "மகிழ்ச்சியான புன்னகை, கண்கள் மலர்ந்த பார்வை",
      "narration_tamil": "அன்பு குழந்தைகளே! வணக்கம்! இன்று நாம் பார்க்கப்போகும் அழகான கதை...",
      "dialogue_tamil": "",
      "sfx_cue": "birds_morning_ambience",
      "lighting_mood": "warm_morning"
    }}
  ]
}}
"""
            try:
                response = self.client.generate_content(prompt)
                clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_text)
                
                script = Script(
                    story_id=story.id,
                    scene_count=len(data.get("scenes", [])),
                    scenes=data.get("scenes", []),
                    shot_list={"target_resolution": "1920x1080", "fps": 24}
                )
                db.add(script)
                db.commit()
                db.refresh(script)
                return script
            except Exception as e:
                logger.warning(f"Gemini script generation failed ({e}), using structured breakdown.")

        # Default structured breakdown into 8 scenes
        paragraphs = [p.strip() for p in story.full_story_tamil.split("\n\n") if p.strip()]
        scenes = []
        for i, para in enumerate(paragraphs, 1):
            scenes.append({
                "scene_number": i,
                "duration_seconds": 60,
                "location": "lush_village_forest",
                "camera_movement": "Slow cinematic pan with soft focal blur on characters",
                "characters_present": ["குட்டி முயல்", "அணில்"],
                "actions": "கதாபாத்திரங்கள் மெதுவாக அசைந்து உரையாடுகின்றன",
                "expressions": "அன்பும் மகிழ்ச்சியும் நிறைந்த முகபாவனை",
                "narration_tamil": para,
                "dialogue_tamil": "",
                "sfx_cue": "nature_stream_gentle_wind",
                "lighting_mood": "soft_golden_hour"
            })
            
        script = Script(
            story_id=story.id,
            scene_count=len(scenes),
            scenes=scenes,
            shot_list={"target_resolution": "1920x1080", "fps": 24}
        )
        db.add(script)
        db.commit()
        db.refresh(script)
        return script
