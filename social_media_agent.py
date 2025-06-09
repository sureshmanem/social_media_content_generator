# --------------------------------------------------------------
# Step 0: Import packages and modules
# --------------------------------------------------------------
import asyncio
import os
from youtube_transcript_api import YouTubeTranscriptApi
from agents import Agent, Runner, WebSearchTool, function_tool, ItemHelpers, trace
from openai import OpenAI
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List


# --------------------------------------------------------------
# Step 1: Get OpenAI API key
# --------------------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --------------------------------------------------------------
# Step 2: Define tools for agent
# --------------------------------------------------------------

# Tool: Generate social media content from transcript
@function_tool
def generate_content(video_transcript: str, social_media_platform: str):
    print(f"Generating social media content for {social_media_platform}...")

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Generate content

    response = client.responses.create(
        model="gpt-4o",
        input=[
            {"role": "user", "content": f"Here is a new video transcript:\n{video_transcript}\n\n"  # noqa: E501
                                        f"Generate a social media post on my {social_media_platform} based on my provided video transcript.\n"}  # noqa: E501
        ],
        max_output_tokens=1000  # Increase tokens for longer blog posts
    )

    return response.output_text


# --------------------------------------------------------------
# Step 3: Define agent (content writer agent)
# --------------------------------------------------------------

@dataclass
class Post:
    platform: str
    content: str


content_writer_agent = Agent(
    name="Content Writer Agent",
    instructions="""You are a talented content writer who writes engaging, humorous, informative and 
                    highly readable social media posts. 
                    You will be given a video transcript and social media platforms. 
                    You will generate a social media post based on the video transcript 
                    and the social media platforms.
                    You may search the web for up-to-date information on the topic and 
                    fill in some useful details if needed.""",  # noqa: E501
    model="gpt-4o-mini",
    tools=[generate_content,
           WebSearchTool(),
           ],
    output_type=List[Post],
)


# --------------------------------------------------------------
# Step 4: Define helper functions
# --------------------------------------------------------------

# Fetch transcript from a youtube video using the video id
def get_transcript(video_id: str, languages: list = None) -> str:
    """
    Retrieves the transcript for a YouTube video.

    Args:
        video_id (str): The YouTube video ID.
        languages (list, optional): List of language codes to try, in order of preference.
                                   Defaults to ["en"] if None.

    Returns:
        str: The concatenated transcript text.

    Raises:
        Exception: If transcript retrieval fails, with details about the failure.
    """  # noqa: E501
    
    if languages is None:
        languages = ["en", "en-US", "en-GB", "en-AU", "en-CA"]

    try:
        # Use the Youtube transcript API
        fetched_transcript = YouTubeTranscriptApi().fetch(video_id, languages=languages)
        # print(fetched_transcript)
        

        # More efficient way to concatenate all text snippets
        transcript_text = " ".join(snippet.text for snippet in fetched_transcript)
        return transcript_text

    except Exception as e:
        # Simplified YouTube transcript API exception handling
        from youtube_transcript_api._errors import (
            CouldNotRetrieveTranscript, 
            VideoUnavailable,
            InvalidVideoId, 
            NoTranscriptFound,
            TranscriptsDisabled
        )

        error_map = {
            NoTranscriptFound: f"No transcript found for video {video_id} in languages: {languages}",  # noqa: E501
            VideoUnavailable: f"Video {video_id} is unavailable",
            InvalidVideoId: f"Invalid video ID: {video_id}",
            TranscriptsDisabled: f"Transcripts are disabled for video {video_id}",
            CouldNotRetrieveTranscript: f"Could not retrieve transcript for video {video_id}",  # noqa: E501
        }

        error_msg = error_map.get(type(e), f"An unexpected error occurred: {str(e)}")
        print(f"Error: {error_msg}")
        raise Exception(error_msg) from e

# --------------------------------------------------------------
# Step 5: Run the agent
# --------------------------------------------------------------
async def main():
    video_id = "OZ5OZZZ2cvk" # "", "4lk4qnnKjuI"
    transcript = get_transcript(video_id)
    
    # print("Transcript retrieved successfully.")

    msg = f"Generate a LinkedIn post and an Instagram caption based on this video transcript: {transcript}"  # noqa: E501

    # Package input for the agent
    input_items = [{"content": msg, "role": "user"}]

    # Run content writer agent
    # Add trace to see the agent's execution steps
    # You can check the trace on https://platform.openai.com/traces
    with trace("Writing content"):
        result = await Runner.run(content_writer_agent, input_items)
        output = ItemHelpers.text_message_outputs(result.new_items)
        print("Generated Post:\n", output)

if __name__ == "__main__":
    asyncio.run(main())
    