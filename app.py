import streamlit as st
import google.generativeai as genai
import PyPDF2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page settings
st.set_page_config(page_title="Next-Gen AI Research Assistant", page_icon="🧬", layout="wide")

def main():
    # Inject Custom CSS for Premium Dark Mode
    st.markdown("""
<style>
h1, h2, h3, h4, .stMarkdown p, .stTextInput label, .stSelectbox label {
    font-family: 'Outfit', sans-serif !important;
}
.stApp {
    background-color: #0F172A !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stSidebar"] {
    background-color: #1E293B !important;
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] * {
    color: #F8FAFC !important;
}
/* Fix Expander Header Contrast & Icons */
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    background-color: #334155 !important;
    color: #FFFFFF !important;
    border-radius: 8px;
}
[data-testid="stExpanderIcon"] {
    font-family: inherit !important;
}
/* Unified Sidebar Inputs */
[data-testid="stSidebar"] .stTextInput input, [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
    background-color: #0F172A !important;
    color: #F8FAFC !important;
    border: 1px solid #334155 !important;
}
.main-header {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    padding: 3rem 2rem;
    border-bottom: 2px solid #6366F1;
    margin-bottom: 2rem;
    text-align: center;
    border-radius: 0 0 20px 20px;
}
.main-header h1 {
    font-weight: 800;
    color: #FFFFFF;
    margin-bottom: 0.5rem;
    font-size: 3rem;
}
.main-header p {
    color: #94A3B8;
    font-size: 1.1rem;
}
.upload-container {
    max-width: 800px;
    margin: 2rem auto;
    padding: 2.5rem;
    background: #1E293B;
    border-radius: 16px;
    border: 1px solid #334155;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
}
.stButton>button {
    background-color: #6366F1 !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 12px !important;
    width: 100% !important;
    border: none !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
}
.stTextInput input, .stSelectbox select, .stFileUploader section {
    background-color: #0F172A !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
    border: 1px solid #334155 !important;
}
</style>
<div class="main-header">
    <h1>Next-Gen AI Research Assistant 🧬</h1>
    <p>Summarize papers with AI precision, tailored to your learning style.</p>
</div>
""", unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        with st.expander("ℹ️ About", expanded=True):
            st.markdown("This tool uses **Google's Gemini 2.5 Flash** to extract and summarize research papers based on your preferred learning style.")
        
        st.subheader("API Status")
        env_api_key = os.getenv("GEMINI_API_KEY", "")
        
        # Smart Hide Logic
        if env_api_key and "change_key" not in st.session_state:
            st.success("✅ Gemini API Key Configured")
            if st.button("🔧 Change API Key", use_container_width=True):
                st.session_state.change_key = True
                st.rerun()
            api_key = env_api_key
        else:
            api_key = st.text_input("Gemini API Key", type="password", value=env_api_key)
            if env_api_key and st.button("Cancel", use_container_width=True):
                if "change_key" in st.session_state:
                    del st.session_state.change_key
                st.rerun()
        
        st.subheader("Preferences")
        learning_style = st.selectbox(
            "Select your learning style",
            ["Visual (Use analogies & structure)", 
             "Explain like I'm 5 (Simple terms)", 
             "Academic (Detailed & formal)", 
             "Bullet points (Quick & concise)"]
        )
        
        translate_to_malayalam = st.toggle("Translate to Malayalam", value=False)
        
    if not api_key:
        st.warning("Please enter your Gemini API Key in the sidebar to continue.")
        st.stop()
        
    genai.configure(api_key=api_key)
    
    # Initialize Session States for Chat & Context
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pdf_text" not in st.session_state:
        st.session_state.pdf_text = None
    if "file_id" not in st.session_state:
        st.session_state.file_id = None

    # Wrap the main interaction area in a native container for stability
    with st.container():
        uploaded_file = st.file_uploader("Upload a Research Paper (PDF)", type=["pdf"])

    # Handle PDF Extraction globally so both tabs have access
    if uploaded_file:
        file_key = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.file_id != file_key:
            with st.spinner("Extracting entire research context..."):
                try:
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    st.session_state.pdf_text = text
                    st.session_state.file_id = file_key
                    st.session_state.messages = [] # Reset chat for new file
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")
                    st.stop()

    # Tabbed interface for Summary and Chat (ALWAYS VISIBLE)
    tab1, tab2 = st.tabs(["📊 Summary", "💬 Chat with Paper"])
    
    with tab1:
        if st.session_state.pdf_text:
            if st.button("🚀 Generate Summary", use_container_width=True):
                with st.spinner("Analyzing and Generating Summary..."):
                    try:
                        # Construct prompt
                        translation_instruction = "Ensure the final output is entirely translated into Malayalam." if translate_to_malayalam else "Provide the output in English."
                        prompt = f"""
                        You are a world-class AI research assistant. 
                        I have provided the text from a research paper below.
                        Please summarize the research paper, specifically adapting your response to the following learning style: "{learning_style}".
                        {translation_instruction}
                        Here is the paper text:
                        ---
                        {st.session_state.pdf_text[:30000]}
                        ---
                        """
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content(prompt)
                        st.success("✨ Summary Generated Successfully!")
                        st.markdown("---")
                        st.markdown(f"### 📝 Structured Summary ({learning_style})")
                        st.write(response.text)
                        
                        st.download_button(
                            label="📥 Download Summary",
                            data=response.text,
                            file_name="research_summary.md",
                            mime="text/markdown"
                        )
                    except Exception as e:
                        st.error(f"Error generating summary: {e}")
        else:
            st.markdown("""
            ### 🏁 How to Get Started
            Welcome to the **Next-Gen AI Research Assistant**! Use the uploader above to begin.
            
            1. **Upload a PDF**: Simply drag and drop your research paper.
            2. **Select Style**: Choose your preferred learning style in the sidebar.
            3. **Generate**: Click the 'Generate Summary' button that will appear here.
            4. **Chat**: Head over to the 'Chat' tab to ask specific questions about the paper.
            """)
            st.info("💡 Tip: You can already use the Chat tab for general research questions!")

    with tab2:
        if st.session_state.pdf_text:
            st.markdown("### 🤖 Contextual Reasoning Chat")
            st.info("Grounded in your uploaded PDF.")
        else:
            st.markdown("### 🤖 Hub: General Research Assistant")
            st.info("I'm in standby mode. Ask me anything, or upload a PDF to enable deep reasoning.")
        
        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("Ask about this paper (or general research questions)..."):
            # Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # Hybrid Reasoning Logic
                        if st.session_state.pdf_text:
                            # Grounded Contextual reasoning prompt
                            context_prompt = f"""
                            You are an intelligent support chatbot for a research assistant.
                            Use the following PDF text to answer the user's question accurately.
                            Grounded Context:
                            ---
                            {st.session_state.pdf_text[:30000]}
                            ---
                            Question: {prompt}
                            Answer based ONLY on the text above. If not available, admit you don't know based on current context.
                            """
                        else:
                            # General assistant prompt
                            context_prompt = f"""
                            You are a world-class AI research assistant. 
                            The user has NOT uploaded a specific paper yet. 
                            Answer their general research, science, or technical questions accurately and professionally.
                            Question: {prompt}
                            """
                        
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content(context_prompt)
                        st.markdown(response.text)
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"Assistant error: {e}")

    # End of main interaction area
    pass

if __name__ == "__main__":
    main()
