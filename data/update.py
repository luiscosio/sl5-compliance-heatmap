import json
import anthropic
import time # For rate limiting
import argparse # For command-line arguments
import os # For checking file existence
import sys # For exiting the script on error

# --- Configuration ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY") 
CLAUDE_MODEL = "claude-opus-4-20250514"
AI_LABS = ["OpenAI", "Anthropic", "Google", "xAI", "Meta"]
# The script will now read from and write to this file
INPUT_OUTPUT_FILE = "data/compliance-data.json"

# Initialize Anthropic client
client = None
if "YOUR_ANTHROPIC_API_KEY" not in ANTHROPIC_API_KEY:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    print("WARNING: ANTHROPIC_API_KEY is not set. API calls will be skipped.", file=sys.stderr)

def get_compliance_info(ai_lab: str, control_name: str, sl_level: int) -> dict:
    """
    Uses Anthropic Claude with web search to find compliance information for a given AI lab and control.
    Returns a dictionary with 'score', 'justification' and 'sources'.
    """
    # Skip API call if client is not initialized (due to missing API key)
    if client is None:
        return {
            "score": 0,
            "justification": "API key not set, skipping API call.",
            "sources": []
        }

    query_prompt = (
        f"Based on publicly available information, assess {ai_lab}'s compliance or posture regarding "
        f"'{control_name}' related to AI model weights security, as might be expected for Security Level {sl_level} "
        "as described in the RAND report 'Securing AI Model Weights'. "
        "Provide a compliance score in 25% increments (0, 25, 50, 75, or 100). "
        "Also, provide a brief, concise justification (1-3 sentences) and the URLs of your sources as a JSON list. "
        "Output the response in a single JSON object within a code block with 'score' (integer), 'justification' (string), and 'sources' (array of strings) fields. "
        "Example JSON: {\"score\": 75, \"justification\": \"...\", \"sources\": [\"url1\", \"url2\"]}. "
        "If no specific public information directly addressing this control for this lab is found, default the score to 0 and respond with "
        "{\"score\": 0, \"justification\": \"No specific public information found.\", \"sources\": []}."
    )

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": query_prompt}
            ],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 3 # Limit searches per query to avoid excessive billing
            }]
        )

        # Default values in case parsing fails
        score = 0
        justification = "Could not parse response or no relevant text."
        sources = []

        # Iterate through content blocks to find the JSON
        for content_block in response.content:
            if content_block.type == "text":
                try:
                    # Attempt to parse the text content as JSON
                    parsed_json = json.loads(content_block.text)
                    if "score" in parsed_json and isinstance(parsed_json["score"], int):
                        # Validate score is within allowed increments
                        if parsed_json["score"] in [0, 25, 50, 75, 100]:
                            score = parsed_json["score"]
                        else:
                            print(f"Warning: LLM returned invalid score '{parsed_json['score']}' for control '{control_name}'. Defaulting to 0%.", file=sys.stderr)
                    if "justification" in parsed_json:
                        justification = parsed_json["justification"]
                    if "sources" in parsed_json and isinstance(parsed_json["sources"], list):
                        sources = parsed_json["sources"]
                except json.JSONDecodeError:
                    # If it's not a JSON, treat it as raw text justification (and score remains default 0)
                    if "No specific public information found." in content_block.text:
                         justification = "No specific public information found."
                    else:
                         justification = content_block.text.strip()
            # Note: web_search_tool_result content type does not directly provide the LLM's final parsed answer.
            # The LLM's final answer, including parsed JSON, is typically in a subsequent 'text' block.
            # However, if needed, you could extract URLs from 'web_search_tool_result' blocks if they are distinct from the LLM's final JSON output.
            # For this script, we rely on the LLM to put the sources into the JSON.

        # Deduplicate sources
        sources = list(set(sources))

        return {"score": score, "justification": justification, "sources": sources}

    except Exception as e:
        print(f"Error querying Claude for {ai_lab} - '{control_name}': {e}", file=sys.stderr)
        return {"score": 0, "justification": f"Error during API call: {e}", "sources": []}

# --- Main script execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AI lab security compliance data.")
    parser.add_argument("--limit", type=int, help="Limit the number of controls to process for testing.")
    args = parser.parse_args()

    # Check if the input JSON file exists
    if not os.path.exists(INPUT_OUTPUT_FILE):
        print(f"Error: The input JSON file '{INPUT_OUTPUT_FILE}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Load existing compliance data from the JSON file
    compliance_data = []
    with open(INPUT_OUTPUT_FILE, "r") as f:
        compliance_data = json.load(f)
    print(f"Loaded existing compliance data from '{INPUT_OUTPUT_FILE}'.")

    print(f"Starting compliance data generation for {len(AI_LABS)} labs and {len(compliance_data)} SL levels...")
    total_queries_made = 0
    controls_processed_count = 0

    for sl_entry in compliance_data:
        sl_level = sl_entry["level"]
        for category in sl_entry["categories"]:
            for subcategory in category["subcategories"]:
                for control in subcategory["controls"]:
                    if args.limit and controls_processed_count >= args.limit:
                        print(f"Limit of {args.limit} controls reached. Stopping processing.")
                        break # Exit if limit is reached
                    
                    control_name = control["name"]
                    for lab in AI_LABS:
                        # Only make API call if client is initialized
                        if client is not None:
                            print(f"Querying for SL{sl_level} - {lab} - '{control_name}'...")
                            info = get_compliance_info(lab, control_name, sl_level)
                            control["compliance"][lab]["score"] = info["score"]
                            control["compliance"][lab]["justification"] = info["justification"]
                            control["compliance"][lab]["sources"] = info["sources"]
                            total_queries_made += 1
                            time.sleep(1) # Small delay to respect API rate limits
                        else:
                            print(f"Skipping API call for {lab} - '{control_name}' (API key not set). Compliance data for this control/lab will not be updated.")
                            # Ensure the structure is correct even if skipped
                            control["compliance"][lab]["score"] = 0
                            control["compliance"][lab]["justification"] = "API key not set, skipping API call."
                            control["compliance"][lab]["sources"] = []
                    
                    controls_processed_count += 1
                if args.limit and controls_processed_count >= args.limit:
                    break
            if args.limit and controls_processed_count >= args.limit:
                break
        if args.limit and controls_processed_count >= args.limit:
            break

    # Save the updated JSON back to the file
    with open(INPUT_OUTPUT_FILE, "w") as f:
        json.dump(compliance_data, f, indent=2)

    print(f"\nUpdated compliance data saved to '{INPUT_OUTPUT_FILE}'.")
    print(f"Total API queries made: {total_queries_made}")
    if args.limit:
        print(f"Processed {controls_processed_count} controls (limited by --limit {args.limit}).")
    print("Remember to review the 'score', 'justification', and 'sources' fields as LLM-generated content may vary and require manual verification.")