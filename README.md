# YouTube Transcript to Summary, Quiz, and Flashcards

This Streamlit app fetches transcripts from YouTube videos and uses a GPT model to generate concise summaries, quiz questions, and flashcards. It’s designed for educational purposes, helping users study video content efficiently. The app features a modern gradient background and is built by **Preran S Gowda**, a student at **VVCE, Mysuru**.

- **LinkedIn**: [Preran S Gowda](https://www.linkedin.com/in/preran-s-gowda-68b975291/)
- **Email**: [preransgowda94@gmail.com](mailto:preransgowda94@gmail.com)

## Features
- **Transcript Fetching**: Extracts English transcripts from YouTube videos using the `youtube-transcript-api`.
- **Content Generation**: Generates a summary, 5 quiz questions with answers, and 5 flashcards with terms and definitions using a GPT model.
- **Interactive UI**: Displays quizzes in expandable sections and flashcards with a flip animation (hover or click to reveal definitions).
- **Secure Secrets**: Stores the GPT API proxy URL in `secrets.toml` to prevent exposure in the GitHub repository.
- **Modern Design**: Features a gradient background (light blue to soft purple) for a clean, professional look.
- **Error Handling**: Provides user-friendly messages for invalid URLs or failed transcript fetching.

## Screenshots
![img1](https://github.com/user-attachments/assets/75bfdaf4-501e-4229-914e-da586cd6cd54)
![img2](https://github.com/user-attachments/assets/7db95bca-f4bd-4c2e-bbc5-665bf5847da9)


## Prerequisites
- **Python 3.8+**
- **Git** (for cloning the repository)
- **Streamlit Cloud account** (for deployment)
- **GPT API Proxy URL** (a private URL for accessing the GPT model, kept secret in `secrets.toml`)

## Setup Instructions

### Local Setup
1. **Clone the Repository**:
   ```bash
   git clone <your-repository-url>
   cd <repository-name>
   ```

2. **Install Dependencies**:
   Install required Python packages using pip:
   ```bash
   pip install streamlit requests youtube-transcript-api tenacity
   ```

3. **Configure Secrets**:
   - Create a `.streamlit/` directory in the project root:
     ```bash
     mkdir .streamlit
     ```
   - Create a `.streamlit/secrets.toml` file with the following content:
     ```toml
     PROXY_URL = "<your-gpt-api-proxy-url>"
     ```
     - Replace `<your-gpt-api-proxy-url>` with your private GPT API proxy URL (e.g., a URL provided by your API service).
     - **Important**: Do not commit `secrets.toml` to GitHub, as it contains sensitive data.
   - Add `.streamlit/secrets.toml` to `.gitignore` to prevent accidental commits:
     ```bash
     echo ".streamlit/secrets.toml" >> .gitignore
     ```

4. **Run the App Locally**:
   ```bash
   streamlit run app.py
   ```
   - Open `http://localhost:8501` in your browser.
   - Enter a YouTube video URL (e.g., `https://www.youtube.com/watch?v=aircAruvnKk`) and click “Generate Summary, Quiz, Flashcards.”
   - The app will fetch the transcript and generate content if the transcript is available and your IP is not blocked by YouTube.

### Deployment on Streamlit Cloud
1. **Push to GitHub**:
   - Ensure `.streamlit/secrets.toml` is not committed:
     ```bash
     git add app.py
     git commit -m "Update Streamlit app"
     git push origin main
     ```
   - If sensitive data (e.g., `PROXY_URL`) was accidentally committed, rewrite Git history:
     ```bash
     git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .streamlit/secrets.toml' HEAD
     git push origin main --force
     ```

2. **Configure Streamlit Cloud**:
   - Go to [Streamlit Cloud](https://cloud.streamlit.io) and link your GitHub repository.
   - In your app’s dashboard, navigate to “Edit Secrets” and add:
     ```toml
     PROXY_URL = "<your-gpt-api-proxy-url>"
     ```
     - Replace `<your-gpt-api-proxy-url>` with your private GPT API proxy URL.
     - **Important**: Do not share this URL publicly or include it in the repository.
   - Save and redeploy the app. Changes take about a minute to propagate.

3. **Test the Deployed App**:
   - Access the app via its Streamlit Cloud URL.
   - Test with a YouTube video URL to ensure transcripts are fetched and content is generated.
   - If you encounter a “Failed to fetch transcript” error, see the **Troubleshooting** section below.

## How It Works
1. **Input**: Enter a YouTube video URL in the text box.
2. **Transcript Fetching**:
   - The app extracts the video ID and attempts to fetch the English transcript using `youtube-transcript-api`.
   - Retries up to 6 times if fetching fails due to network issues.
3. **Content Generation**:
   - Sends the transcript to a GPT model via the `PROXY_URL` to generate:
     - A concise summary.
     - 5 quiz questions with answers (displayed in expandable sections).
     - 5 flashcards with terms and definitions (displayed with a flip animation).
4. **UI**:
   - Features a gradient background (light blue to soft purple).
   - Includes a footer crediting **Preran S Gowda, VVCE, Mysuru** with LinkedIn and email links.
5. **Error Handling**:
   - Displays errors for invalid URLs or failed transcript fetching (e.g., due to missing captions or YouTube IP blocking).

## Troubleshooting

### “Failed to Fetch Transcript” Error
If you see an error like “Failed to fetch transcript after 6 attempts” (e.g., with `https://www.youtube.com/watch?v=aircAruvnKk`):
- **Cause 1: Missing Captions**:
  - Visit the YouTube video in a browser.
  - Click the “Settings” (gear) icon and check for “Subtitles/CC” (English).
  - If no captions are available, try a different video with English captions.
- **Cause 2: YouTube IP Blocking**:
  - YouTube may block requests from cloud provider IPs (e.g., Streamlit Cloud) or if too many requests are made.
  - **Solution**: Use a proxy to route requests through a different IP.
    - Obtain proxies from a service like Bright Data, Oxylabs, or `free-proxy-list.net`.
    - Update the app code to support proxies (see **Adding Proxy Support** below).
- **Cause 3: Rate Limits**:
  - Avoid rapid, repeated requests to YouTube.
  - Add a delay in the `fetch_transcript` function:
    ```python
    import time
    def fetch_transcript(video_id):
        time.sleep(1)  # Add delay
        # ... rest of the function
    ```
- **Report Issues**: If the video has captions and the error persists, check the `youtube-transcript-api` GitHub issues page: [https://github.com/jdepoix/youtube-transcript-api/issues](https://github.com/jdepoix/youtube-transcript-api/issues).

### Adding Proxy Support
To bypass YouTube IP blocking (common in cloud deployments):
1. Modify the `fetch_transcript` function in `app.py` to use a list of proxies:
   ```python
   import random
   def fetch_transcript(video_id):
       try:
           transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
           transcript = transcript_list.find_transcript(['en'])
           @retry(
               stop=stop_after_attempt(6),
               wait=wait_fixed(2),
               retry=retry_if_exception_type(Exception),
               reraise=True
           )
           def try_fetch_transcript():
               http_proxies = st.secrets.get("HTTP_PROXIES", "").split(",") if st.secrets.get("HTTP_PROXIES") else []
               https_proxies = st.secrets.get("HTTPS_PROXIES", "").split(",") if st.secrets.get("HTTPS_PROXIES") else []
               http_proxies = [proxy.strip() for proxy in http_proxies if proxy.strip()]
               https_proxies = [proxy.strip() for proxy in https_proxies if proxy.strip()]
               proxy = None
               if http_proxies and https_proxies:
                   proxy_index = random.randint(0, min(len(http_proxies), len(https_proxies)) - 1)
                   proxy = {
                       "http": http_proxies[proxy_index],
                       "https": https_proxies[proxy_index]
                   }
               transcript_data = transcript.fetch(proxies=proxy)
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
   ```
2. Update `.streamlit/secrets.toml` with proxy lists:
   ```toml
   PROXY_URL = "<your-gpt-api-proxy-url>"
   HTTP_PROXIES = "http://<proxy1-address:port>,http://<proxy2-address:port>,..."
   HTTPS_PROXIES = "https://<proxy1-address:port>,https://<proxy2-address:port>,..."
   ```
   - Replace `<proxy1-address:port>`, etc., with proxy addresses from a service like `free-proxy-list.net` or a paid provider (e.g., Bright Data).
3. Update Streamlit Cloud secrets with the same proxy lists.
4. Redeploy the app and test.

### GPT API Proxy Errors
If you see “Error: Proxy API not responding, try again”:
- Verify that the `PROXY_URL` in `secrets.toml` or Streamlit Cloud secrets is correct and the API is accessible.
- Check your API service for rate limits or downtime.
- Contact the API provider for support.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a branch (`git checkout -b feature-branch`).
3. Make changes and test locally.
4. Submit a pull request with a clear description.

Please ensure no sensitive data (e.g., `PROXY_URL`, proxy addresses) is included in pull requests.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For questions or support, contact:
- **Preran S Gowda**
- **Email**: [preransgowda94@gmail.com](mailto:preransgowda94@gmail.com)
- **LinkedIn**: [Preran S Gowda](https://www.linkedin.com/in/preran-s-gowda-68b975291/)
