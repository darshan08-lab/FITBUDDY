import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = None
if API_KEY and API_KEY.strip():
    try:
        client = genai.Client(api_key=API_KEY.strip())
    except Exception as e:
        print(f"Failed to initialize Gemini client: {e}")
        client = None


def _fallback_nutrition(goal, age, weight):

    return f"""NUTRITION & RECOVERY TIP

For your {goal} goal, focus on balanced meals containing:

- A protein source such as eggs, chicken, fish, beans, paneer, or Greek yogurt.
- Vegetables and fruit for vitamins and fiber.
- Whole grains or other practical carbohydrate sources for energy.
- Healthy fats in moderate portions.

Hydration:

Drink water regularly throughout the day and around your workouts.

Recovery:

Aim for consistent sleep and give your body enough recovery time between harder sessions.

This is general wellness guidance, not medical advice.
"""


def generate_nutrition_tip_with_flash(goal, age, weight):

    prompt = f"""
You are FitBuddy, an AI fitness assistant.

Create a concise nutrition and recovery tip.

Age: {age}
Weight: {weight} kg
Fitness goal: {goal}

Requirements:
- Practical nutrition advice.
- Hydration advice.
- Recovery advice.
- Simple and beginner-friendly.
- No extreme diets or dangerous medical advice.
"""

    if client is None:
        return _fallback_nutrition(goal, age, weight)

    for model_name in ["gemini-2.5-flash", "gemini-1.5-flash"]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"Gemini nutrition error with {model_name}: {e}. Retrying/falling back.")

    return _fallback_nutrition(goal, age, weight)