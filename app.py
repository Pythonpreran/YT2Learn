import streamlit as st
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import re
import streamlit.components.v1 as components
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

def gpt_generate(prompt: str) -> str:
    url = st.secrets["PROXY_URL"]
    headers = {"Content-Type": "application/json"}
    @retry(
        stop=stop_after_attempt(6),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True
    )
    def make_request():
        response = requests.post(url, json={"query": prompt}, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json().get("content", "")
    
    try:
        return make_request()
    except requests.RequestException:
        return "Error: Proxy API not responding, try again"

def get_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def fetch_transcript(video_id):
    try:
        # Check available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en'])  # Prefer English transcript
        @retry(
            stop=stop_after_attempt(6),
            wait=wait_fixed(2),
            retry=retry_if_exception_type(Exception),
            reraise=True
        )
        def try_fetch_transcript():
            proxies = {
                "http": st.secrets.get("HTTP_PROXY", None),
                "https": st.secrets.get("HTTPS_PROXY", None),
            }
            transcript_data = transcript.fetch(
                proxies=proxies if proxies["http"] or proxies["https"] else None
            )
            if transcript_data:
                full_text = " ".join([item['text'] for item in transcript_data])
                return full_text if full_text.strip() else None
            return None
        
        return try_fetch_transcript()
    except Exception as e:
        st.error(
            f"Failed to fetch transcript for video ID {video_id}: {str(e)}\n"
            "This may be due to YouTube blocking the request or the video lacking captions. "
            "Please check if captions are available on YouTube or try a different video."
        )
        return None

def parse_response(output):
    output = re.sub(r'\n\s*\n', '\n\n', output.strip())
    sections = re.split(r'^(?:[-*\s]*)(Summary|Quiz|Flashcards):[-*\s]*\n', output, flags=re.M|re.I)
    summary = "No summary found."
    quiz_pairs = []
    flashcards = []
    
    for i in range(1, len(sections), 2):
        section_name = sections[i].lower()
        content = sections[i+1].strip()
        
        if section_name == 'summary':
            summary = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', content).strip()
            
        elif section_name == 'quiz':
            pattern = re.compile(
                r'(?:\d+\.|\*\s*|-)\s*(.*?)(?:\n\s*(?:Answer:|-)\s*(.*?))(?=\n\s*(?:\d+\.|\*|-|\Z))',
                re.S|re.I
            )
            quiz_pairs = [(q.strip(), a.strip()) for q, a in pattern.findall(content)]
            
        elif section_name == 'flashcards':
            pattern = re.compile(
                r'(?:\d+\.|\*\s*|-)\s*(?:Term:?\s*)?(.*?)(?:\n\s*(?:Definition:|-)\s*(.*?))(?=\n\s*(?:\d+\.|\*|-|\Z))',
                re.S|re.I
            )
            flashcards = [
                {
                    "term": re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', term).strip(),
                    "definition": re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', definition).strip().replace("\n", " ")
                }
                for term, definition in pattern.findall(content)
            ]
    
    return summary, quiz_pairs, flashcards

def render_flashcards(flashcards):
    card_html_template = """
    <div class="flashcard" tabindex="0">
      <div class="flashcard-inner">
        <div class="flashcard-front">{term}</div>
        <div class="flashcard-back">{definition}</div>
      </div>
    </div>
    """
    cards_html = "".join([card_html_template.format(term=fc["term"], definition=fc["definition"]) for fc in flashcards])

    full_html = f"""
    <style>
    .flashcard {{
      background: #f8f9fa;
      border: 1px solid #ddd;
      width: 220px;
      height: 140px;
      perspective: 1000px;
      margin: 10px;
      cursor: pointer;
      border-radius: 8px;
      box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
      display: inline-block;
      vertical-align: top;
      outline: none;
    }}
    .flashcard-inner {{
      position: relative;
      width: 100%;
      height: 100%;
      text-align: center;
      transition: transform 0.6s;
      transform-style: preserve-3d;
    }}
    .flashcard:focus .flashcard-inner,
    .flashcard:hover .flashcard-inner {{
      transform: rotateY(180deg);
    }}
    .flashcard-front, .flashcard-back {{
      position: absolute;
      width: 100%;
      height: 100%;
      backface-visibility: hidden;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 10px;
      box-sizing: border-box;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      font-size: 16px;
      overflow: auto;
    }}
    .flashcard-front {{
      background: #007bff;
      color: white;
      font-weight: bold;
      border-radius: 8px;
    }}
    .flashcard-back {{
      background: #e9ecef;
      color: #333;
      transform: rotateY(180deg);
      border-radius: 8px;
      font-weight: normal;
    }}
    </style>
    <div>{cards_html}</div>
    """
    components.html(full_html, height=180 * ((len(flashcards) + 1) // 2))

def main():
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #e0eafc, #cfdef3);
            background-attachment: fixed;
        }
        .footer {
            text-align: center;
            padding: 20px;
            margin-top: 20px;
            font-size: 14px;
            color: #333;
        }
        .footer a {
            color: #007bff;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📽️ YouTube → Summary + Quiz + Flashcards")
    url = st.text_input("Enter YouTube Video URL")
    if url:
        video_id = get_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL or video ID not found.")
            return
        with st.spinner("Fetching transcript..."):
            transcript = fetch_transcript(video_id)
        if not transcript:
            return
        st.success("Transcript fetched successfully!")
        st.markdown(f"**Transcript length:** {len(transcript)} characters")

        if st.button("🚀 Generate Summary, Quiz, Flashcards"):
            with st.spinner("Generating response from GPT..."):
                prompt = f"""
You are an expert assistant.

Please perform these tasks based on the text below:

1. Provide a concise summary.
2. Generate 5 quiz questions and their answers.
3. Create 5 flashcards with key terms and definitions.

Text:
\"\"\"{transcript}\"\"

Format your response clearly with sections labeled "Summary:", "Quiz:", and "Flashcards:".
For Quiz, use format: "1. Question\n- Answer: Answer text"
For Flashcards, use format: "1. Term: Term text\n- Definition: Definition text"
"""
                output = gpt_generate(prompt)
                if output.startswith("Error:"):
                    st.error(output)
                    return
                summary, quiz, flashcards = parse_response(output)
                st.markdown("### 📝 Summary")
                st.markdown(summary if summary else "No summary found.")
                st.markdown("### ❓ Quiz")
                if quiz:
                    for i, (q, a) in enumerate(quiz):
                        with st.expander(f"Q{i+1}: {q}"):
                            st.write(f"**Answer:** {a}")
                else:
                    st.write("No quiz found.")
                st.markdown("### 🧠 Flashcards")
                if flashcards:
                    render_flashcards(flashcards)
                else:
                    st.write("No flashcards found.")

    st.markdown("""
        <div class="footer">
            Project by Preran S Gowda, VVCE, Mysuru<br>
            <a href="https://www.linkedin.com/in/preran-s-gowda-68b975291/" target="_blank">LinkedIn Profile</a> | 
            Email: <a href="mailto:preransgowda94@gmail.com">preransgowda94@gmail.com</a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
