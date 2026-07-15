import os
import google.generativeai as genai

gemini_key = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=gemini_key)

try:
    print("Generating image...")
    result = genai.generate_images(
        prompt="A clean minimalist laptop desk with code on screen, digital art",
        number_of_images=1,
        model="imagen-3.0-generate-001",
        aspect_ratio="16:9"
    )
    for generated_image in result.generated_images:
        print("Image generated successfully!")
        break
except Exception as e:
    print(f"Failed to generate image: {e}")
