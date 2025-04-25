import os
import openai
from flask import Flask, render_template, request, send_file
from io import BytesIO
from docx import Document  
import json
from datetime import datetime
from dotenv import load_dotenv
app = Flask(__name__)



load_dotenv()  


openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_key = os.getenv("OPENAI_API_KEY")
deployment = os.getenv("OPENAI_DEPLOYMENT")

deployment = "gpt-4o"

def generate_worksheet_prompt(question_types, extra_instructions, detail_instructions):
    instructions = [
        "You are a helpful assistant that creates English worksheets.",
        "Generate an English worksheet that looks like a teacher’s handout with clear, numbered sections and headings in plain text.",
        "Do not use markdown symbols such as '#' or '*' in the output. Instead, use numbered headings, dashes, and clear text formatting.",
        "Include a small child-friendly fun fact about the content at the end of the whole worksheet.",
        "The user wants the following question types:"
        "If no instruction given do no do not generate anything"
        "Generate the thing that is chosen"
        "If the thing you are requested to generate does not follow grammer rules of english do not generate it and prompt the user to ask again"
        "Grade the test out of 100 and make a grading on the top right section on the worksheet it should look something like this _/number and all of these numbers should add up to 100 according to the question amount so if there is 20 total questions each question should equal to 5 points"
        "Never do an exam key ever I dont want to see the answers to the questions anywhere on the worksheet"
        "Do not use the word worksheet"
        "Do not generate anything more than what it is asked from you"
        
    ]
    
    def build_detail(detail):
        parts = []
        words = detail.get("words", "").strip()
        topics = detail.get("topics", "").strip()
        if words:
            parts.append("Words: " + words)
        if topics:
            parts.append("Topics: " + topics)
        return " ".join(parts)
    
    if 'reading_tf' in question_types:
        detail = build_detail(detail_instructions.get("reading_tf", {}))
        count = detail_instructions.get("reading_tf", {}).get("count", "5")
        if detail:
            instructions.append(f"1) For Reading Comprehension (True/False/Don't Say): {detail}. Provide a short reading passage (in English) and {count} True/False/Don't Say questions about it.")
        else:
            instructions.append(f"1) Provide a short reading passage (in English) and {count} True/False/Don't Say questions about it.")
    
    if 'reading_oe' in question_types:
        detail = build_detail(detail_instructions.get("reading_oe", {}))
        if detail:
            instructions.append(f"2) For Reading Comprehension Open Ended: {detail}. Provide a short reading passage and open-ended questions about it.")
        else:
            instructions.append("2) Provide a short reading passage and open-ended questions about it.")
    
    if 'essay' in question_types:
        detail = build_detail(detail_instructions.get("essay", {}))
        if detail:
            instructions.append(f"3) For Essay Prompt: {detail}. Provide an essay writing prompt or open-ended question for the user.")
        else:
            instructions.append("3) Provide an essay writing prompt or open-ended question for the user.")
    
    if 'multiple_choice' in question_types:
        detail = build_detail(detail_instructions.get("multiple_choice", {}))
        count = detail_instructions.get("multiple_choice", {}).get("count", "5")
        if detail:
            instructions.append(f"4) For Multiple Choice: {detail}. Provide {count} multiple-choice questions with 4 options each.")
        else:
            instructions.append(f"4) Provide {count} multiple-choice questions with 4 options each.")
    
    if 'matching' in question_types:
        detail = build_detail(detail_instructions.get("matching", {}))
        if detail:
            instructions.append(f"5) For Matching: {detail}. Provide a matching exercise with definitions or synonyms.")
        else:
            instructions.append("5) Provide a matching exercise with definitions or synonyms.")
    
    if 'fill_blanks' in question_types:
        detail = build_detail(detail_instructions.get("fill_blanks", {}))
        count = detail_instructions.get("fill_blanks", {}).get("count", "5")
        if detail:
            instructions.append(f"6) For Fill in the Blanks: {detail}. Provide {count} fill-in-the-blank sentences (each with one blank).")
        else:
            instructions.append(f"6) Provide {count} fill-in-the-blank sentences (each with one blank).")
    
    if 'vocab_practice' in question_types:
        detail = build_detail(detail_instructions.get("vocab_practice", {}))
        if detail:
            instructions.append(f"7) For Vocabulary Practice: {detail}. Ask the user to write sentences using the vocabulary provided.")
        else:
            instructions.append("7) Ask the user to write sentences using the provided vocabulary.")
            
    if 'P_w_multchoice' in question_types:
        detail = build_detail(detail_instructions.get("P_w_multchoice", {}))
        if detail:
            instructions.append(f"7) For paragraph with multiple choice: {detail}. Ask user to answer questions based on the empty spots in the paragraph and make the questions multiple choice under the paragraph ")
        else:
            instructions.append("7) Ask the user to write sentences using the provided vocabulary.")

    if 'rewrite_exercise' in question_types:
        detail = build_detail(detail_instructions.get("rewrite_exercise", {}))
        if detail:
            instructions.append(
                f"8) For Rewrite Exercise: {detail}. Given a sentence or short paragraph, ask learners to rewrite it—practicing grammar structures or paraphrasing.")
        else:
            instructions.append(
                "8) Given a sentence or short paragraph, ask learners to rewrite it—practicing grammar structures or paraphrasing.")
            
    if extra_instructions.strip():
        instructions.append(f"Additional instructions: {extra_instructions.strip()}")

    instructions.append("----------------------------------------------------------------------------------------------------------")
    instructions.append("Final Formatting Instructions:")
    instructions.append("Please format the worksheet as plain text using numbered sections and headings. For example:")
    instructions.append("")
    instructions.append("English Worksheet")
    instructions.append("Grade Level: Elementary/Middle School")
    instructions.append("")
    instructions.append("Section 1: Essay Writing Practice")
    instructions.append("Essay Prompt: [Insert Essay Prompt here]")
    instructions.append("Instructions:")
    instructions.append("  1. [Instruction one]")
    instructions.append("  2. [Instruction two]")
    instructions.append("  ...")
    instructions.append("")
    instructions.append("Section 2: Reading Comprehension")
    instructions.append("Reading Passage: [Insert Passage Here]")
    instructions.append("Questions:")
    instructions.append("  1. [Question 1]")
    instructions.append("  2. [Question 2]")
    instructions.append("  ...")
    instructions.append("")
    instructions.append("----------------------------------------------------------------------------------------------------------")
    instructions.append("Make sure that the final output does NOT contain any markdown syntax characters such as '#' or '*'.")
    
    return "\n".join(instructions)

