import streamlit as st

st.set_page_config(page_title="Client Meet", page_icon="📹", layout="wide")

st.title("📹 Client Meet")
st.markdown("Join a secure video conference. Enter a custom room name or use the default one.")

room_name = st.text_input("Enter Room Name", value="clientMeet")
display_name = st.text_input("Enter Your Name", value="Guest")

jitsi_embed_code = f"""
<!DOCTYPE html>
<html>
  <head>
    <script src='https://8x8.vc/vpaas-magic-cookie-947339c5744d4782a2f74e59edc8dc95/external_api.js' async></script>
    <style>html, body, #jaas-container {{ height: 100%; margin: 0; overflow: hidden; }}</style>
    <script type="text/javascript">
      window.onload = () => {{
        const domain = "8x8.vc";
        const options = {{
          roomName: "vpaas-magic-cookie-947339c5744d4782a2f74e59edc8dc95/{room_name}",
          width: "100%",
          height: 620,
          parentNode: document.querySelector("#jaas-container"),
          configOverwrite: {{
            startWithAudioMuted: false,
            startWithVideoMuted: false
          }},
          interfaceConfigOverwrite: {{
            SHOW_JITSI_WATERMARK: false,
            SHOW_WATERMARK_FOR_GUESTS: false,
            DEFAULT_BACKGROUND: "#1a1a1a"
          }},
          userInfo: {{
            displayName: "{display_name}"
          }}
        }};
        const api = new JitsiMeetExternalAPI(domain, options);
      }};
    </script>
  </head>
  <body><div id="jaas-container"></div></body>
</html>
"""

st.components.v1.html(jitsi_embed_code, height=640)
