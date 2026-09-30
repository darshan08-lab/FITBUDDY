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


def _fallback_updated_plan(original_plan, feedback):

    text = feedback.lower()

    intensity_note = "Keep the intensity moderate and comfortable."

    if any(
        word in text
        for word in [
            "easy",
            "difficult",
            "hard",
            "too much",
            "beginner"
        ]
    ):
        intensity_note = (
            "Reduce intensity, use controlled movements, "
            "and take extra rest whenever needed."
        )

    home_note = ""

    if any(
        word in text
        for word in [
            "home",
            "equipment",
            "gym"
        ]
    ):
        home_note = (
            "Use bodyweight or common home alternatives "
            "instead of gym machines."
        )

    cardio_note = ""

    if "cardio" in text:
        cardio_note = (
            "Add 15-25 minutes of comfortable walking "
            "or cycling on cardio days."
        )

    yoga_note = ""

    if "yoga" in text or "stretch" in text:
        yoga_note = (
            "Add 10-15 minutes of gentle yoga or "
            "stretching on recovery days."
        )

    return f"""UPDATED FITBUDDY 7-DAY WORKOUT PLAN

The plan has been adjusted based on your feedback:

"{feedback}"

{intensity_note}

{home_note}

{cardio_note}

{yoga_note}


DAY 1 - FULL BODY

- Warm-up: 5-10 minutes
- Bodyweight Squats: 3 x 10
- Incline Push-ups: 3 x 8
- Glute Bridges: 3 x 12
- Bird Dog: 2 x 10 each side
- Cooldown: 5 minutes


DAY 2 - CARDIO + CORE

- Brisk Walk: 20 minutes
- Dead Bug: 3 x 8 each side
- Plank: 3 x 20 seconds
- Gentle stretching: 5 minutes


DAY 3 - RECOVERY

- Easy walk: 15-20 minutes
- Gentle stretching/yoga: 10-15 minutes
- Focus on hydration and sleep


DAY 4 - FULL BODY

- Warm-up: 5-10 minutes
- Reverse Lunges: 3 x 8 each leg
- Incline Push-ups: 3 x 8
- Hip Hinge: 3 x 10
- Shoulder Taps: 2 x 10 each side
- Cooldown: 5 minutes


DAY 5 - CARDIO + CORE

- Brisk Walk or cycling: 20-25 minutes
- Glute Bridges: 3 x 12
- Side Plank: 2 x 15-20 seconds each side
- Gentle stretching: 5 minutes


DAY 6 - LIGHT STRENGTH

- Chair Squats: 3 x 10
- Wall Push-ups: 3 x 10
- Calf Raises: 3 x 12
- Standing Knee Raises: 2 x 10 each side


DAY 7 - REST / ACTIVE RECOVERY

- Easy walk: 15-20 minutes if comfortable
- Gentle stretching: 10 minutes


SAFETY

Progress gradually. Stop if you experience pain, dizziness, or unusual symptoms.
"""


def update_workout_plan_with_feedback(
    original_plan,
    feedback
):

    prompt = f"""
You are FitBuddy, an AI fitness assistant.

Original workout plan:

{original_plan}

User feedback:

{feedback}

Create an updated 7-day workout plan.

Requirements:
- Meaningfully respond to the feedback.
- Keep it practical and beginner-friendly.
- Include Day 1 through Day 7.
- Include exercises, sets, repetitions or duration.
- Include recovery when appropriate.
- Do not provide dangerous or extreme instructions.
- Return only the updated workout plan.
"""

    if client is None:
        return _fallback_updated_plan(
            original_plan,
            feedback
        )

    for model_name in ["gemini-2.5-flash", "gemini-1.5-flash"]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"Gemini feedback error with {model_name}: {e}. Retrying/falling back.")

    return _fallback_updated_plan(
        original_plan,
        feedback
    )