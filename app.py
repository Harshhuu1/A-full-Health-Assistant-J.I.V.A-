from flask import Flask, render_template, request
import os
import re
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableLambda

# Load API Key securely (Use .env in production)
os.environ["OPENAI_API_KEY"] = "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"

# Initialize Flask App
app = Flask(__name__)

# Initialize OpenAI Model (Lower temperature for strict format)
llm_restro = OpenAI(temperature=0.1)  # Strict AI response

# **AI Prompt Template (Ensuring AI follows format)**
prompt_template_resto = PromptTemplate(
    input_variables=["age", "weight", "height", "bmi", "gender", "veg_or_nonveg", "disease", "allergics", "foodtype"],
    template="""
    📢 Hello! I'm **Coach Lily**, your friendly health instructor! 💪  
    I will **PERSONALLY design** a **perfect plan** for you, based on your BMI.  

    **📝 First, let's calculate your BMI:**  
    📊 **Formula:** BMI = weight / (height * height)  
    **💡 Your details:**  
    - **Age:** {age}  
    - **Height:** {height} m  
    - **Weight:** {weight} kg  
    - **BMI:** {bmi}  
    - **Gender:** {gender}  
    - **Food Preference:** {veg_or_nonveg}  
    - **Health Conditions:** {disease}  
    - **Allergies:** {allergics}  
    - **Preferred Diet:** {foodtype}  

    🔥 **I will now provide you with:**  
    ✅ 6 daily morning routine tips 🌅  
    ✅ 6 delicious breakfast ideas 🍳  
    ✅ 6 healthy dinner meals 🍽️  
    ✅ 6 power-packed workout plans 🏋️  

    **FORMAT RESPONSE EXACTLY LIKE THIS (NO EXTRA TEXT!):**  
    ---
    📊 **Your BMI Category:** (Underweight, Normal, Overweight, Obese)  
    🌅 **Daily Routine Recommendations:**  
    1. Example Routine 1  
    2. Example Routine 2  
    ...  

    🥞 **Recommended Breakfast:**  
    1. Example Breakfast 1  
    2. Example Breakfast 2  
    ...  

    🍽️ **Recommended Dinner:**  
    1. Example Dinner 1  
    2. Example Dinner 2  
    ...  

    🏋️ **Recommended Workouts:**  
    1. Example Workout 1  
    2. Example Workout 2  
    ...
    """
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    # **Get user input**
    age = request.form.get('age', '').strip()
    gender = request.form.get('gender', '').strip()
    weight = request.form.get('weight', '').strip()
    height = request.form.get('height', '').strip()
    disease = request.form.get('disease', '').strip()
    veg_or_nonveg = request.form.get('veg', '').strip()
    allergic = request.form.get('allergics', '').strip()
    food_type = request.form.get('foodtype', '').strip()

    # **Validate input**
    if not all([age, gender, weight, height, veg_or_nonveg, allergic, food_type]):
        return "⚠️ Oops! Please fill in all required fields.", 400

    # **Calculate BMI**
    try:
        weight = float(weight)
        height = float(height)
        bmi = round(weight / (height * height), 2)
    except ValueError:
        return "⚠️ Error: Invalid height or weight values.", 400

    # **Determine BMI Category**
    if bmi < 18.5:
        bmi_category = "Underweight 😟 (Time to fuel up! 🥑)"
    elif 18.5 <= bmi < 24.9:
        bmi_category = "Normal 💪 (You're in great shape! Keep going! 🔥)"
    elif 25 <= bmi < 29.9:
        bmi_category = "Overweight 😕 (Let's tweak that routine! 🚴)"
    else:
        bmi_category = "Obese 🚨 (Time for a power-packed transformation! 🚀)"

    # **Prepare Input for AI**
    input_data = {
        "age": age,
        "weight": weight,
        "height": height,
        "bmi": bmi,
        "gender": gender,
        "veg_or_nonveg": veg_or_nonveg,
        "disease": disease,
        "allergics": allergic,
        "foodtype": food_type
    }

    # **Generate AI recommendations using the new Runnable format**
    chain = prompt_template_resto | llm_restro
    response = chain.invoke(input_data)

    # **Fix AI Output Encoding Issues**
    response = response.encode("utf-8", "ignore").decode("utf-8")

    # **Extract information using regex**
    bmi_category_ai = re.search(r"📊 \*\*Your BMI Category\*\*:\s*(.*)", response)
    daily_routine = re.search(r"🌅 \*\*Daily Routine Recommendations:\*\*\s*(.*?)\s*🥞", response, re.DOTALL)
    breakfast_items = re.search(r"🥞 \*\*Recommended Breakfast.*?\*\*\s*(.*?)\s*🍽️", response, re.DOTALL)
    dinner_items = re.search(r"🍽️ \*\*Recommended Dinner.*?\*\*\s*(.*?)\s*🏋️", response, re.DOTALL)
    workout_plans = re.search(r"🏋️ \*\*Recommended Workouts.*?\*\*\s*(.*)", response, re.DOTALL)

    # **Convert extracted text to lists**
    bmi_category = bmi_category_ai.group(1).strip() if bmi_category_ai else bmi_category
    daily_routine = daily_routine.group(1).strip().split("\n") if daily_routine else ["⚠ AI forgot the routines! 😢"]
    breakfast_items = breakfast_items.group(1).strip().split("\n") if breakfast_items else ["⚠ Breakfast ideas missing! 🍳"]
    dinner_items = dinner_items.group(1).strip().split("\n") if dinner_items else ["⚠ No dinner ideas! 🍽️"]
    workout_plans = workout_plans.group(1).strip().split("\n") if workout_plans else ["⚠ AI skipped workouts! 💪"]

    return render_template(
        'result.html',
        bmi=bmi,
        bmi_category=bmi_category,
        daily_routine=daily_routine,
        breakfast_items=breakfast_items,
        dinner_items=dinner_items,
        workout_plans=workout_plans
    )

if __name__ == "__main__":
    app.run(debug=True)
