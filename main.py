
from langfuse import Langfuse, observe
import google.generativeai as genai

# Setup Langfuse
langfuse = Langfuse(
    public_key="pk-lf-a9e6914d-2e63-4658-88d3-6151715b5821",
    secret_key="sk-lf-347475ef-2e06-4a2e-9353-679a8386b57f",
    host="http://localhost:3000"
)


# Gemini 2.0 Flash LLM call
def gemini_llm_call(prompt):
    genai.configure(api_key="AIzaSyBRT5hfxrH02dgQiUPshBoCV8xdEuHKYvw")
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text

# Prompt-managed function
@observe(as_type="generation")
def story_teller(theme, version=None):
    if version is not None:
        prompt = langfuse.get_prompt("generate-story", version=version)
    else:
        prompt = langfuse.get_prompt("generate-story")
    rendered_prompt = prompt.compile(theme=theme)
    return gemini_llm_call(rendered_prompt)

# Run
if __name__ == "__main__":
    result = story_teller("horror",version=1)
    print(result)
