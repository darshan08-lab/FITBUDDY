from fastapi import FastAPI, Request, Form, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel

from app.database import (
    save_user,
    get_all_users,
    get_user,
    update_workout_plan,
    save_feedback,
)

app = FastAPI(title="FitBuddy - AI Fitness Plan Generator")

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "FitBuddy"}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )


class WorkoutRequest(BaseModel):
    name: str
    age: int
    weight: str
    goal: str
    intensity: str


@app.post("/generate-workout", response_class=HTMLResponse)
async def generate_workout(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    weight: str = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...)
):
    from app.gemini_generator import generate_workout_gemini
    from app.gemini_flash_generator import generate_nutrition_tip_with_flash

    workout_plan = generate_workout_gemini(
        name=name,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity
    )

    nutrition_tip = generate_nutrition_tip_with_flash(
        goal=goal,
        age=age,
        weight=weight
    )

    user = save_user(
        name=name,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity,
        workout_plan=workout_plan,
        nutrition_tip=nutrition_tip
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "request": request,
            "user": user,
            "workout_plan": workout_plan,
            "nutrition_tip": nutrition_tip
        }
    )


@app.post("/api/generate-workout")
async def api_generate_workout(data: WorkoutRequest):
    from app.gemini_generator import generate_workout_gemini
    from app.gemini_flash_generator import generate_nutrition_tip_with_flash

    workout_plan = generate_workout_gemini(
        name=data.name,
        age=data.age,
        weight=data.weight,
        goal=data.goal,
        intensity=data.intensity
    )

    nutrition_tip = generate_nutrition_tip_with_flash(
        goal=data.goal,
        age=data.age,
        weight=data.weight
    )

    user = save_user(
        name=data.name,
        age=data.age,
        weight=data.weight,
        goal=data.goal,
        intensity=data.intensity,
        workout_plan=workout_plan,
        nutrition_tip=nutrition_tip
    )

    return {
        "status": "success",
        "user": {
            "id": user.id,
            "name": user.name,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity
        },
        "workout_plan": workout_plan,
        "nutrition_tip": nutrition_tip
    }


@app.post("/submit-feedback", response_class=HTMLResponse)
async def submit_feedback(
    request: Request,
    user_id: int = Form(...),
    feedback: str = Form(...)
):
    from app.updated_plan import update_workout_plan_with_feedback

    user = get_user(user_id)

    if not user:
        return HTMLResponse(
            content="User not found. Please check the User ID.",
            status_code=404
        )

    feedback = feedback.strip()

    if not feedback:
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "request": request,
                "user": user,
                "workout_plan": user.workout_plan,
                "nutrition_tip": user.nutrition_tip,
                "feedback_message": "Please enter some feedback before submitting."
            }
        )

    save_feedback(
        user_id=user_id,
        feedback=feedback
    )

    new_plan = update_workout_plan_with_feedback(
        original_plan=user.workout_plan,
        feedback=feedback
    )

    updated_user = update_workout_plan(
        user_id=user_id,
        new_plan=new_plan
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "request": request,
            "user": updated_user,
            "workout_plan": new_plan,
            "nutrition_tip": updated_user.nutrition_tip,
            "feedback_message": "Your workout plan has been updated successfully."
        }
    )


class FeedbackRequest(BaseModel):
    user_id: int
    feedback: str


@app.post("/api/submit-feedback")
async def api_submit_feedback(data: FeedbackRequest):
    from app.updated_plan import update_workout_plan_with_feedback

    user = get_user(data.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    feedback_text = data.feedback.strip()

    if not feedback_text:
        raise HTTPException(status_code=400, detail="Feedback cannot be empty.")

    save_feedback(user_id=data.user_id, feedback=feedback_text)

    new_plan = update_workout_plan_with_feedback(
        original_plan=user.workout_plan,
        feedback=feedback_text
    )

    updated_user = update_workout_plan(user_id=data.user_id, new_plan=new_plan)

    return {
        "status": "success",
        "user": {
            "id": updated_user.id,
            "name": updated_user.name,
            "workout_plan": updated_user.workout_plan
        },
        "workout_plan": new_plan,
        "feedback": feedback_text
    }


@app.get("/view-all-users", response_class=HTMLResponse)
async def view_all_users(request: Request):
    users = get_all_users()

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "request": request,
            "users": users
        }
    )


@app.get("/api/users")
async def api_get_all_users():
    users = get_all_users()
    return [
        {
            "id": u.id,
            "name": u.name,
            "age": u.age,
            "weight": u.weight,
            "goal": u.goal,
            "intensity": u.intensity,
            "workout_plan": u.workout_plan,
            "nutrition_tip": u.nutrition_tip,
            "feedback": u.feedback
        }
        for u in users
    ]