import json, os, re
from groq import Groq
from dotenv import load_dotenv
from app.retriever import search, get_by_name
from app.prompts import SYSTEM_PROMPT, build_user_prompt, format_catalog_for_prompt
from app.schemas import Recommendation

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL   = "llama-3.3-70b-versatile"
print(f"Groq ready with model: {MODEL}")


def extract_search_query(messages):
    user_messages = [m["content"] for m in messages if m["role"] == "user"]
    return " ".join(user_messages)[-500:]


def is_comparison_request(messages):
    last_user_msg = ""
    original_msg  = ""
    for m in reversed(messages):
        if m["role"] == "user":
            last_user_msg = m["content"].lower()
            original_msg  = m["content"]
            break
    compare_words = ["compare", "difference between", "vs", "versus", "which is better"]
    is_compare = any(w in last_user_msg for w in compare_words)
    if not is_compare:
        return False, []
    names = re.findall(r'\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*\b', original_msg)
    return True, names


def call_llm(messages, catalog_context):
    prompt = build_user_prompt(messages, catalog_context)
    try:
        response = _client.chat.completions.create(
            model    = MODEL,
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt}
            ],
            temperature     = 0.3,
            response_format = {"type": "json_object"},
            max_tokens      = 1000,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$',     '', raw)
        parsed = json.loads(raw)
        return {
            "reply"              : parsed.get("reply", "Could you rephrase that?"),
            "should_recommend"   : parsed.get("should_recommend", False),
            "end_of_conversation": parsed.get("end_of_conversation", False),
        }
    except Exception as e:
        print(f"LLM error: {e}")
        return {
            "reply"              : "I'm having trouble processing that. Could you rephrase?",
            "should_recommend"   : False,
            "end_of_conversation": False,
        }


def handle_chat(messages):
    query = extract_search_query(messages)

    is_compare, names = is_comparison_request(messages)
    if is_compare and names:
        found = []
        for name in names[:3]:
            result = get_by_name(name)
            if result:
                found.append(result)
        semantic      = search(query, top_k=5)
        catalog_items = found + [s for s in semantic if s not in found]
    else:
        catalog_items = search(query, top_k=10)

    catalog_context = format_catalog_for_prompt(catalog_items)
    llm_result      = call_llm(messages, catalog_context)

    recommendations = []
    if llm_result["should_recommend"]:
        for item in catalog_items[:10]:
            recommendations.append(
                Recommendation(
                    name      = item["name"],
                    url       = item["url"],
                    test_type = item.get("test_type_codes", item["test_type"])
                )
            )

    return {
        "reply"              : llm_result["reply"],
        "recommendations"    : recommendations,
        "end_of_conversation": llm_result["end_of_conversation"],
    }