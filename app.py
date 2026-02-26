import os
import streamlit as st
import opengradient as og


@st.cache_resource
def get_client() -> og.Client:
    private_key = os.environ.get("OG_PRIVATE_KEY")
    if not private_key:
        raise RuntimeError(
            "Environment variable OG_PRIVATE_KEY is not set. "
            "Please configure it on your hosting platform with your Base Sepolia private key."
        )
    return og.Client(private_key=private_key)


st.set_page_config(
    page_title="OpenGradient Verifiable Chat",
    page_icon="💬",
    layout="wide",
)

# --- OG site–style: dark, warm gold accent, clean ---
st.markdown(
    """
    <style>
    /* Base: deep dark like opengradient.ai */
    .stApp {
        background: linear-gradient(180deg, #080c14 0%, #0a0e1a 50%, #060810 100%);
        color: #e2e8f0;
    }
    [data-testid="stSidebar"] {
        background: rgba(10, 14, 26, 0.95);
        border-right: 1px solid rgba(148, 163, 184, 0.12);
    }
    [data-testid="stSidebar"] .stMarkdown { color: #94a3b8; }

    /* Typography */
    h1, h2, h3 { color: #f8fafc; font-weight: 600; }
    h1 { font-size: 1.85rem; letter-spacing: -0.02em; }
    p, .stMarkdown { color: #cbd5e1; }

    /* Chat input: prominent, OG-style */
    [data-testid="stChatInput"] {
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(251, 191, 36, 0.35) !important;
        border-radius: 1rem !important;
        padding: 0.75rem 1rem !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: rgba(251, 191, 36, 0.7) !important;
        box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.15) !important;
    }

    /* Buttons: warm gold accent */
    .stButton > button {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        color: #0f172a !important;
        border: none !important;
        border-radius: 0.75rem !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%) !important;
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.35) !important;
    }

    /* Cards / response area */
    .og-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 1rem;
        padding: 1.25rem;
        margin: 0.5rem 0;
    }
    .og-accent { color: #fbbf24; }

    /* Selectboxes */
    .stSelectbox > div > div {
        background: rgba(15, 23, 42, 0.9) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(148, 163, 184, 0.25) !important;
        border-radius: 0.75rem !important;
    }

    /* Footer */
    .social-footer {
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(51, 65, 85, 0.6);
        text-align: center;
        font-size: 0.875rem;
        color: #64748b;
    }
    .social-footer a {
        color: #fbbf24;
        text-decoration: none;
        margin: 0 0.35rem;
        font-weight: 500;
    }
    .social-footer a:hover { text-decoration: underline; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ---
st.title("OpenGradient Verifiable Chat")
st.markdown(
    "Run **verifiable LLM chat** on the OpenGradient network. "
    "Your request is executed via the Python SDK; the response can be verified on-chain."
)
st.markdown("---")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    model = st.selectbox(
        "Model",
        [
            og.TEE_LLM.GPT_4O,
            og.TEE_LLM.CLAUDE_3_7_SONNET,
            og.TEE_LLM.GEMINI_2_5_FLASH,
        ],
        format_func=lambda m: str(m).split(".")[-1],
    )
    settlement_mode = st.selectbox(
        "Settlement mode (x402)",
        [
            og.x402SettlementMode.SETTLE,
            og.x402SettlementMode.SETTLE_METADATA,
            og.x402SettlementMode.SETTLE_BATCH,
        ],
        format_func=lambda m: str(m).split(".")[-1],
    )
    st.markdown("---")
    with st.expander("Feedback / Issues"):
        fb = st.text_area("Your message", key="feedback_message", height=80, placeholder="Error or idea? Leave it here.")
        if st.button("Send", key="send_feedback"):
            st.success("Thanks! Your message has been sent.") if fb.strip() else st.warning("Enter a message first.")

# --- Chat input: Enter sends natively ---
prompt = st.chat_input("Enter your prompt and press Enter to send")

if prompt and prompt.strip():
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = None
    st.session_state.last_prompt = prompt.strip()

    try:
        client = get_client()
    except Exception as e:
        st.error(f"Failed to initialize OpenGradient client: {e}")
    else:
        with st.chat_message("user"):
            st.write(prompt.strip())
        with st.spinner("Running verifiable inference on OpenGradient..."):
            try:
                client.llm.ensure_opg_approval(opg_amount=5)
                completion = client.llm.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt.strip()}],
                    x402_settlement_mode=settlement_mode,
                )
            except Exception:
                st.warning("Something went wrong on the network side. Please try again.")
            else:
                response_text = None
                try:
                    response_text = completion.chat_output.get("content")
                except Exception:
                    pass
                with st.chat_message("assistant"):
                    if response_text:
                        st.write(response_text)
                    else:
                        st.write("Could not read response content.")
                        st.json(getattr(completion, "__dict__", str(completion)))
                st.markdown('<div class="og-card">', unsafe_allow_html=True)
                st.subheader("On-chain verification")
                tx_hash = getattr(completion, "transaction_hash", None)
                if tx_hash and tx_hash != "external":
                    st.write("Transaction hash (Base Sepolia):")
                    st.code(tx_hash, language="text")
                elif tx_hash == "external":
                    st.write("On-chain transaction hash is managed externally for this request.")
                else:
                    st.write("`transaction_hash` not found in the response.")
                with st.expander("Raw response data (for OpenGradient reviewer)"):
                    st.json({"transaction_hash": tx_hash, "raw": getattr(completion, "__dict__", str(completion))})
                st.markdown('</div>', unsafe_allow_html=True)

# --- Footer ---
st.markdown(
    """
    <div class="social-footer">
      OpenGradient · 
      <a href="https://x.com/OpenGradient" target="_blank" rel="noopener">X</a> ·
      <a href="https://discord.gg/2t5sx5BCpB" target="_blank" rel="noopener">Discord</a> ·
      <a href="https://www.opengradient.ai/" target="_blank" rel="noopener">Website</a> ·
      <a href="https://github.com/OpenGradient" target="_blank" rel="noopener">GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
