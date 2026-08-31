import streamlit as st


def trigger_voice_alert(text: str) -> None:
    safe_text = (
        str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
    )

    js_code = f"""
    <script>
    function speakFemale() {{
        if (!("speechSynthesis" in window)) {{
            return;
        }}
        window.speechSynthesis.cancel();
        var voices = window.speechSynthesis.getVoices();
        var femaleKeywords = [
            "female", "zira", "samantha", "susan", "karen", "moira",
            "victoria", "google us english", "microsoft zira"
        ];
        var selected = null;
        for (var i = 0; i < voices.length; i++) {{
            var name = voices[i].name.toLowerCase();
            for (var j = 0; j < femaleKeywords.length; j++) {{
                if (name.includes(femaleKeywords[j])) {{
                    selected = voices[i];
                    break;
                }}
            }}
            if (selected) {{ break; }}
        }}
        if (!selected) {{
            for (var i = 0; i < voices.length; i++) {{
                if (voices[i].lang && voices[i].lang.toLowerCase().startsWith("en")) {{
                    selected = voices[i];
                    break;
                }}
            }}
        }}
        var message = new SpeechSynthesisUtterance("{safe_text}");
        message.volume = 1.0;
        message.rate = 1.0;
        message.pitch = 1.15;
        if (selected) {{
            message.voice = selected;
        }}
        window.speechSynthesis.speak(message);
    }}
    if (window.speechSynthesis.getVoices().length === 0) {{
        window.speechSynthesis.onvoiceschanged = function() {{ speakFemale(); }};
    }} else {{
        speakFemale();
    }}
    </script>
    """

    st.components.v1.html(js_code, height=0, width=0)
