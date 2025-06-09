import streamlit as st
import asyncio
from social_media_agent import (
    get_transcript,
    content_writer_agent,
    Runner,
    ItemHelpers,
    trace,
)

st.set_page_config(page_title="Social Media Content Generator", layout="centered")

st.title("🎬 Social Media Content Generator")
st.write(
    "Generate engaging social media posts from any YouTube video transcript using AI!"
)

with st.form("content_form"):
    video_id = st.text_input(
        "YouTube Video ID",
        help="Paste the video ID from the YouTube URL (e.g., dQw4w9WgXcQ)",
    )
    user_query = st.text_area(
        "What do you want?",
        value="Generate a LinkedIn post and an Instagram caption based on this video transcript.",  # noqa: E501
        help="Describe what kind of social media content you want.",
    )
    submit = st.form_submit_button("Generate Content")

if submit:
    if not video_id.strip():
        st.error("Please enter a YouTube video ID.")
    else:
        with st.spinner("Fetching transcript and generating content..."):
            try:
                transcript = get_transcript(video_id)
                msg = f"{user_query}\n\nTranscript:\n{transcript}"
                input_items = [{"content": msg, "role": "user"}]

                async def run_agent():
                    with trace("Writing content"):
                        result = await Runner.run(content_writer_agent, input_items)
                        return ItemHelpers.text_message_outputs(result.new_items)

                output = asyncio.run(run_agent())
                st.success("Generated Content:")
                st.markdown("---")
                st.markdown(output)
            except Exception as e:
                st.error(f"Error: {e}")
