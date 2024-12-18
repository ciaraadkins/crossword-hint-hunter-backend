from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai

app = FastAPI()

# OpenAI API setup
openai.api_key = "your-openai-api-key"

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
async def guess_word(input_data: GuessWordInput):
    # Function schema for OpenAI
    tools = [
        {
            "type": "function",
            "function": {
                "name": "guess_word",
                "description": "Generates word suggestions based on given letters, placements, and hints.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "num_letters": {"type": "integer"},
                        "letters_and_placement": {"type": "string"},
                        "hint": {"type": "string"},
                    },
                    "required": ["num_letters", "letters_and_placement", "hint"],
                },
            },
        }
    ]
    messages = [
        {"role": "system", "content": "You are a crossword assistant using tools to find words."},
        {"role": "user", "content": "Can you suggest a word for my crossword?"},
    ]

    # Call OpenAI's API
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=messages,
        tools=tools
    )

    # Extract the function call
    tool_calls = response["choices"][0]["message"].get("tool_calls", [])
    if not tool_calls:
        raise HTTPException(status_code=500, detail="No tool call was generated.")

    tool_call = tool_calls[0]
    # Execute function logic
    suggestion = tool_call["function"]["arguments"]
    return {"suggested_word": suggestion}

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