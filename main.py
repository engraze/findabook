import os
import random
import requests
import datetime
from google import genai

# Setup the Gemini client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found.")
    exit()

client = genai.Client()

TARGET_QUOTES = 3
WORDS_PER_CHUNK = 666
MAX_ATTEMPTS = 100

def fetch_random_chunk():
    book_id = random.randint(1, 70000)
    
    # 1. Fetch the Metadata from Gutendex
    meta_url = f"https://gutendex.com/books/{book_id}"
    try:
        meta_response = requests.get(meta_url, timeout=10)
        if meta_response.status_code != 200:
            return None
            
        book_data = meta_response.json()
        title = book_data.get("title", "Unknown Title")
        
        # Gutendex returns a list of authors. We grab the first one.
        authors_list = book_data.get("authors", [])
        if authors_list:
            raw_author = authors_list[0].get("name", "Unknown Author")
            # Gutendex formats as "Last, First". Let's flip it to "First Last".
            if ", " in raw_author:
                parts = raw_author.split(", ")
                author = f"{parts[1]} {parts[0]}"
            else:
                author = raw_author
        else:
            author = "Unknown Author"

        # 2. Fetch the actual text from Gutenberg
        text_url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
        text_response = requests.get(text_url, timeout=10)
        
        if text_response.status_code != 200:
            return None
            
        words = text_response.text.split()
        if len(words) < WORDS_PER_CHUNK:
            return None
            
        start_limit = int(len(words) * 0.1)
        end_limit = len(words) - WORDS_PER_CHUNK - int(len(words) * 0.1)
        
        if start_limit >= end_limit:
            return None
            
        start_idx = random.randint(start_limit, end_limit)
        chunk_words = words[start_idx : start_idx + WORDS_PER_CHUNK]
        
        # Return a dictionary with the chunk AND the metadata
        return {
            "text": " ".join(chunk_words),
            "title": title,
            "author": author
        }
        
    except Exception:
        return None

def mine_quotes():
    quotes = []
    attempts = 0
    
    print(f"Igniting the pipeline. Target: {TARGET_QUOTES} ultra-premium, fully-cited quotes.")
    print("-" * 50)
    
    while len(quotes) < TARGET_QUOTES and attempts < MAX_ATTEMPTS:
        attempts += 1
        book_data = fetch_random_chunk()
        
        if not book_data:
            continue
            
        chunk = book_data["text"]
        title = book_data["title"]
        author = book_data["author"]
        
        # The "Thoughtful Reader" Prompt
        prompt = f"""
        You are a thoughtful reader exploring a massive, dusty library. 
        Read this {WORDS_PER_CHUNK}-word excerpt from the book "{title}" by {author}.
        
        Your goal is simply to find a sentence or short paragraph that feels good to read. It does NOT have to be a profound universal truth. It could be:
        - A beautiful or calming description of nature or a room.
        - A quiet, relatable observation about life, people, or emotions.
        - A comforting or poetic thought.
        - Just a genuinely lovely piece of writing that might make someone pause or smile today.
        
        If you find something that fits this vibe, extract it. 
        Translate the quote, the author, and the title into natural, elegant English (if it isn't already in English that is).
        
        Format strictly as: "[quote]" — Author, Book Title
        
        If the text is completely dry, technical, or just a table of contents, reply with EXACTLY and ONLY the word: NONE
        
        Excerpt:
        ---
        {chunk}
        ---
        """

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            
            result = response.text.strip()
            
            if result and result.upper() != "NONE":
                quotes.append(result)
                print(f"[{len(quotes)}/{TARGET_QUOTES}] GEM SECURED from '{title}'! (Attempt {attempts})")
            else:
                print(f"Attempt {attempts}: Rejected by CEO. Digging again...")
                
        except Exception as e:
            print(f"API Error on attempt {attempts}: {e}")
           
    # ... (Keep everything above this exactly the same) ...

    # --- NEW HTML GENERATION LOGIC ---
    import datetime
    today_str = datetime.datetime.now().strftime("%B %d, %Y")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Find A Book.</title>
    <style>
        :root {{
            --bg: #F9F9F8;
            --text: #1A1A1A;
            --faded: #7A7A7A;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text);
            font-family: "Georgia", serif;
            max-width: 650px;
            margin: 10vh auto;
            padding: 20px;
            line-height: 1.8;
            font-size: 1.1rem;
        }}
        h1 {{
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--faded);
            margin-bottom: 3rem;
            text-align: center;
        }}
        .quote-block {{
            margin-bottom: 4rem;
        }}
        .quote {{
            font-style: italic;
            font-size: 1.3rem;
        }}
        .citation {{
            display: block;
            margin-top: 10px;
            font-size: 0.95rem;
            text-align: right;
            color: var(--faded);
        }}
        footer {{
            margin-top: 5rem;
            text-align: center;
            font-size: 0.85rem;
            font-family: monospace;
            color: var(--faded);
        }}
    </style>
</head>
<body>

    <h1>Curated Daily • {today_str}</h1>
"""

    for q in quotes:
        # Safely split the AI's output into the Quote and the Citation
        if ' — ' in q:
            text, citation = q.rsplit(' — ', 1)
        else:
            text = q
            citation = "Unknown Source"

        html_content += f"""
    <div class="quote-block">
        <div class="quote">{text}</div>
        <div class="citation">— {citation}</div>
    </div>
"""

    html_content += """
    <footer>
        <p>Three quotes mined daily from Project Gutenberg's 70,000+ archives.<br>Running autonomously on a headless Metin2 server.</p>
    </footer>

</body>
</html>
"""

    # Save the file to the repo directory
    file_path = "/home/denis/findabook/index.html"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Successfully generated {file_path}")

if __name__ == "__main__":
    mine_quotes() 
