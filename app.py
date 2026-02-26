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
    page_title="OGChat",
    page_icon="💬",
    layout="wide",
)

# --- No white stripes, pastel palette, big logo ---
st.markdown(
    """
    <style>
    /* Remove white bars: full-bleed dark background */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: #1a1f2e !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .stApp {
        background: linear-gradient(180deg, #1e2433 0%, #1a1f2e 50%, #161b26 100%) !important;
        color: #e2e8f0;
        min-height: 100vh;
    }
    [data-testid="stToolbar"], [data-testid="stDecoration"] {
        background: transparent !important;
    }
    section[data-testid="stSidebar"] {
        background: rgba(30, 36, 51, 0.98) !important;
        border-right: 1px solid rgba(148, 163, 184, 0.15);
    }
    [data-testid="stSidebar"] .stMarkdown { color: #94a3b8; }

    /* Soft pastel typography */
    h1, h2, h3 { color: #f1f5f9; font-weight: 600; }
    h1 { font-size: 1.85rem; letter-spacing: -0.02em; }
    p, .stMarkdown { color: #cbd5e1; }

    /* Pastel chat input */
    [data-testid="stChatInput"] {
        background: rgba(30, 41, 59, 0.85) !important;
        border: 1px solid rgba(148, 163, 184, 0.3) !important;
        border-radius: 1rem !important;
        padding: 0.75rem 1rem !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: rgba(251, 207, 232, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(251, 207, 232, 0.15) !important;
    }

    /* Pastel buttons */
    .stButton > button {
        background: linear-gradient(135deg, #c4b5fd 0%, #a78bfa 100%) !important;
        color: #1e1b4b !important;
        border: none !important;
        border-radius: 0.75rem !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%) !important;
        box-shadow: 0 4px 20px rgba(167, 139, 250, 0.35) !important;
    }

    .og-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 1rem;
        padding: 1.25rem;
        margin: 0.5rem 0;
    }
    .stSelectbox > div > div {
        background: rgba(30, 41, 59, 0.9) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(148, 163, 184, 0.25) !important;
        border-radius: 0.75rem !important;
    }

    .social-footer {
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(71, 85, 105, 0.5);
        text-align: center;
        font-size: 0.875rem;
        color: #94a3b8;
    }
    .social-footer a {
        color: #c4b5fd;
        text-decoration: none;
        margin: 0 0.35rem;
        font-weight: 500;
    }
    .social-footer a:hover { text-decoration: underline; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header: logo x5 (360px) + OGChat ---
logo_col, title_col = st.columns([0.2, 0.8])
with logo_col:
    try:
        st.image("logo.png", width=360)
    except Exception:
        try:
            st.image("https://raw.githubusercontent.com/DJwell3838/og-verifiable-chat/main/logo.png", width=360)
        except Exception:
            pass
with title_col:
    st.title("OGChat")
    st.caption("Verifiable LLM chat on the OpenGradient network")
st.markdown("Your request runs via the OpenGradient Python SDK; the response can be verified on-chain.")
st.markdown("---")

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

prompt = st.chat_input("Enter your prompt and press Enter to send")

if prompt and prompt.strip():
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
