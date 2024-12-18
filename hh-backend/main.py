from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
from openai import OpenAI
import os

app = FastAPI()

# OpenAI API setup
load_dotenv()
client = OpenAI()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Temporary storage to hold the last guessed word
latest_verified_word = {}

class WordRequest(BaseModel):
    num_letters: int
    letters_and_placement: str
    hint: str

# Define input schemas
class GuessWordInput(BaseModel):
    num_letters: int
    letters_and_placement: str
    hint: str

class WordValidationInput(BaseModel):
    word: str
    num_letters: int
    letters_and_placement: str

@app.post("/guess-word")
async def guess_word(request: WordRequest):
    """
    Suggest a word based on given crossword details.
    """
    try:
        # Build the prompt for word guessing
        prompt = f"""
        Solve the following crossword clue:
        - Number of letters: {request.num_letters}
        - Known letters and placements: {request.letters_and_placement}
        - Clue: {request.hint}

        Return only the word.
        """

        # Call the GPT-4o-mini model
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful crossword solver."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extract and clean up the AI's response
        suggested_word = completion.choices[0].message.content.strip()

        # Verify the word matches requirements
        if len(suggested_word) == request.num_letters and all(
            sc == "_" or sc == wc for sc, wc in zip(request.letters_and_placement, suggested_word)
        ):
            # Store the word for hint generation
            latest_verified_word["word"] = suggested_word
            return {"suggested_word": suggested_word.upper()}
        else:
            raise HTTPException(status_code=400, detail="Word does not meet requirements.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate-word")
async def validate_word(input_data: WordValidationInput):
    word = input_data.word
    num_letters = input_data.num_letters
    letters_and_placement = input_data.letters_and_placement

    if len(word) != num_letters:
        return {"valid": False, "error": "Word length mismatch."}
    
    for i, char in enumerate(letters_and_placement):
        if char != "_" and char != word[i]:
            return {"valid": False, "error": f"Mismatch at position {i + 1}."}
    
    return {"valid": True}

@app.post("/get-hint")
async def get_hint(request: WordRequest):
    """
    Generate a crossword-style hint based on the verified word.
    """
    try:
        # Retrieve the previously verified word
        verified_word = latest_verified_word.get("word")
        if not verified_word:
            raise HTTPException(status_code=400, detail="No verified word found. Guess a word first.")

        # Build the prompt for generating a hint
        prompt = f"""
        The user is solving a crossword puzzle.
        - Verified word: {verified_word}
        - Original clue: {request.hint}

        Provide an additional crossword-style hint for the verified word. Keep it short and max 30 characters.
        """

        # Call the GPT-4o-mini model
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful crossword assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extract and clean up the AI's response
        generated_hint = completion.choices[0].message.content.strip()

        return {"hint": generated_hint}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))