def call_openai_api(prompt):
    response = openai.ChatCompletion.create(
        engine=deployment,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that creates English worksheets."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1200,
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response["choices"][0]["message"]["content"].strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        question_types = request.form.getlist("question_types")
        if not question_types:
            return render_template("index.html")
        extra_instructions = request.form.get("extra_instructions", "")
        
        detail_instructions = {}
        
        if 'reading_tf' in question_types:
            detail_instructions["reading_tf"] = {
                "words": request.form.get("reading_tf_words", ""),
                "topics": request.form.get("reading_tf_topics", ""),
                "count": request.form.get("reading_tf_count", "5")
            }
        if 'reading_oe' in question_types:
            detail_instructions["reading_oe"] = {
                "words": request.form.get("reading_oe_words", ""),
                "topics": request.form.get("reading_oe_topics", "")
            }
        if 'essay' in question_types:
            detail_instructions["essay"] = {
                "words": request.form.get("essay_words", ""),
                "topics": request.form.get("essay_topics", "")
            }
        if 'multiple_choice' in question_types:
            detail_instructions["multiple_choice"] = {
                "words": request.form.get("multiple_choice_words", ""),
                "topics": request.form.get("multiple_choice_topics", ""),
                "count": request.form.get("multiple_choice_count", "5")
            }
        if 'matching' in question_types:
            detail_instructions["matching"] = {
                "words": request.form.get("matching_words", ""),
                "topics": request.form.get("matching_topics", "")
            }
        if 'fill_blanks' in question_types:
            detail_instructions["fill_blanks"] = {
                "words": request.form.get("fill_blanks_words", ""),
                "topics": request.form.get("fill_blanks_topics", ""),
                "count": request.form.get("fill_blanks_count", "5")
            }
        if 'vocab_practice' in question_types:
            detail_instructions["vocab_practice"] = {
                "words": request.form.get("vocab_practice_words", ""),
                "topics": request.form.get("vocab_practice_topics", "")
            }
        if 'P_w_multchoice' in question_types:
            detail_instructions["P_w_multchoice"] = {
                "words": request.form.get("P_w_multchoice_words", ""),
                "topics": request.form.get("P_w_multchoice_topics", "")
            }
        if 'rewrite_exercise' in question_types:
            detail_instructions["rewrite_exercise"] = {
                "words": request.form.get("rewrite_exercise_words", ""),
                "topics": request.form.get("rewrite_exercise_topics", "")
            }
        
        prompt = generate_worksheet_prompt(question_types, extra_instructions, detail_instructions)
        worksheet_text = call_openai_api(prompt)

        data_to_save = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "question_types": question_types,
            "extra_instructions": extra_instructions,
            "details": detail_instructions,
            "worksheet_output": worksheet_text
        }
        os.makedirs("pastworksheets", exist_ok=True)

        filename = f"pastworksheets/worksheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                
        return render_template("worksheet.html", worksheet_text=worksheet_text)
    return render_template("index.html")

@app.route('/download', methods=['POST'])
def download():
    worksheet_text = request.form.get("worksheet_text")
    if not worksheet_text:
        return "No worksheet text provided!", 400

    doc = Document()
    doc.add_paragraph(worksheet_text)

    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    
    return send_file(
        file_stream,
        as_attachment=True,
        download_name="worksheet_exam.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if __name__ == '__main__':
    app.run(debug=True)
