import json
import os
import time
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from llm_helper import llm


def clean_text(text):
    """Removes non-ASCII characters (emojis) that can sometimes break LLM JSON output."""
    return text.encode("ascii", "ignore").decode("ascii")


def process_posts(raw_file_path, processed_file_path=None):
    print("Reading raw posts from:", os.path.abspath(raw_file_path))
    enriched_posts = []

    # 1. Read raw posts and extract metadata for each post
    with open(raw_file_path, encoding='utf-8') as file:
        posts = json.load(file)

        for index, post in enumerate(posts):
            if 'text' not in post:
                print(f"⚠️ Skipping post at index {index} because it's missing the 'text' key.")
                continue

            cleaned_post = clean_text(post['text'])
            post_id = post.get('id', post.get('post_id', index + 1))
            print(f"🔄 Processing post ID: {post_id}...")

            # Extract line count, language, and tags using LLM
            metadata = extract_metadata(cleaned_post)

            # Merge original post data with new metadata
            post_with_metadata = {**post, **metadata}
            enriched_posts.append(post_with_metadata)

            # Pause briefly to prevent hitting Groq's Tokens-Per-Minute (TPM) rate limits
            time.sleep(2)

    # 2. Unify messy tags across all posts into standard categories
    print("\n🔗 Unifying tags across all posts...")
    time.sleep(2)  # Pause before API call
    unified_tags_map = get_unified_tags(enriched_posts)

    # Apply tag unification if a valid map was returned
    if unified_tags_map:
        for post in enriched_posts:
            current_tags = post.get('tags', [])
            # Map old tags to standardized versions, keeping original if not found in map
            new_tags = {unified_tags_map.get(tag, tag) for tag in current_tags}
            post['tags'] = list(new_tags)

    # 3. Save the final enriched and unified posts to file
    if processed_file_path:
        os.makedirs(os.path.dirname(processed_file_path), exist_ok=True)
        with open(processed_file_path, mode="w", encoding="utf-8") as outfile:
            json.dump(enriched_posts, outfile, indent=4, ensure_ascii=False)
        print(f"\n✅ Successfully saved {len(enriched_posts)} enriched posts to {processed_file_path}")

    return enriched_posts


def extract_metadata(post):
    """Sends post text to LLM to extract line_count, language, and max 2 tags as JSON."""
    template = '''
    You are given a LinkedIn post. You need to extract the number of lines, language of the post, and tags.
    1. Return a valid JSON object only. No preamble, no markdown outside the JSON.
    2. The JSON object must have exactly three keys: line_count (integer), language (string), tags (array of strings).
    3. tags should be an array of text tags (maximum two tags).
    4. Language should be English or Hinglish (Hinglish means Hindi written in English script + English).

    Here is the actual post on which you need to perform this task:
    {post}
    '''

    parser = JsonOutputParser()
    pt = PromptTemplate.from_template(template)
    chain = pt | llm | parser

    try:
        res = chain.invoke({'post': post})
    except OutputParserException:
        raise OutputParserException("Context too big or invalid JSON returned by LLM.")
    return res


def get_unified_tags(posts):
    """Gathers all unique tags and maps them to standardized categories via LLM."""
    unique_tags = set()
    for post in posts:
        unique_tags.update(post.get('tags', []))

    if not unique_tags:
        return {}

    unique_tags_str = ", ".join(unique_tags)

    template = '''
    I have a list of tags extracted from LinkedIn posts: {tags}
    Please unify these tags into a standardized set of categories. 
    For example, map variations like "jobseeker" or "job hunting" to "job search".
    Return a valid JSON object where keys are the original tags and values are the unified/standardized tags. 
    No preamble, strictly JSON.
    '''

    parser = JsonOutputParser()
    pt = PromptTemplate.from_template(template)
    chain = pt | llm | parser

    try:
        mapping = chain.invoke({'tags': unique_tags_str})
        return mapping
    except Exception as e:
        print(f"⚠️ Warning: Tag unification failed ({e}). Keeping original tags.")
        return {}


if __name__ == '__main__':
    process_posts("data/raw_posts.json", "data/processed_posts.json")