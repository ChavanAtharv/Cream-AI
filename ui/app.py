"""SchemeSaathi Streamlit Web Application.

Features:
1. Live Profile Chips: filter schemes by age, gender, occupation, income, category, and area,
   with a dynamic 'Why you match' explanation under each scheme card.
2. Natural Language Chat: calls FastAPI /ask (grounded RAG with citations) or /agent (LangGraph agent
   with comparison tools and approval flow).
3. Citation viewer and feedback (thumbs up / thumbs down) persistence.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECORDS_FILE = PROJECT_ROOT / "data" / "records.json"
FEEDBACK_FILE = PROJECT_ROOT / "data" / "feedback.json"


def _get_api_base_url() -> str:
    """Normalize API_URL to handle local, Docker, and Render service hostnames."""
    raw = os.getenv("API_URL", "http://127.0.0.1:8000").strip().rstrip("/")
    if not raw.startswith(("http://", "https://")):
        if "onrender.com" in raw:
            return f"https://{raw}"
        if any(h in raw for h in ("localhost", "127.0.0.1", "0.0.0.0", "api:")) or ":" in raw:
            return f"http://{raw}"
        # On Render, free services without protocol map to https://<host>.onrender.com
        return f"https://{raw}.onrender.com"
    return raw


API_BASE_URL = _get_api_base_url()


def make_api_request(
    endpoint: str, method: str = "POST", json_payload: dict = None, timeout: int = 35
):
    """Attempt request against primary API_BASE_URL and candidate fallbacks."""
    candidates = [
        API_BASE_URL,
        "https://schemesaathi-api-tqtz.onrender.com",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
    seen = set()
    unique_urls = []
    for u in candidates:
        clean = (u or "").strip().rstrip("/")
        if clean and clean not in seen:
            seen.add(clean)
            unique_urls.append(clean)

    last_error = None
    for base in unique_urls:
        target = f"{base}/{endpoint.lstrip('/')}"
        try:
            if method.upper() == "POST":
                return requests.post(target, json=json_payload, timeout=timeout)
            return requests.get(target, timeout=timeout)
        except Exception as e:
            last_error = e
            continue
    raise last_error or RuntimeError(f"Could not reach {endpoint}")


st.set_page_config(
    page_title="SchemeSaathi — Government Scheme Discovery",
    page_icon="🇮🇳",
    layout="wide",
)


@st.cache_data(ttl=60)
def load_all_records():
    """Load records from API if available, else from local JSON."""
    try:
        response = make_api_request("records?limit=100", method="GET", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    if RECORDS_FILE.exists():
        try:
            return json.loads(RECORDS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_feedback(question: str, answer: str, rating: str, mode: str):
    """Save thumbs up/down user feedback."""
    feedback_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "question": question,
        "answer": answer,
        "rating": rating,
    }
    entries = []
    if FEEDBACK_FILE.exists():
        try:
            entries = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    entries.append(feedback_entry)
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    FEEDBACK_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def evaluate_match(record, age_band, gender, occupation, income_band, category, area):
    """Determine if a scheme matches selected profile chips and why."""
    reasons = []
    name = record.get("scheme_name", "").lower()
    eligibility = (record.get("eligibility") or "").lower()
    cat = (record.get("category") or "").lower()

    # Occupation match
    if occupation != "All Occupations":
        occ_lower = occupation.lower()
        if "farmer" in occ_lower and ("farmer" in eligibility or "pm-kisan" in name or "kcc" in name or "kmy" in name):
            reasons.append("Designed specifically for farmer households and agricultural cultivation")
        elif "street vendor" in occ_lower and ("vendor" in eligibility or "svanidhi" in name):
            reasons.append("Directly benefits street vendors with collateral-free working capital")
        elif "artisan" in occ_lower and ("artisan" in eligibility or "craftsman" in eligibility or "vishwakarma" in name):
            reasons.append("Supports traditional artisans and craftsmen with toolkit and credit support")
        elif "student" in occ_lower and ("student" in eligibility or "internship" in name or "scholarship" in name):
            reasons.append("Open to university and college students seeking internship/scholarship")
        elif "unorganized" in occ_lower and ("unorganized" in eligibility or "pension" in name or "insurance" in cat):
            reasons.append("Provides financial safety net for unorganized workers")
        elif occ_lower not in eligibility and occ_lower not in cat:
            return False, ""

    # Age band match
    if age_band != "All Ages":
        if "18-40" in age_band:
            if "18-40" in eligibility or "18–40" in eligibility or "apy" in name:
                reasons.append("Matches the 18–40 entry age bracket")
            elif "18-50" in eligibility or "18–50" in eligibility:
                reasons.append("Falls within the eligible 18–50 age range")
            elif "60" in eligibility and "after" not in eligibility:
                return False, ""
        elif "18-50" in age_band:
            if "18-50" in eligibility or "18–50" in eligibility or "18-40" in eligibility or "18–40" in eligibility:
                reasons.append("Eligible under the adult entry criteria")
        elif "60+" in age_band:
            if "60" in eligibility or "pension" in eligibility or "pension" in cat:
                reasons.append("Provides pension benefits starting at or after age 60")
            elif "18-40" in eligibility or "18–40" in eligibility:
                return False, ""
        elif "Youth" in age_band:
            if "student" in eligibility or "intern" in name or "youth" in eligibility:
                reasons.append("Targeted at youth and student applicants")

    # Income band match
    if income_band != "All Incomes":
        if "Taxpayer" in income_band and "Non-Taxpayer" not in income_band:
            if "income-tax payers are excluded" in eligibility or "income tax" in eligibility:
                return False, ""
        elif "Non-Taxpayer" in income_band:
            if "income-tax payers are excluded" in eligibility or "small and marginal" in eligibility:
                reasons.append("Meets non-taxpayer / small-holder eligibility criteria")

    # Area match
    if area != "All Areas":
        if area == "Rural":
            if "urban" in name and "rural" not in name and "awaas yojana - urban" in name:
                return False, ""
            if "gramin" in name or "rural" in eligibility or "agriculture" in cat:
                reasons.append("Covers rural residences and village households")
        elif area == "Urban":
            if "gramin" in name:
                return False, ""
            if "urban" in name or "svanidhi" in name or "urban" in eligibility:
                reasons.append("Covers urban municipalities and towns")

    # Gender
    if gender == "Female":
        if "women" in eligibility or "girl" in eligibility or "sukanya" in name or "matru" in name:
            reasons.append("Special priority/mandate for female applicants")

    # If no specific tag triggered but not disqualified
    if not reasons:
        reasons.append("General criteria match based on selected demographic profile")

    return True, "; ".join(reasons)


# --- Header ---
st.title("🇮🇳 SchemeSaathi (योजना साथी)")
st.caption(
    "AI-powered discovery, live profile matching, and grounded guidance for Indian Central Government Schemes."
)

tab_match, tab_chat, tab_compare = st.tabs(
    ["🎯 Profile Matcher", "💬 Ask SchemeSaathi", "⚖️ Scheme Comparator"]
)

records = load_all_records()

# --- TAB 1: Profile Matcher ---
with tab_match:
    st.subheader("Profile Chips — Live Scheme Eligibility Matcher")
    st.write(
        "Select your demographic details below to filter schemes and view instant personalized match rationales."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        age_band = st.selectbox(
            "Age Band",
            ["All Ages", "18-40 (Youth/Working)", "18-50 (Adult)", "60+ (Senior)", "Youth/Students"],
            index=0,
            key="chip_age",
        )
        gender = st.selectbox(
            "Gender",
            ["All Genders", "Female", "Male", "Transgender"],
            index=0,
            key="chip_gender",
        )
    with c2:
        occupation = st.selectbox(
            "Occupation",
            [
                "All Occupations",
                "Farmer",
                "Street Vendor",
                "Artisan / Craftsman",
                "Student / Researcher",
                "Unorganized / Self-Employed",
            ],
            index=0,
            key="chip_occupation",
        )
        income_band = st.selectbox(
            "Income Band",
            ["All Incomes", "Non-Taxpayer / Low Income", "Income Taxpayer"],
            index=0,
            key="chip_income",
        )
    with c3:
        category = st.selectbox(
            "Category",
            ["All Categories", "General", "OBC", "SC", "ST", "Minority"],
            index=0,
            key="chip_category",
        )
        area = st.selectbox(
            "Area / Residence",
            ["All Areas", "Rural", "Urban"],
            index=0,
            key="chip_area",
        )

    # Filter records live
    matched_schemes = []
    for r in records:
        is_match, why = evaluate_match(r, age_band, gender, occupation, income_band, category, area)
        if is_match:
            matched_schemes.append((r, why))

    st.markdown(f"### Matching Schemes ({len(matched_schemes)} found)")
    if not matched_schemes:
        st.info("No schemes matched all selected criteria. Try broadening your filters.")
    else:
        for rec, why in matched_schemes:
            with st.container(border=True):
                col_title, col_cat = st.columns([3, 1])
                with col_title:
                    st.markdown(f"#### {rec.get('scheme_name')}")
                with col_cat:
                    cat_val = rec.get("category")
                    if cat_val:
                        st.caption(f"🏷️ {cat_val}")

                st.markdown(f"**Ministry:** {rec.get('ministry') or 'Not specified'}")
                st.markdown(f"**Benefit:** {rec.get('benefit') or 'Not specified'}")
                st.markdown(f"**Eligibility:** {rec.get('eligibility') or 'Not specified'}")

                # Signature feature: 'Why you match' line
                st.success(f"💡 **Why you match:** {why}")

                if rec.get("source_url"):
                    st.markdown(f"[Official Scheme Portal]({rec.get('source_url')})")

# --- TAB 2: Chat & AI Agent ---
with tab_chat:
    st.subheader("Grounded Scheme Q&A")
    st.caption("Ask specific questions backed by official scheme guidelines and PDF documentation.")

    mode = st.radio(
        "Response Mode",
        ["RAG Search (/ask)", "Autonomous Agent (/agent)"],
        horizontal=True,
        key="chat_mode_radio",
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "agent_thread_id" not in st.session_state:
        st.session_state.agent_thread_id = None
    if "pending_approval" not in st.session_state:
        st.session_state.pending_approval = None

    # Render previous messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "citations" in msg and msg["citations"]:
                with st.expander("📚 Citations & Official Sources"):
                    for c in msg["citations"]:
                        st.markdown(
                            f"- **[{c['number']}] {c['title']}** (Page {c['page']}) — `{c['file']}`\n  *Source: {c['source']}*"
                        )
            if "feedback_given" in msg:
                st.caption(f"Feedback recorded: {msg['feedback_given']}")

    # Check if waiting for human-in-the-loop approval from /agent
    if st.session_state.pending_approval:
        pending = st.session_state.pending_approval
        with st.container(border=True):
            st.warning("⚠️ **Human Approval Required by Agent**")
            st.markdown(f"The agent proposes to run tool: **`{pending.get('tool')}`**")
            st.code(json.dumps(pending.get("input"), indent=2))
            c_app, c_rej = st.columns(2)
            if c_app.button("✅ Approve Tool Execution", use_container_width=True):
                try:
                    res = make_api_request(
                        "agent",
                        method="POST",
                        json_payload={
                            "thread_id": st.session_state.agent_thread_id,
                            "approve": True,
                        },
                        timeout=30,
                    ).json()
                    st.session_state.pending_approval = None
                    answer_text = res.get("answer", "")
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": answer_text, "citations": []}
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error resuming agent: {e}")
            if c_rej.button("❌ Reject Tool Execution", use_container_width=True):
                try:
                    res = make_api_request(
                        "agent",
                        method="POST",
                        json_payload={
                            "thread_id": st.session_state.agent_thread_id,
                            "approve": False,
                        },
                        timeout=30,
                    ).json()
                    st.session_state.pending_approval = None
                    answer_text = res.get("answer", "Action cancelled by user.")
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": answer_text, "citations": []}
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error resuming agent: {e}")

    # Chat input
    user_query = st.chat_input("E.g., Can a farmer paying income tax receive PM-KISAN?")
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Consulting SchemeSaathi knowledge base..."):
                try:
                    if "RAG" in mode:
                        resp = make_api_request(
                            "ask",
                            method="POST",
                            json_payload={"question": user_query, "top_k": 4},
                            timeout=35,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            answer = data.get("answer", "No answer received.")
                            citations = data.get("citations", [])
                            st.markdown(answer)
                            if citations:
                                with st.expander("📚 Citations & Official Sources"):
                                    for c in citations:
                                        st.markdown(
                                            f"- **[{c['number']}] {c['title']}** (Page {c['page']}) — `{c['file']}`\n  *Source: {c['source']}*"
                                        )
                            st.session_state.chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": answer,
                                    "citations": citations,
                                }
                            )
                        else:
                            err_msg = f"API error ({resp.status_code}): {resp.text}"
                            st.error(err_msg)
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": err_msg, "citations": []}
                            )
                    else:  # Agent mode
                        payload = {"question": user_query, "auto_approve": False}
                        if st.session_state.agent_thread_id:
                            payload["thread_id"] = st.session_state.agent_thread_id
                        resp = make_api_request("agent", method="POST", json_payload=payload, timeout=35)
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.agent_thread_id = data.get("thread_id")
                            if data.get("awaiting_approval"):
                                st.session_state.pending_approval = data.get("pending_action")
                                st.warning("Agent requested tool approval. See above.")
                                st.rerun()
                            else:
                                answer = data.get("answer", "Done.")
                                st.markdown(answer)
                                st.session_state.chat_history.append(
                                    {
                                        "role": "assistant",
                                        "content": answer,
                                        "citations": [],
                                    }
                                )
                        else:
                            err_msg = f"Agent API error ({resp.status_code}): {resp.text}"
                            st.error(err_msg)
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": err_msg, "citations": []}
                            )
                except Exception as ex:
                    err_msg = f"Could not reach SchemeSaathi backend: {ex}"
                    st.error(err_msg)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": err_msg, "citations": []}
                    )

    # Thumbs up/down feedback on the latest assistant answer
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
        last_idx = len(st.session_state.chat_history) - 1
        last_msg = st.session_state.chat_history[last_idx]
        if "feedback_given" not in last_msg:
            col_fb1, col_fb2, col_fb3 = st.columns([1, 1, 8])
            with col_fb1:
                if st.button("👍 Helpful", key=f"up_{last_idx}"):
                    save_feedback(user_query or "Query", last_msg["content"], "positive", mode)
                    last_msg["feedback_given"] = "👍 Helpful"
                    st.rerun()
            with col_fb2:
                if st.button("👎 Not helpful", key=f"down_{last_idx}"):
                    save_feedback(user_query or "Query", last_msg["content"], "negative", mode)
                    last_msg["feedback_given"] = "👎 Not helpful"
                    st.rerun()

# --- TAB 3: Scheme Comparator ---
with tab_compare:
    st.subheader("Side-by-Side Scheme Comparison")
    st.write("Compare 2 to 4 schemes across benefits, eligibility conditions, and required documents.")

    scheme_names_list = [r.get("scheme_name") for r in records if r.get("scheme_name")]
    selected_schemes = st.multiselect(
        "Select schemes to compare (2 to 4)",
        options=scheme_names_list,
        default=scheme_names_list[:2] if len(scheme_names_list) >= 2 else [],
        max_selections=4,
        key="comparator_schemes_multiselect",
    )

    if st.button("Compare Schemes", key="comparator_execute_btn"):
        if len(selected_schemes) < 2:
            st.warning("Please select at least 2 schemes to compare.")
        else:
            try:
                from app.tools import compare_schemes
                table_md = compare_schemes(selected_schemes, records=records)
                st.markdown(table_md)
            except Exception as e:
                st.error(f"Comparison error: {e}")
