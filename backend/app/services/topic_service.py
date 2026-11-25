import json
import logging
import random
import re
from typing import Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger("TamilKidsAI.Topics")

# Fixed character descriptions: reuse in every image prompt so characters look the same in all scenes.
CHARACTERS = {
    "சின்னு": "Chinnu, a round orange fox cub with big shiny eyes and a blue scarf",
    "முயல்": "Mini, a fluffy white bunny with long ears and a red backpack",
    "ஆமை": "Aami, a kind green turtle with a yellow shell and round glasses",
    "யானை": "Gaja, a gentle baby elephant with big ears and a green cap",
    "குரங்கு": "Kutty, a playful brown monkey with a striped shirt",
    "காகம்": "Kaaku, a clever black crow with a tiny orange bag",
}

LESSONS = [
    "உண்மை பேசுவது", "பகிர்ந்து கொள்வது", "நட்பின் மதிப்பு", "கடின உழைப்பு",
    "பொறுமை", "நன்றி சொல்வது", "பெரியவர்களை மதிப்பது", "தைரியம்",
    "ஒற்றுமை", "சுத்தமாக இருப்பது", "உதவி செய்வது", "பேராசை கூடாது",
    "நேரத்தை மதிப்பது", "மன்னிப்பு கேட்பது", "முயற்சியை கைவிடாதே", "இயற்கையை காப்போம்",
]
PLACES = [
    "காட்டில்", "கிராமத்தில்", "ஆற்றங்கரையில்", "மலை அடிவாரத்தில்", "பள்ளியில்",
    "சந்தையில்", "கடற்கரையில்", "தோட்டத்தில்", "குளக்கரையில்", "திருவிழாவில்",
]
TITLE_FORMS = [
    "{c} மற்றும் {l}", "{c}வின் {p} ஒரு நாள்", "{p} {c} கற்ற பாடம்: {l}",
    "{c}வின் அதிசய பயணம் - {l}",
]


class TopicService:
    def _fallback(self, count: int, used: set) -> List[Dict]:
        """Offline generator: thousands of unique combos, never runs out."""
        out, tries = [], 0
        names = list(CHARACTERS.keys())
        while len(out) < count and tries < 2000:
            tries += 1
            c, l, p = random.choice(names), random.choice(LESSONS), random.choice(PLACES)
            title = random.choice(TITLE_FORMS).format(c=c, l=l, p=p)
            if title in used or any(o["title_tamil"] == title for o in out):
                continue
            out.append({
                "title_tamil": title, "moral": l, "character": CHARACTERS[c],
                "location": p, "category": "நீதிக்கதை",
            })
        return out

    def _gemini(self, count: int, used: List[str]) -> Optional[List[Dict]]:
        if not settings.GEMINI_API_KEY:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            chars = "; ".join(CHARACTERS.values())
            prompt = (
                f"Create {count} NEW Tamil moral story ideas for kids aged 3-8. "
                f"Use only these recurring characters: {chars}. "
                f"Do NOT repeat or closely resemble these existing titles: {used[-60:]}. "
                'Return ONLY a JSON array, each item: {"title_tamil": str, "moral": str (Tamil), '
                '"character": str (copy exact description from list), "location": str, "category": "நீதிக்கதை"}'
            )
            text = model.generate_content(prompt).text
            text = re.sub(r"```(?:json)?", "", text).strip()
            data = json.loads(text)
            return [d for d in data if isinstance(d, dict) and d.get("title_tamil")]
        except Exception as e:
            logger.warning(f"Gemini topic generation failed: {e}")
            return None

    def get_topics(self, count: int = 5, used_titles: Optional[List[str]] = None) -> List[Dict]:
        """Always returns `count` topics not in used_titles."""
        used = list(used_titles or [])
        used_set = set(used)
        topics = [t for t in (self._gemini(count, used) or []) if t["title_tamil"] not in used_set]
        if len(topics) < count:
            seen = used_set | {t["title_tamil"] for t in topics}
            topics += self._fallback(count - len(topics), seen)
        return topics[:count]
