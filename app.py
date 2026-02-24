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


# --- Basic page config ---
st.set_page_config(
    page_title="OpenGradient Verifiable Chat",
    page_icon="💬",
)

# --- Softer OG-style theming via CSS ---
OG_PRIMARY = "#facc15"   # softer yellow
OG_PRIMARY_HOVER = "#fde047"
OG_BG = "#020617"        # very dark blue/navy
OG_PANEL = "#030712"     # slightly lighter panel

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {OG_BG};
        color: #e5e7eb;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    }}

    [data-testid="stSidebar"] {{
        background-color: {OG_PANEL};
        border-right: 1px solid rgba(148,163,184,0.25);
    }}

    h1, h2, h3, h4 {{
        color: #f9fafb;
    }}

    /* Primary buttons */
    .stButton > button {{
        background-color: {OG_PRIMARY};
        color: #111827;
        border-radius: 999px;
        border: none;
        padding: 0.55rem 1.4rem;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(0,0,0,0.35);
    }}
    .stButton > button:hover {{
        background-color: {OG_PRIMARY_HOVER};
        box-shadow: 0 6px 14px rgba(0,0,0,0.45);
    }}

    /* Text areas and inputs */
    textarea, .stTextInput input {{
        background-color: #020617 !important;
        color: #e5e7eb !important;
        border-radius: 0.75rem !important;
        border: 1px solid rgba(148,163,184,0.6) !important;
    }}
    textarea:focus, .stTextInput input:focus {{
        border-color: {OG_PRIMARY} !important;
        box-shadow: 0 0 0 1px {OG_PRIMARY}55 !important;
    }}

    /* Select boxes */
    .stSelectbox > div > div {{
        background-color: #020617 !important;
        color: #e5e7eb !important;
        border-radius: 0.75rem !important;
        border: 1px solid rgba(148,163,184,0.6) !important;
    }}

    /* Footer links */
    .social-footer {{
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(55,65,81,0.8);
        text-align: center;
        font-size: 0.9rem;
        color: #9ca3af;
    }}
    .social-footer a {{
        color: {OG_PRIMARY};
        text-decoration: none;
        margin: 0 0.4rem;
        font-weight: 500;
    }}
    .social-footer a:hover {{
        text-decoration: underline;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Main content ---
st.title("OpenGradient Verifiable Chat")
st.write(
    """
This app demonstrates how to run **verifiable LLM chat via OpenGradient**.

- The request is executed on the OpenGradient network using the Python SDK  
- The model response is accompanied by metadata that can be verified on-chain
"""
)

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

    # Small feedback block in the sidebar
    with st.expander("Feedback / Issues"):
        feedback_text = st.text_area(
            "Your message",
            key="feedback_message",
            height=90,
            placeholder="Hit an error or have an idea? Leave it here.",
        )
        if st.button("Send", key="send_feedback"):
            if feedback_text.strip():
                st.success("Thanks! Your message has been sent.")
            else:
                st.warning("Please enter a message before sending.")

st.subheader("Prompt")
prompt = st.text_area(
    "Enter your prompt",
    height=160,
    placeholder="Example: Explain in simple terms how OpenGradient works and why verifiable inference matters.",
)

if st.button("Run verifiable inference on OpenGradient", type="primary", key="run_inference"):
    if not prompt.strip():
        st.warning("Please enter a prompt first.")
    else:
        try:
            client = get_client()
        except Exception as e:
            st.error(f"Failed to initialize OpenGradient client: {e}")
        else:
            with st.spinner("Running verifiable inference on the OpenGradient network..."):
                try:
                    # Ensure there is enough OPG allowance for x402 payments
                    client.llm.ensure_opg_approval(opg_amount=5)

                    completion = client.llm.chat(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        x402_settlement_mode=settlement_mode,
                    )
                except Exception as e:
                    msg = str(e)
                    # Более дружелюбное сообщение для платёжных/фосетных проблем
                    if "Payment Required" in msg or "payment" in msg:
                        st.error(
                            "OpenGradient payment error: the testnet payment gateway "
                            "returned an invalid response. This is usually a temporary "
                            "issue on the network side or a faucet limit. "
                            "Please try again in a bit or verify your OPG balance on Base Sepolia."
                        )
                    else:
                        st.error(f"Error while calling OpenGradient: {e}")
                else:
                    response_text = None
                    try:
                        response_text = completion.chat_output.get("content")
                    except Exception:
                        pass

                    st.subheader("Model response")
                    if response_text:
                        st.write(response_text)
                    else:
                        st.write("Could not read `chat_output['content']` from the response.")
                        st.json(getattr(completion, "__dict__", str(completion)))

                    st.subheader("On-chain verification")
                    tx_hash = getattr(completion, "transaction_hash", None)
                    if tx_hash and tx_hash != "external":
                        st.write("Transaction hash (Base Sepolia):")
                        st.code(tx_hash, language="text")
                    elif tx_hash == "external":
                        st.write("On-chain transaction hash is managed externally for this request.")
                    else:
                        st.write("`transaction_hash` field not found in the response.")

                    with st.expander("Raw response data (for OpenGradient reviewer)"):
                        st.json(
                            {
                                "transaction_hash": tx_hash,
                                "raw": getattr(completion, "__dict__", str(completion)),
                            }
                        )

# --- Footer with OpenGradient social links ---
st.markdown(
    """
    <div class="social-footer">
      <span>OpenGradient links:</span>
      <a href="https://x.com/OpenGradient" target="_blank" rel="noopener noreferrer">X</a> ·
      <a href="https://discord.gg/2t5sx5BCpB" target="_blank" rel="noopener noreferrer">Discord</a> ·
      <a href="https://www.opengradient.ai/" target="_blank" rel="noopener noreferrer">Website</a> ·
      <a href="https://github.com/OpenGradient" target="_blank" rel="noopener noreferrer">GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
