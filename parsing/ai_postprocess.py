import os
from openai import OpenAI
import json

# Initialize the OpenAI client with your environment variable
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))

def filter_grobid_references_with_chatgpt(references_list):
    """
    1) Prints debug info about references_list from GROBID.
    2) Splits references into chunks of size 10.
    3) For each chunk, calls ChatGPT with instructions:
       - 'Return only JSON, no triple backticks.'
       - Mark references as valid or not.
    4) Removes any backticks from the response before parsing JSON.
    5) Adds only valid references to final_references.
    6) Prints debug info about ChatGPT calls and final output.
    """
    # Debug: Print out what GROBID gave us
    print("DEBUG: references_list before ChatGPT:", references_list)

    chunk_size = 10
    final_references = []

    for i in range(0, len(references_list), chunk_size):
        chunk = references_list[i : i + chunk_size]
        # Debug: Show which references are in this chunk
        print(f"DEBUG: Processing chunk {i}–{i+chunk_size}: {chunk}")

        # Build the prompt
        # Approach A: explicitly instruct ChatGPT to avoid triple backticks
        prompt_content = (
            "You are an expert in parsing academic references. "
            "Return only JSON (no triple backticks or code fences). "
            "Below is a list of references in JSON form. Each normally has keys: "
            "'first_name', 'last_name', 'title', 'year', and 'journal'. "
            "If the reference has a title that fits the usual of an academic paper, OR it has a famous journal "
            "name, set 'valid': true. (this means keep the references that satisfy either of those two conditions)"
            "If it's clearly gibberish, set 'valid': false. "
            "Return only the JSON array, nothing else.\n\n"
            f"References:\n{json.dumps(chunk, indent=2)}"
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # or "gpt-4", if your account has access
                messages=[
                    {
                        "role": "system",
                        "content": "You are an extremely helpful assistant for checking references."
                    },
                    {
                        "role": "user",
                        "content": prompt_content
                    }
                ],
                temperature=0.0
            )

            # Debug: Print out ChatGPT's raw response text
            content = response.choices[0].message.content.strip()
            print("DEBUG: ChatGPT raw response content:\n", content)

            # Approach B: Remove possible code fences/backticks just in case
            content = content.replace("```json", "").replace("```", "")

            # Attempt to parse the JSON
            validated_chunk = json.loads(content)
            if isinstance(validated_chunk, list):
                for ref in validated_chunk:
                    if ref.get("valid") is True:
                        ref.pop("valid", None)
                        final_references.append(ref)
            else:
                print("DEBUG: ChatGPT returned something other than a list:", validated_chunk)

        except json.JSONDecodeError as e:
            print("DEBUG: JSONDecodeError while parsing ChatGPT response:", e)
        except Exception as e:
            print("DEBUG: Other error calling ChatGPT or reading response:", e)

    # Debug: Show what we ended up with after all chunks
    print("DEBUG: final_references after ChatGPT:", final_references)
    return final_references


def summarize_methods_and_tables_with_chatgpt(methods_text, tables_json_str):
    """
    Passes both the methods text and tables data (in JSON form) to ChatGPT,
    asking for a concise summary covering main methods + key findings.

    Returns a single string containing the summary from GPT.
    """
    # Build a prompt that instructs ChatGPT on how to summarize
    prompt_content = f"""
You are an expert at reading research methods and analyzing table data to extract main findings.

Below is the Methods section of a research paper, followed by a JSON representation of tables from that paper.

=== METHODS TEXT ===
{methods_text}

=== TABLES (JSON) ===
{tables_json_str}

Please produce a summary that addresses:
1) The main research methods used in the paper.
2) The key takeaways or findings from the data of each table.
3) Present the information in a medium-length, coherent report without code fences or raw JSON.
    """

    # For safety, chunk the prompt or handle large data if needed.
    # But here's a simple one-shot approach:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4" if available
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes academic methods and table findings."
                },
                {
                    "role": "user",
                    "content": prompt_content
                }
            ],
            temperature=0.0
        )

        # Extract the final content
        summary_text = response.choices[0].message.content.strip()
        return summary_text
    except Exception as e:
        print(f"Error calling OpenAI for methods/tables summary: {e}")
        return "LLM summarization failed or encountered an error."
