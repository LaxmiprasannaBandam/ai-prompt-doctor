"""
Prompt Doctor - Main Streamlit Application
Two-panel layout: Prompt Editor (left) + Examiner Verdict (right)
"""

import streamlit as st
from levels import LEVELS, DOMAINS
from runner import run_student_prompt
from examiner import call_examiner

# Page configuration
st.set_page_config(
    page_title="Prompt Doctor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the app
st.markdown("""
<style>
    .verdict-pass {
        color: #00cc66;
        font-weight: bold;
    }
    .verdict-fail {
        color: #ff4444;
        font-weight: bold;
    }
    .principle-pass {
        color: #00cc66;
        font-size: 1.2em;
    }
    .principle-fail {
        color: #ff4444;
        font-size: 1.2em;
    }
    .stButton button {
        width: 100%;
        background-color: #0066cc;
        color: white;
    }
    .level-card {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 8px;
        border-left: 4px solid #ccc;
    }
    .level-locked {
        opacity: 0.5;
        border-left-color: #999;
    }
    .level-current {
        border-left-color: #0066cc;
        background-color: #f0f7ff;
    }
    .level-passed {
        border-left-color: #00cc66;
        background-color: #f0fff0;
    }
    .domain-btn {
        margin: 2px;
    }
    .reasoning-box {
        background-color: #f5f5f5;
        border-left: 3px solid #0066cc;
        padding: 10px;
        border-radius: 4px;
        font-size: 0.9em;
        margin: 10px 0;
    }
    .weakness-text {
        color: #cc6600;
        font-style: italic;
    }
    .question-text {
        color: #0066cc;
        font-weight: 500;
    }
    h1, h2, h3 {
        margin-top: 0;
    }
    .sidebar-content {
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "current_level" not in st.session_state:
        st.session_state.current_level = 1
    if "passed_levels" not in st.session_state:
        st.session_state.passed_levels = set()
    if "domain" not in st.session_state:
        st.session_state.domain = None
    if "student_prompt" not in st.session_state:
        st.session_state.student_prompt = ""
    if "verdict" not in st.session_state:
        st.session_state.verdict = None
    if "live_output" not in st.session_state:
        st.session_state.live_output = None
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "openrouter_api_key" not in st.session_state:
        st.session_state.openrouter_api_key = ""
    if "revision_count" not in st.session_state:
        st.session_state.revision_count = 0
    if "max_level" not in st.session_state:
        st.session_state.max_level = 1


def get_level_data(level_num):
    """Get the level data for a given level number."""
    for level in LEVELS:
        if level["level"] == level_num:
            return level
    return LEVELS[0]


def get_domain_task(domain_name, level_num):
    """Get the domain-specific task description."""
    for domain in DOMAINS:
        if domain["name"] == domain_name:
            return domain["tasks"].get(level_num, "")
    return ""


def render_level_card(level_num):
    """Render a single level card in the sidebar."""
    level_data = get_level_data(level_num)
    is_current = level_num == st.session_state.current_level
    is_passed = level_num in st.session_state.passed_levels
    is_locked = level_num > st.session_state.max_level
    
    css_class = "level-card"
    if is_locked:
        css_class += " level-locked"
    elif is_passed:
        css_class += " level-passed"
    elif is_current:
        css_class += " level-current"
    
    status_icon = "✅" if is_passed else ("🔒" if is_locked else "📝")
    
    st.markdown(
        f"""<div class="{css_class}">
            <strong>{status_icon} Level {level_num}: {level_data['name']}</strong><br>
            <small>{level_data['description']}</small>
        </div>""",
        unsafe_allow_html=True
    )


def handle_submit():
    """Handle the submit button click - run prompt and get verdict."""
    if not st.session_state.student_prompt.strip():
        st.error("Please write a prompt first.")
        return
    
    if not st.session_state.domain:
        st.error("Please select a domain first.")
        return
    
    level_data = get_level_data(st.session_state.current_level)
    domain_name = st.session_state.domain
    domain_task = get_domain_task(domain_name, st.session_state.current_level)
    
    # Use sample input from level data
    sample_input = level_data["sample_input"]
    
    with st.spinner("Running your prompt..."):
        # Step 1: Run the student's prompt on the sample input
        live_output = run_student_prompt(
            st.session_state.student_prompt,
            sample_input
        )
        st.session_state.live_output = live_output
    
    with st.spinner("Examiner is grading your prompt..."):
        # Step 2: Call the examiner to grade the prompt
        verdict = call_examiner(
            level_data,
            st.session_state.student_prompt,
            sample_input,
            live_output
        )
        st.session_state.verdict = verdict
        st.session_state.submitted = True
        st.session_state.revision_count += 1


def handle_advance():
    """Handle advancing to the next level."""
    current = st.session_state.current_level
    st.session_state.passed_levels.add(current)
    
    if current < 5:
        next_level = current + 1
        st.session_state.current_level = next_level
        if next_level > st.session_state.max_level:
            st.session_state.max_level = next_level
    else:
        st.session_state.current_level = 5  # Stay at max
    
    # Reset for next level
    st.session_state.verdict = None
    st.session_state.live_output = None
    st.session_state.submitted = False
    st.session_state.student_prompt = ""
    st.session_state.revision_count = 0


def main():
    init_session_state()
    
    # Title
    st.title("🏥 Prompt Doctor")
    st.markdown("---")
    
    # Main two-panel layout
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        # ─── LEFT PANEL ───
        
        # Domain Selection
        st.subheader("🎯 Domain")
        domain_names = [d["name"] for d in DOMAINS]
        
        # Domain picker as radio buttons for clean selection
        selected_domain = st.radio(
            "Choose your domain:",
            domain_names,
            index=domain_names.index(st.session_state.domain) if st.session_state.domain in domain_names else 0,
            key="domain_selector",
            label_visibility="collapsed",
            horizontal=True
        )
        st.session_state.domain = selected_domain
        
        st.markdown("---")
        
        # Level Tracker
        st.subheader("📊 Levels")
        for lvl in range(1, 6):
            render_level_card(lvl)
        
        st.markdown("---")
        
        # Current Level Task
        level_data = get_level_data(st.session_state.current_level)
        domain_name = st.session_state.domain or "Healthcare"
        domain_task = get_domain_task(domain_name, st.session_state.current_level)
        
        st.subheader(f"Level {level_data['level']}: {level_data['name']}")
        
        # Task card
        st.info(f"**{level_data['description']}**")
        
        if domain_task:
            st.markdown(f"**Your task in *{domain_name}*:** {domain_task}")
        
        # Sample input display
        with st.expander("📄 Sample Input", expanded=True):
            st.code(level_data["sample_input"], language="text")
        
        # Principles checklist
        with st.expander("📋 Grading Principles", expanded=False):
            for p in level_data["principles"]:
                st.markdown(f"- **{p['name']}**: {p['description']}")
        
        st.markdown("---")
        
        # Prompt Editor
        st.subheader("✍️ Your Prompt")
        
        st.markdown("Write your prompt below. It will be used as the **system prompt** for the AI model.")
        
        prompt = st.text_area(
            "Prompt editor",
            value=st.session_state.student_prompt,
            height=250,
            placeholder="Write your prompt here...",
            label_visibility="collapsed",
            key="prompt_editor"
        )
        st.session_state.student_prompt = prompt
        
        # Submit button
        st.button(
            "🚀 Submit for Grading",
            on_click=handle_submit,
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.domain
        )
        
        # API Key input in sidebar area
        with st.expander("🔑 API Key Settings", expanded=False):
            api_key = st.text_input(
                "OpenRouter API Key",
                type="password",
                value=st.session_state.openrouter_api_key,
                help="Enter your OpenRouter API key. Get one at https://openrouter.ai/keys"
            )
            st.session_state.openrouter_api_key = api_key
        
        # Stats
        if st.session_state.revision_count > 0:
            st.caption(f"Revisions submitted: {st.session_state.revision_count}")
    
    with col_right:
        # ─── RIGHT PANEL ───
        
        if not st.session_state.submitted:
            # Welcome / instructions when nothing has been submitted
            st.subheader("📋 Examiner Verdict")
            st.info("""
            **Welcome to Prompt Doctor!** 🏥
            
            1. Select a **domain** on the left
            2. Read the **task** for the current level
            3. Write a **prompt** that satisfies the grading principles
            4. Click **"Submit for Grading"**
            
            The examiner will grade your prompt and return a verdict with ✓ / ✗ for each principle.
            
            *Tip: Each level adds new principles. Pass all checks to advance!*
            """)
            
            st.markdown("---")
            st.subheader("📤 Live Output")
            st.info("Submit a prompt to see the live output here.")
        else:
            # Display Verdict
            verdict = st.session_state.verdict
            
            st.subheader("📋 Examiner Verdict")
            
            if verdict.get("_reasoning"):
                with st.expander("🔍 Examiner's Reasoning", expanded=False):
                    st.markdown(
                        f'<div class="reasoning-box">{verdict["_reasoning"]}</div>',
                        unsafe_allow_html=True
                    )
            
            if verdict.get("verdict") == "pass":
                st.success("✅ **PASSED!** All principles satisfied.")
            else:
                st.error("❌ **REVISE** - Some principles need work.")
            
            # Principles breakdown
            st.markdown("### Principles")
            for p in verdict.get("principles", []):
                principle_name = p.get("name", "unknown")
                passed = p.get("pass", False)
                
                if passed:
                    st.markdown(f'<div class="principle-pass">✓ <strong>{principle_name}</strong></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="principle-fail">✗ <strong>{principle_name}</strong></div>', unsafe_allow_html=True)
                    
                    weakness = p.get("weakness", "")
                    question = p.get("question", "")
                    
                    if weakness:
                        st.markdown(f'<div class="weakness-text">💬 {weakness}</div>', unsafe_allow_html=True)
                    if question:
                        st.markdown(f'<div class="question-text">❓ {question}</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Live Output
            st.subheader("📤 Live Output")
            live_output = st.session_state.live_output
            
            if live_output:
                if live_output.startswith("ERROR"):
                    st.error(live_output)
                else:
                    st.code(live_output, language="text")
            
            st.markdown("---")
            
            # Action buttons
            verdict_passed = verdict.get("verdict") == "pass" if verdict else False
            
            if verdict_passed:
                if st.session_state.current_level < 5:
                    st.success(f"🎉 Level {st.session_state.current_level} Passed!")
                    st.button(
                        f"➡️ Advance to Level {st.session_state.current_level + 1}",
                        on_click=handle_advance,
                        type="primary",
                        use_container_width=True
                    )
                else:
                    st.success("🎉 **Congratulations! You've completed all 5 levels!** 🎉")
                    st.balloons()
                    st.button(
                        "🔄 Celebrate & Reset",
                        on_click=lambda: setattr(st.session_state, 'current_level', 1) or 
                                     setattr(st.session_state, 'passed_levels', set()) or
                                     setattr(st.session_state, 'max_level', 1) or
                                     setattr(st.session_state, 'verdict', None) or
                                     setattr(st.session_state, 'live_output', None) or
                                     setattr(st.session_state, 'submitted', False) or
                                     setattr(st.session_state, 'student_prompt', '') or
                                     setattr(st.session_state, 'revision_count', 0),
                        use_container_width=True
                    )
            else:
                st.info("💡 **Tip:** Read the examiner's feedback, revise your prompt, and submit again.")
    
    # Footer
    st.markdown("---")
    st.caption("Prompt Doctor · A prompt engineering skills lab · Powered by OpenRouter")


if __name__ == "__main__":
    main()