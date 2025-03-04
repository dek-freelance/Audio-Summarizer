import matplotlib.pyplot as plt
import base64
import io
import os
import pdfkit
import streamlit as st
# Dummy data
fruits = ['apple', 'blueberry', 'cherry', 'orange']
counts = [40, 100, 30, 55]
bar_labels = ['green', 'blue', 'red', 'orange']
bar_colors = ['tab:green', 'tab:blue', 'tab:red', 'tab:orange']

# Create chart with PyPlot
fig, ax = plt.subplots()
ax.bar(fruits, counts, label=bar_labels, color=bar_colors)
ax.set_ylabel('fruit supply')
ax.set_title('Fruit supply by kind and color')
ax.legend(title='Fruit color')

# Convert chart to jpg image (base64 encoded)
stringIObytes = io.BytesIO()
plt.savefig(stringIObytes, format='jpg')
stringIObytes.seek(0)
base64_jpg = base64.b64encode(stringIObytes.read()).decode()

# Create HTML for report
img_html = '<img src="data:image/png;base64, ' + base64_jpg + '" width=100%>'      
html = "<h1>Fruit supply report</h1>" + img_html

# Write HTML to temporary PDF file and read as base64 string
file_name = 'report.pdf'
pdfkit.from_string(html, file_name)
with open(file_name, "rb") as f:
    pdf_base64 = base64.b64encode(f.read())

# Send PDF as email attachment
email_server = pq.connect('Postmark')
email = {
    "from": "no-reply@acme.com",
    "to": "john@acme.com",
    "subject": "Your report",
    "text": "See PDF file attached.",
    "html": "See PDF file attached.",
    "attachment_name": "report.pdf",
    "attachment_content_base64": pdf_base64.decode("ascii"),
    "attachment_contenttype": "application/octet-stream"
}
result = email_server.add('email_with_attachment', email)
st.json(result) # for testing only, show result of sending email

os.remove(file_name)